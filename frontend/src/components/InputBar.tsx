import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

interface InputBarProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
}

const MIN_ROWS = 1
const MAX_ROWS = 4

export function InputBar({ onSend, disabled, placeholder = 'Message...' }: InputBarProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(MAX_ROWS * 24, Math.max(MIN_ROWS * 24, el.scrollHeight))}px`
  }, [value])

  const handleSubmit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t border-white/5 bg-[#0f0f11] p-4">
      <div className="flex gap-3 items-end max-w-3xl mx-auto bg-[#1c1c21] rounded-xl border border-white/5 focus-within:ring-2 focus-within:ring-indigo-500/40">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={MIN_ROWS}
          className="flex-1 resize-none bg-transparent px-4 py-3 text-[#fafafa] placeholder-[#71717a] outline-none rounded-xl min-h-[48px] max-h-[120px] text-sm"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!value.trim() || disabled}
          className="p-2.5 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed active:scale-[0.97] transition-all mb-1 mr-1"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
