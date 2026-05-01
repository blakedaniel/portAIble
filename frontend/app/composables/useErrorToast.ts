/**
 * useErrorToast — extracts a useful message from a thrown $fetch error and
 * surfaces it via Nuxt UI's useToast(). Pages can still keep an inline error
 * banner for blocking flows; this is for transient failures where a toast
 * is enough.
 */
export const useErrorToast = () => {
  const toast = useToast()

  function showError(e: unknown, fallback = 'Something went wrong') {
    let msg = fallback
    if (e && typeof e === 'object') {
      // Nuxt's $fetch wraps the response body under `.data`; FastAPI puts the
      // human-readable message under `.detail`.
      const anyE = e as any
      msg = anyE?.data?.detail ?? anyE?.message ?? (String(e) || fallback)
    } else if (typeof e === 'string') {
      msg = e
    }
    toast.add({
      title: 'Error',
      description: msg,
      color: 'error',
      icon: 'i-lucide-circle-alert',
      duration: 6000,
    })
    return msg
  }

  function showSuccess(title: string, description?: string) {
    toast.add({
      title,
      description,
      color: 'success',
      icon: 'i-lucide-circle-check',
      duration: 3000,
    })
  }

  return { showError, showSuccess }
}
