import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, FileText } from 'lucide-react'
import type { SourceRef } from '../types'

interface SourceCardProps {
  source: SourceRef
}

export function SourceCard({ source }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false)
  const pageOrChunk =
    source.chunk_index != null ? `Chunk ${source.chunk_index + 1}` : null

  return (
    <div className="rounded-lg border border-white/6 bg-[#1c1c21] overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-[#fafafa] hover:bg-white/5 transition-colors"
      >
        <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
        <span className="truncate flex-1">
          {source.filename}
          {pageOrChunk && (
            <span className="text-[#a1a1aa] ml-1">({pageOrChunk})</span>
          )}
        </span>
        <ChevronDown
          className={`w-4 h-4 shrink-0 text-[#a1a1aa] transition-transform ${
            expanded ? 'rotate-180' : ''
          }`}
        />
      </button>
      <AnimatePresence>
        {expanded && source.snippet && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-l-2 border-indigo-500 bg-[#18181b] px-3 py-2"
          >
            <p className="text-xs text-[#a1a1aa] whitespace-pre-wrap">
              {source.snippet}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
