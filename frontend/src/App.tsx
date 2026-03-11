import { useState, useEffect, useCallback } from 'react'
import { Toaster } from 'react-hot-toast'
import { Menu, PanelLeftClose } from 'lucide-react'
import { Sidebar } from './components/Sidebar'
import { ChatInterface } from './components/ChatInterface'
import { DocumentsPage } from './components/DocumentsPage'
import { listChats } from './api/client'
import type { ChatSession } from './types'
import './index.css'

export default function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [view, setView] = useState<'chat' | 'documents'>('chat')

  const loadSessions = useCallback(() => {
    listChats()
      .then(setSessions)
      .catch(() => setSessions([]))
  }, [])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  useEffect(() => {
    if (activeId && !sessions.some((s) => s.id === activeId)) {
      setActiveId(sessions[0]?.id ?? null)
    }
  }, [sessions, activeId])

  return (
    <div className="h-screen flex bg-[#0f0f11]">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { background: '#1c1c21', color: '#fafafa', border: '1px solid rgba(255,255,255,0.06)' },
        }}
      />

      {/* Mobile: overlay when sidebar open */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar: overlay on mobile, inline on desktop with expand/collapse */}
      <div
        className={`fixed lg:relative inset-y-0 left-0 z-30 flex flex-col bg-[#18181b] border-r border-white/5 transition-all duration-200 ease-out overflow-hidden
          ${sidebarOpen ? 'translate-x-0 w-[280px]' : '-translate-x-full lg:translate-x-0 lg:w-0'}
        `}
      >
        <Sidebar
          sessions={sessions}
          activeId={activeId}
          onSelect={(id) => {
            setActiveId(id)
            setView('chat')
            setSidebarOpen(false)
          }}
          onNewChat={() => setActiveId(null)}
          onSessionsChange={loadSessions}
          onNavigateToDocuments={() => setView('documents')}
          currentView={view}
          collapsed={false}
        />
      </div>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="shrink-0 h-14 border-b border-white/5 flex items-center gap-2 px-4 lg:px-6">
          <button
            type="button"
            onClick={() => setSidebarOpen((o) => !o)}
            className="p-2 rounded-lg text-[#a1a1aa] hover:bg-white/5 hover:text-[#fafafa] transition-colors"
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
          <h1 className="text-lg font-semibold text-[#fafafa]">
            {view === 'documents' ? 'Documents' : 'RAG Chat'}
          </h1>
        </header>
        {view === 'documents' ? (
          <DocumentsPage />
        ) : (
          <ChatInterface
            sessionId={activeId}
            onSessionTitleChange={loadSessions}
          />
        )}
      </main>
    </div>
  )
}
