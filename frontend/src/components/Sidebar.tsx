import { Trash2, Plus, MessageSquare, FolderOpen } from 'lucide-react'
import { useState } from 'react'
import type { ChatSession } from '../types'
import { createChat, deleteChat } from '../api/client'

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60 * 1000) return 'Just now'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / 3600000)}h ago`
  if (diff < 7 * 24 * 60 * 60 * 1000) return `${Math.floor(diff / 86400000)}d ago`
  return d.toLocaleDateString()
}

interface SidebarProps {
  sessions: ChatSession[]
  activeId: string | null
  onSelect: (id: string) => void
  onNewChat: () => void
  onSessionsChange: () => void
  onNavigateToDocuments?: () => void
  currentView?: 'chat' | 'documents'
  collapsed?: boolean
}

export function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNewChat,
  onSessionsChange,
  onNavigateToDocuments,
  currentView = 'chat',
  collapsed = false,
}: SidebarProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleNew = async () => {
    try {
      const chat = await createChat()
      onSelect(chat.id)
      onSessionsChange()
    } catch (e) {
      console.error(e)
    }
    onNewChat()
  }

  const handleSelectChat = (id: string) => {
    onSelect(id)
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (deletingId === id) {
      await deleteChat(id)
      onSessionsChange()
      if (activeId === id) onNewChat()
      setDeletingId(null)
    } else {
      setDeletingId(id)
      setTimeout(() => setDeletingId(null), 2000)
    }
  }

  if (collapsed) {
    return (
      <aside className="w-16 flex flex-col bg-[#18181b] border-r border-white/5 shrink-0">
        <button
          type="button"
          onClick={handleNew}
          className="p-4 flex items-center justify-center text-indigo-400 hover:bg-white/5"
        >
          <Plus className="w-6 h-6" />
        </button>
        <div className="flex-1 overflow-y-auto py-2">
          {sessions.slice(0, 20).map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onSelect(s.id)}
              className={`w-full p-3 flex items-center justify-center rounded-none border-l-2 ${
                activeId === s.id && currentView === 'chat' ? 'border-indigo-500 bg-white/5' : 'border-transparent hover:bg-white/5'
              }`}
            >
              <MessageSquare className="w-5 h-5 text-[#a1a1aa]" />
            </button>
          ))}
        </div>
        {onNavigateToDocuments && (
          <button
            type="button"
            onClick={onNavigateToDocuments}
            className={`p-3 flex items-center justify-center border-l-2 ${
              currentView === 'documents' ? 'border-indigo-500 bg-white/5' : 'border-transparent hover:bg-white/5'
            }`}
          >
            <FolderOpen className="w-5 h-5 text-[#a1a1aa]" />
          </button>
        )}
      </aside>
    )
  }

  return (
    <aside className="w-[280px] flex flex-col bg-[#18181b] border-r border-white/5 shrink-0">
      <button
        type="button"
        onClick={handleNew}
        className="m-3 py-2.5 px-4 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white font-medium text-sm flex items-center justify-center gap-2"
      >
        <Plus className="w-4 h-4" />
        New Chat
      </button>
      <div className="flex-1 overflow-y-auto px-2 pb-4 flex flex-col">
        <div className="flex-1 min-h-0">
          {sessions.map((s) => (
            <div
              key={s.id}
              role="button"
              tabIndex={0}
              onClick={() => handleSelectChat(s.id)}
              onKeyDown={(e) => e.key === 'Enter' && handleSelectChat(s.id)}
              className={`group flex items-center gap-2 rounded-lg px-3 py-2.5 cursor-pointer border-l-2 transition-colors 150ms ${
                activeId === s.id && currentView === 'chat'
                  ? 'border-indigo-500 bg-[#1c1c21]'
                  : 'border-transparent hover:bg-white/5'
              }`}
            >
              <span className="flex-1 min-w-0 text-left text-sm text-[#fafafa] truncate" title={s.title}>
                {s.title || 'New Chat'}
              </span>
              <span className="text-xs text-[#71717a] shrink-0">{formatTime(s.updated_at)}</span>
              <button
                type="button"
                onClick={(e) => handleDelete(e, s.id)}
                title={deletingId === s.id ? 'Click again to delete' : 'Delete'}
                className={`p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-[#a1a1aa] hover:text-red-400 shrink-0 ${
                  deletingId === s.id ? 'opacity-100 ring-1 ring-red-500/50' : ''
                }`}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        {onNavigateToDocuments && (
          <button
            type="button"
            onClick={onNavigateToDocuments}
            className={`mt-2 flex items-center gap-2 rounded-lg px-3 py-2.5 w-full text-sm border-l-2 transition-colors 150ms ${
              currentView === 'documents'
                ? 'border-indigo-500 bg-[#1c1c21] text-[#fafafa]'
                : 'border-transparent hover:bg-white/5 text-[#a1a1aa]'
            }`}
          >
            <FolderOpen className="w-5 h-5 shrink-0" />
            Documents
          </button>
        )}
      </div>
    </aside>
  )
}
