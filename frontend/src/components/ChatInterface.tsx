import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Bot, User, ChevronDown, ChevronRight } from 'lucide-react'
import type { ChatMessage, SourceRef } from '../types'
import { getChat, streamChat } from '../api/client'
import { EmptyState } from './EmptyState'
import { ThinkingIndicator } from './ThinkingIndicator'
import { InputBar } from './InputBar'
import { SourceCard } from './SourceCard'

interface ChatInterfaceProps {
  sessionId: string | null
  onSessionTitleChange?: () => void
}

export function ChatInterface({ sessionId, onSessionTitleChange }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null)
  const [streamingSources, setStreamingSources] = useState<SourceRef[]>([])
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const streamingSourcesRef = useRef<SourceRef[]>([])

  useEffect(() => {
    if (!sessionId) {
      setMessages([])
      return
    }
    setLoading(true)
    setError(null)
    getChat(sessionId)
      .then((data) => {
        setMessages(data.messages || [])
        onSessionTitleChange?.()
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [sessionId, onSessionTitleChange])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = (content: string) => {
    if (!sessionId) return
    setStreamingStatus('Thinking...')
    setStreamingContent('')
    setStreamingSources([])
    setError(null)
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])

    streamChat(
      sessionId,
      content,
      {
        onStatus: setStreamingStatus,
        onToken: (token) => {
          setStreamingStatus(null)
          setStreamingContent((c) => c + token)
        },
        onSources: (sources) => {
          streamingSourcesRef.current = sources
          setStreamingSources(sources)
        },
        onDone: () => {
          setStreamingStatus(null)
          setStreamingContent((c) => {
            if (c) {
              const sources = streamingSourcesRef.current
              setMessages((prev) => [
                ...prev,
                {
                  id: `temp-assistant-${Date.now()}`,
                  session_id: sessionId,
                  role: 'assistant',
                  content: c,
                  created_at: new Date().toISOString(),
                  sources: sources?.length ? sources : undefined,
                },
              ])
              streamingSourcesRef.current = []
              setStreamingSources([])
              onSessionTitleChange?.()
            }
            return ''
          })
        },
        onError: (e) => {
          setStreamingStatus(null)
          setStreamingContent('')
          setError(e.message)
        },
      }
    )
  }

  if (!sessionId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-[#a1a1aa]">
        <p className="text-sm">Select a chat or create a new one</p>
      </div>
    )
  }

  const [sourcesOpen, setSourcesOpen] = useState<Record<string, boolean>>({})
  const showEmpty = !loading && messages.length === 0 && !streamingContent
  const displayMessages = streamingContent
    ? [
        ...messages.filter((m) => m.role === 'user' || (m.role === 'assistant' && m.id.startsWith('temp-') === false)),
        ...(messages.some((m) => m.role === 'assistant' && m.id.startsWith('temp-assistant-')))
          ? []
          : [{
              role: 'assistant' as const,
              content: streamingContent,
              isStreaming: true,
              sources: streamingSources.length ? streamingSources : undefined,
            }],
      ]
    : messages

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6">
          {loading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton h-16 rounded-2xl w-full" />
              ))}
            </div>
          )}

          {!loading && showEmpty && <EmptyState />}

          {!loading && !showEmpty && (
            <div className="space-y-6">
              <AnimatePresence>
                {displayMessages.map((msg, idx) => {
                  const isUser = msg.role === 'user'
                  const isStreaming = 'isStreaming' in msg && msg.isStreaming
                  const content = 'content' in msg ? msg.content : ''
                  const msgId = isStreaming ? 'streaming' : (msg as ChatMessage).id || String(idx)
                  const sources = (msg as ChatMessage).sources
                  const hasSources = sources && sources.length > 0
                  const sourcesExpanded = sourcesOpen[msgId] ?? false
                  return (
                    <motion.div
                      key={msgId}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.15, delay: idx * 0.05 }}
                      className={`flex flex-col gap-1 ${isUser ? 'items-end' : ''}`}
                    >
                      <div className={`flex gap-3 ${isUser ? 'justify-end' : ''}`}>
                        {!isUser && (
                          <div className="w-8 h-8 rounded-full bg-[#27272a] flex items-center justify-center shrink-0 mt-1">
                            <Bot className="w-4 h-4 text-indigo-400" />
                          </div>
                        )}
                        <div
                          className={`rounded-2xl px-4 py-3 max-w-[85%] ${
                            isUser
                              ? 'bg-indigo-500 text-white rounded-br-md'
                              : 'bg-[#27272a] text-[#fafafa] rounded-bl-md'
                          }`}
                        >
                          {isUser ? (
                            <p className="text-sm whitespace-pre-wrap">{content}</p>
                          ) : isStreaming ? (
                            <span className="text-sm whitespace-pre-wrap">
                              {content}
                              <span className="streaming-cursor" />
                            </span>
                          ) : (
                            <div className="prose prose-invert prose-sm max-w-none">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                        {isUser && (
                          <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center shrink-0 mt-1">
                            <User className="w-4 h-4 text-indigo-400" />
                          </div>
                        )}
                      </div>
                      {!isUser && hasSources && (
                        <div className="ml-11 w-full max-w-[85%]">
                          <button
                            type="button"
                            onClick={() => setSourcesOpen((prev) => ({ ...prev, [msgId]: !prev[msgId] }))}
                            className="flex items-center gap-2 text-xs text-[#a1a1aa] hover:text-[#fafafa] transition-colors py-1"
                          >
                            {sourcesExpanded ? (
                              <ChevronDown className="w-4 h-4" />
                            ) : (
                              <ChevronRight className="w-4 h-4" />
                            )}
                            <span>Sources ({sources!.length})</span>
                          </button>
                          <AnimatePresence>
                            {sourcesExpanded && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden space-y-2 mt-2"
                              >
                                {sources!.map((src, i) => (
                                  <SourceCard key={i} source={src} />
                                ))}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}
                    </motion.div>
                  )
                })}
              </AnimatePresence>

              {streamingStatus && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#27272a] flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-indigo-400" />
                  </div>
                  <ThinkingIndicator label={streamingStatus} />
                </motion.div>
              )}

              {error && (
                <p className="text-sm text-red-400 bg-red-500/10 rounded-lg px-4 py-2">{error}</p>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </div>

      <InputBar
        onSend={handleSend}
        disabled={!!streamingStatus || !!streamingContent}
      />
    </div>
  )
}
