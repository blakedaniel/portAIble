/**
 * Happy-path e2e covering Phases 1–4:
 *   home → start session → upload zip → analyze (bg job)
 *        → confirm source profile → suggest + confirm destination
 *        → generate decisions (bg job) → answer + submit
 *        → assembled prompt page renders the splice
 *
 * Pipeline submission is intentionally NOT exercised — that requires
 * local-chat-agent running on AI_PIPELINE_URL. A Phase-7 spec can pin
 * a respx-style fake upstream when we want to cover that surface too.
 */

import { test, expect } from '@playwright/test'

function makeFakeDjangoZip(): Buffer {
  // Hand-roll a tiny ZIP via the standard ZIP file format so we don't add
  // adm-zip as a dep. zlib's deflate isn't stored — we use STORED method
  // (compression=0) which means raw bytes preceded by the ZIP local file
  // header. Two files: manage.py and requirements.txt. That's enough for
  // the FakeSourceAnalyzer to declare "Django + Python".
  //
  // Done in JS to keep the test self-contained (no FS fixture file).
  const files = [
    { name: 'manage.py', data: Buffer.from('import django\n', 'utf-8') },
    { name: 'requirements.txt', data: Buffer.from('Django==4.2\n', 'utf-8') },
  ]
  const localParts: Buffer[] = []
  const centralParts: Buffer[] = []
  let offset = 0
  for (const f of files) {
    const nameBytes = Buffer.from(f.name, 'utf-8')
    const crc32 = crc32Of(f.data)
    const size = f.data.length
    const local = Buffer.alloc(30)
    local.writeUInt32LE(0x04034b50, 0)   // local file header sig
    local.writeUInt16LE(20, 4)            // version
    local.writeUInt16LE(0, 6)             // flags
    local.writeUInt16LE(0, 8)             // compression: stored
    local.writeUInt16LE(0, 10)            // mod time
    local.writeUInt16LE(0, 12)            // mod date
    local.writeUInt32LE(crc32, 14)
    local.writeUInt32LE(size, 18)         // compressed size
    local.writeUInt32LE(size, 22)         // uncompressed size
    local.writeUInt16LE(nameBytes.length, 26)
    local.writeUInt16LE(0, 28)            // extra len
    localParts.push(local, nameBytes, f.data)

    const central = Buffer.alloc(46)
    central.writeUInt32LE(0x02014b50, 0)
    central.writeUInt16LE(20, 4)          // version made by
    central.writeUInt16LE(20, 6)          // version needed
    central.writeUInt16LE(0, 8)
    central.writeUInt16LE(0, 10)
    central.writeUInt16LE(0, 12)
    central.writeUInt16LE(0, 14)
    central.writeUInt32LE(crc32, 16)
    central.writeUInt32LE(size, 20)
    central.writeUInt32LE(size, 24)
    central.writeUInt16LE(nameBytes.length, 28)
    central.writeUInt16LE(0, 30)
    central.writeUInt16LE(0, 32)
    central.writeUInt16LE(0, 34)
    central.writeUInt16LE(0, 36)
    central.writeUInt32LE(0, 38)
    central.writeUInt32LE(offset, 42)
    centralParts.push(central, nameBytes)
    offset += local.length + nameBytes.length + size
  }
  const central = Buffer.concat(centralParts)
  const eocd = Buffer.alloc(22)
  eocd.writeUInt32LE(0x06054b50, 0)
  eocd.writeUInt16LE(0, 4)
  eocd.writeUInt16LE(0, 6)
  eocd.writeUInt16LE(files.length, 8)
  eocd.writeUInt16LE(files.length, 10)
  eocd.writeUInt32LE(central.length, 12)
  eocd.writeUInt32LE(offset, 16)
  eocd.writeUInt16LE(0, 20)
  return Buffer.concat([...localParts, central, eocd])
}

// ---- crc32 lookup table ----
const CRC_TABLE = (() => {
  const table = new Uint32Array(256)
  for (let i = 0; i < 256; i++) {
    let c = i
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    table[i] = c >>> 0
  }
  return table
})()
function crc32Of(buf: Buffer): number {
  let crc = 0xffffffff
  for (let i = 0; i < buf.length; i++) crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}

test('full porting workflow up to assembled prompt', async ({ page }) => {
  // Surface any browser-side errors in the test report.
  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[browser ${msg.type()}]`, msg.text())
  })
  page.on('pageerror', err => console.log('[browser pageerror]', err.message))

  // Home page renders and backend is reachable
  await page.goto('/', { waitUntil: 'networkidle' })
  await expect(page.getByRole('heading', { name: 'portAIble' })).toBeVisible()
  await expect(page.getByText(/Backend reachable/)).toBeVisible()

  // Start a session — Nuxt UI <UButton> renders as <button> with the label as text content.
  // Wait for hydration so the click handler is bound.
  const startBtn = page.locator('button', { hasText: /Start a new porting session/ })
  await expect(startBtn).toBeVisible()
  await startBtn.click()

  await page.waitForURL(/\/sessions\/[a-f0-9]{12}\/extract/, { timeout: 15_000 })
  const url = new URL(page.url())
  const sid = url.pathname.split('/')[2]
  expect(sid).toMatch(/^[a-f0-9]{12}$/)

  // Upload a synthetic Django ZIP
  const zipBytes = makeFakeDjangoZip()
  await page.locator('input[type="file"]').setInputFiles({
    name: 'django-app.zip',
    mimeType: 'application/zip',
    buffer: zipBytes,
  })
  await page.locator('button', { hasText: /^Upload$/ }).click()
  await page.waitForURL(`**/sessions/${sid}`)

  // Session overview — start the analyze background job
  await page.getByRole('link', { name: /Analyze/i }).click()
  await page.waitForURL(`**/sessions/${sid}/analyze`)
  await page.locator('button', { hasText: /Run/ }).first().click()
  // FakeSourceAnalyzer resolves immediately; we should land on source-profile
  await page.waitForURL(`**/sessions/${sid}/source-profile`, { timeout: 15_000 })

  // Source profile should be pre-populated with the Fake's Django entry
  await expect(page.locator('input[value="Python"]')).toBeVisible()
  await expect(page.locator('input[value="Django"]')).toBeVisible()
  await page.locator('button', { hasText: /Confirm/ }).first().click()
  await page.waitForURL(`**/sessions/${sid}/destination-profile`)

  // Destination — suggest from source, then confirm
  await page.locator('button', { hasText: /^Suggest$/ }).click()
  await expect(page.locator('input[value="Spring Boot"]')).toBeVisible({ timeout: 15_000 })
  await page.locator('button', { hasText: /Confirm \+ continue/ }).click()
  await page.waitForURL(`**/sessions/${sid}/decisions`)

  // Decisions — generate (bg job), answer all, submit
  await page.locator('button', { hasText: /Generate decisions/ }).click()
  // FakeDesignDecisions returns 3 canned questions; wait for the first one to render
  await expect(page.getByText(/Which persistence approach/i)).toBeVisible({ timeout: 15_000 })

  // Pick the first option of every decision
  const radios = page.locator('input[type="radio"]')
  const count = await radios.count()
  for (let i = 0; i < count; i++) {
    const r = radios.nth(i)
    const name = await r.getAttribute('name')
    // Click the first radio for each unique name only
    const sameName = await page.locator(`input[type="radio"][name="${name}"]`)
    if ((await sameName.first().isChecked()) === false) {
      await sameName.first().check()
    }
  }

  await page.locator('button', { hasText: /Submit answers/ }).click()
  await page.waitForURL(`**/sessions/${sid}/prompt`)

  // Build the prompt
  await page.locator('button', { hasText: /Build prompt/ }).click()
  // The assembled prompt renders as styled markdown inside a .prose-prompt div.
  const prompt = page.locator('.prose-prompt')
  await expect(prompt).toContainText(/Source Profile/i, { timeout: 15_000 })
  await expect(prompt).toContainText(/Destination Profile/i)
  // The bundled prompt-bank/transitions/django-springboot.md should be spliced in.
  await expect(prompt).toContainText(/Django.*Spring Boot/i)
  // Decisions answered are spliced in as a "Design Decisions" section.
  await expect(prompt).toContainText(/Design Decisions/i)
  // Markdown actually rendered (not raw '###'): a real <h3> exists inside the prose container.
  await expect(prompt.locator('h3').first()).toBeVisible()
})
