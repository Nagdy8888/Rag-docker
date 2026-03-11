import { MessageSquare } from 'lucide-react'

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 text-[#a1a1aa]">
      <div className="rounded-full bg-[#1c1c21] p-6 mb-4 border border-white/5">
        <MessageSquare className="w-12 h-12 text-indigo-500/80" />
      </div>
      <p className="text-base font-medium text-[#fafafa]">Start a conversation</p>
      <p className="text-sm mt-1">Send a message below to get started.</p>
    </div>
  )
}
