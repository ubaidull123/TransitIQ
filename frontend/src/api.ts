import type {
  AnalysisRecord,
  ApiError,
  ApiErrorDetail,
  ExceptionInput,
  ExceptionRecord,
} from './types'

export const LIST_LIMIT = 50

export class ApiRequestError extends Error {
  readonly status: number
  readonly code: string
  readonly details: ApiErrorDetail[]

  constructor(status: number, body: ApiError | null) {
    super(body?.message ?? 'The request could not be completed.')
    this.name = 'ApiRequestError'
    this.status = status
    this.code = body?.code ?? 'unknown'
    this.details = body?.details ?? []
  }
}

export function fieldErrors(error: ApiRequestError): Record<string, string> {
  const mapped: Record<string, string> = {}
  for (const detail of error.details) {
    const field = detail.field.replace(/^body\./, '')
    if (!(field in mapped)) {
      mapped[field] = detail.message
    }
  }
  return mapped
}

async function readErrorBody(response: Response): Promise<ApiError | null> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'error' in body) {
      return (body as { error: ApiError }).error
    }
    return null
  } catch {
    return null
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, init)
  } catch {
    throw new ApiRequestError(0, {
      code: 'unreachable',
      message: 'Could not reach the API. Check that the server is running.',
      details: [],
    })
  }
  if (!response.ok) {
    throw new ApiRequestError(response.status, await readErrorBody(response))
  }
  return (await response.json()) as T
}

export function listExceptions(): Promise<ExceptionRecord[]> {
  return request<ExceptionRecord[]>(`/exceptions?limit=${LIST_LIMIT}`, {
    headers: { Accept: 'application/json' },
  })
}

export function createException(input: ExceptionInput): Promise<ExceptionRecord> {
  return request<ExceptionRecord>('/exceptions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(input),
  })
}

export function getAnalysis(shipmentId: string): Promise<AnalysisRecord> {
  return request<AnalysisRecord>(
    `/exceptions/${encodeURIComponent(shipmentId)}/analysis`,
    { headers: { Accept: 'application/json' } },
  )
}

export function runAnalysis(shipmentId: string): Promise<AnalysisRecord> {
  return request<AnalysisRecord>(
    `/exceptions/${encodeURIComponent(shipmentId)}/analyze`,
    { method: 'POST', headers: { Accept: 'application/json' } },
  )
}