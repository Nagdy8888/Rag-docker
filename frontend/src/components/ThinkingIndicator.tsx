import { motion } from 'framer-motion'

interface ThinkingIndicatorProps {
  label?: string
}

export function ThinkingIndicator({ label = 'Thinking...' }: ThinkingIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-2 text-sm text-[#a1a1aa] mb-2"
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
      </span>
      <span>{label}</span>
    </motion.div>
  )
}
