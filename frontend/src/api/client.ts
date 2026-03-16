import type { ChatSession, ChatMessage, SSEMessageEvent, DocumentFile, SourceRef } from '../types'

const API_BASE = '/api'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || err.message || 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export async function listChats(): Promise<ChatSession[]> {
  const res = await fetch(`${API_BASE}/chats`)
  return handleResponse<ChatSession[]>(res)
}

export async function getChat(sessionId: string): Promise<ChatSession & { messages: ChatMessage[] }> {
  const res = await fetch(`${API_BASE}/chats/${sessionId}`)
  return handleResponse(res)
}

export async function createChat(): Promise<ChatSession> {
  const res = await fetch(`${API_BASE}/chats`, { method: 'POST' })
  return handleResponse<ChatSession>(res)
}

export async function deleteChat(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/chats/${sessionId}`, { method: 'DELETE' })
  await handleResponse<void>(res)
}

export async function listDocuments(): Promise<DocumentFile[]> {
  const res = await fetch(`${API_BASE}/documents`)
  return handleResponse<DocumentFile[]>(res)
}

export interface UploadResultItem {
  filename: string
  success: boolean
  file_id: string | null
  status: string | null
  error: string | null
}

export interface UploadResponse {
  results: UploadResultItem[]
}

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.xls', '.md']

export function isSupportedFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return SUPPORTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

export function getSupportedExtensionsString(): string {
  return SUPPORTED_EXTENSIONS.map((e) => e.replace('.', '')).join(', ')
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  if (files.length === 0) throw new Error('No files selected')
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  return handleResponse<UploadResponse>(res)
}

export interface DocumentsStatus {
  documents_folder: string
  folder_exists: boolean
  files_on_disk: string[]
  files_count: number
  phase2_tables_ok: boolean
  db_error: string | null
}

export async function getDocumentsStatus(): Promise<DocumentsStatus> {
  const res = await fetch(`${API_BASE}/documents/status`)
  return handleResponse<DocumentsStatus>(res)
}

export type StreamCallbacks = {
  onStatus: (status: string) => void
  onToken: (token: string) => void
  onDone: () => void
  onSources?: (sources: SourceRef[]) => void
  onError: (err: Error) => void
}

export async function streamChat(
  sessionId: string,
  content: string,
  callbacks: StreamCallbacks
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, content }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    callbacks.onError(new Error(err.detail || 'Request failed'))
    return
  }
  const reader = res.body?.getReader()
  if (!reader) {
    callbacks.onError(new Error('No response body'))
    return
  }
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: SSEMessageEvent = JSON.parse(line.slice(6))
            if (data.type === 'status') callbacks.onStatus(data.content)
            else if (data.type === 'token') callbacks.onToken(data.content)
            else if (data.type === 'sources') {
              try {
                const sources: SourceRef[] = JSON.parse(data.content || '[]')
                callbacks.onSources?.(sources)
              } catch {
                callbacks.onSources?.([])
              }
            } else if (data.type === 'error') {
              callbacks.onError(new Error(data.content || 'Server error'))
            } else if (data.type === 'done') callbacks.onDone()
          } catch {
            // skip invalid JSON
          }
        }
      }
    }
    callbacks.onDone()
  } catch (e) {
    callbacks.onError(e instanceof Error ? e : new Error(String(e)))
  }
}
