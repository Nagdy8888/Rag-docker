export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface SourceRef {
  filename: string
  chunk_index?: number
  snippet?: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  sources?: SourceRef[]
}

export type SSEEventType = 'status' | 'token' | 'done' | 'sources'

export interface SSEMessageEvent {
  type: SSEEventType
  content: string
}

export interface DocumentFile {
  id: string
  filename: string
  file_type: string
  file_size: number
  chunk_count: number
  status: 'processing' | 'ready' | 'error'
  error_message?: string | null
  created_at: string
}
