export type ExceptionSource = 'email' | 'edi' | 'webhook' | 'manual'

export const EXCEPTION_SOURCES: ExceptionSource[] = ['manual', 'email', 'edi', 'webhook']

export const SOURCE_LABELS: Record<ExceptionSource, string> = {
  manual: 'Manual',
  email: 'Email',
  edi: 'EDI',
  webhook: 'Webhook',
}

export interface ExceptionInput {
  shipment_id: string
  source: ExceptionSource
  reported_at: string
  carrier: string
  origin: string
  destination: string
  raw_text: string
  metadata: Record<string, unknown> | null
}

export interface ExceptionRecord extends ExceptionInput {
  id: number
}

export interface AnalysisAction {
  id: string
  description?: string
  status?: string
  created_at?: string | null
  completed_at?: string | null
}

export interface AnalysisContextEntry {
  source?: string
  content?: string
  created_at?: string
}

export interface AnalysisRun {
  exception_type?: string
  severity?: string
  created_at?: string
  missing_information?: string[]
  recommended_actions?: string[]
}

export interface AnalysisRecord {
  shipment_id: string
  status: string
  current_step: string
  analysis_error: string | null
  exception_type: string | null
  severity: string | null
  missing_information: string[]
  recommended_actions: string[]
  actions: AnalysisAction[]
  context: AnalysisContextEntry[]
  analysis_history: AnalysisRun[]
  updated_at: string | null
}

export interface ApiErrorDetail {
  field: string
  message: string
}

export interface ApiError {
  code: string
  message: string
  details: ApiErrorDetail[]
}