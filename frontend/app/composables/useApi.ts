/**
 * Thin typed fetch wrapper around the portAIble backend.
 *
 * Hand-rolled until Phase 1.5 when we generate from the backend's openapi.json
 * via `npm run gen:api`. The shapes here mirror the Pydantic models in
 * backend/src/portaible/api/schemas.py.
 */

export type SessionStatus =
  | 'created'
  | 'extracted'
  | 'analyzed'
  | 'source_profile_confirmed'
  | 'destination_profile_confirmed'
  | 'decisions_answered'
  | 'prompt_built'
  | 'pipeline_submitted'
  | 'pipeline_completed'
  | 'pipeline_failed'

export interface LanguageEntry { name: string; version?: string | null }
export interface FrameworkEntry { name: string; version?: string | null }
export interface PackageEntry { name: string; version?: string | null; alternatives: string[] }

export interface SourceProfile {
  languages: LanguageEntry[]
  frameworks: FrameworkEntry[]
  packages: PackageEntry[]
  important_information: string
  analyzer_draft: boolean
}

export interface DestinationProfile {
  languages: LanguageEntry[]
  frameworks: FrameworkEntry[]
  packages: PackageEntry[]
  target_notes: string
  analyzer_draft: boolean
}

export interface AssembledPrompt {
  instructions: string
  source_zip_path: string
}

export interface DecisionOption {
  id: string
  label: string
  description: string
}

export interface DesignDecision {
  id: string
  question: string
  options: DecisionOption[]
  allow_freeform: boolean
  rationale: string
}

export interface DecisionAnswer {
  decision_id: string
  selected_option_id: string | null
  freeform_answer: string | null
}

export interface Session {
  id: string
  status: SessionStatus
  extraction_kind: string | null
  source_uri: string | null
  extracted_file_count: number
  source_profile: SourceProfile | null
  destination_profile: DestinationProfile | null
  assembled_prompt: AssembledPrompt | null
  pipeline_remote_job_id: string | null
  pipeline_result_path: string | null
  created_at: string
  updated_at: string
}

export interface PipelineJob {
  remote_job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress_percentage: number
  progress_message: string
  error: string | null
  result_path: string | null
}

export interface SessionListItem {
  id: string
  status: SessionStatus
  created_at: string
  updated_at: string
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  const $get = <T>(url: string) => $fetch<T>(url, { baseURL: base })
  const $post = <T>(url: string, body?: unknown) =>
    $fetch<T>(url, { baseURL: base, method: 'POST', body })
  const $put = <T>(url: string, body?: unknown) =>
    $fetch<T>(url, { baseURL: base, method: 'PUT', body })
  const $del = <T>(url: string) => $fetch<T>(url, { baseURL: base, method: 'DELETE' })

  return {
    health: () => $get<{ ok: boolean; workspace_dir: string }>('/api/health'),

    listSessions: () => $get<{ sessions: SessionListItem[] }>('/api/sessions'),
    createSession: () => $post<Session>('/api/sessions'),
    getSession: (sid: string) => $get<Session>(`/api/sessions/${sid}`),
    deleteSession: (sid: string) => $del<void>(`/api/sessions/${sid}`),

    uploadZip: async (sid: string, file: File): Promise<Session> => {
      const fd = new FormData()
      fd.append('file', file)
      return await $fetch<Session>(`/api/sessions/${sid}/source/zip`, {
        baseURL: base,
        method: 'POST',
        body: fd,
      })
    },

    analyze: (sid: string) => $post<{ job_id: string }>(`/api/sessions/${sid}/analyze`),
    getJob: (sid: string, jid: string) =>
      $get<{ id: string; kind: string; status: string; progress_percentage: number; progress_message: string; error: string | null }>(
        `/api/sessions/${sid}/jobs/${jid}`,
      ),

    confirmSource: (sid: string) => $post<Session>(`/api/sessions/${sid}/profiles/source/confirm`),
    suggestDestination: (sid: string, target_hint: string | null) =>
      $post<Session>(`/api/sessions/${sid}/profiles/destination/suggest`, { target_hint }),
    confirmDestination: (sid: string) =>
      $post<Session>(`/api/sessions/${sid}/profiles/destination/confirm`),
    putSource: (sid: string, profile: SourceProfile) =>
      $put<Session>(`/api/sessions/${sid}/profiles/source`, profile),
    putDestination: (sid: string, profile: DestinationProfile) =>
      $put<Session>(`/api/sessions/${sid}/profiles/destination`, profile),

    generateDecisions: (sid: string) =>
      $post<{ job_id: string }>(`/api/sessions/${sid}/decisions/generate`),
    getDecisions: (sid: string) => $get<DesignDecision[]>(`/api/sessions/${sid}/decisions`),
    submitDecisionAnswers: (sid: string, answers: DecisionAnswer[]) =>
      $put<Session>(`/api/sessions/${sid}/decisions/answers`, { answers }),

    buildPrompt: (sid: string) => $post<Session>(`/api/sessions/${sid}/prompt/build`),
    getPrompt: (sid: string) => $get<AssembledPrompt>(`/api/sessions/${sid}/prompt`),

    submitPipeline: (sid: string) => $post<Session>(`/api/sessions/${sid}/pipeline/submit`),
    pollPipeline: (sid: string) => $get<PipelineJob>(`/api/sessions/${sid}/pipeline/status`),
    pipelineResultUrl: (sid: string) => `${base}/api/sessions/${sid}/pipeline/result`,
  }
}
