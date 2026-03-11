import { useEffect, useState } from 'react'
import { FileText, FileSpreadsheet, FileType, AlertCircle } from 'lucide-react'
import type { DocumentFile } from '../types'
import { listDocuments, getDocumentsStatus } from '../api/client'

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function iconForType(fileType: string) {
  const t = fileType.toLowerCase()
  if (t === 'pdf') return <FileText className="w-8 h-8 text-red-400" />
  if (t === 'docx' || t === 'doc') return <FileText className="w-8 h-8 text-blue-400" />
  if (t === 'csv' || t === 'xlsx' || t === 'xls') return <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
  return <FileType className="w-8 h-8 text-zinc-400" />
}

export function DocumentList({ refreshTrigger }: { refreshTrigger?: number }) {
  const [docs, setDocs] = useState<DocumentFile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<Awaited<ReturnType<typeof getDocumentsStatus>> | null>(null)

  const load = () => {
    setError(null)
    listDocuments()
      .then(setDocs)
      .catch((e) => {
        setError(e.message)
        setDocs([])
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    if (refreshTrigger !== undefined && refreshTrigger > 0) {
      load()
    }
  }, [refreshTrigger])

  useEffect(() => {
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (docs.length === 0 && !loading) {
      getDocumentsStatus().then(setStatus).catch(() => setStatus(null))
    } else {
      setStatus(null)
    }
  }, [docs.length, loading])

  if (loading && docs.length === 0) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 rounded-xl bg-[#1c1c21] border border-white/5 skeleton" />
        ))}
      </div>
    )
  }

  if (error && docs.length === 0) {
    return (
      <div className="p-6 text-center text-[#a1a1aa] text-sm">
        <p>Could not load documents. Make sure the backend is running and Phase 2 migration is applied.</p>
        <p className="mt-2 text-red-400">{error}</p>
      </div>
    )
  }

  if (docs.length === 0 && status) {
    return (
      <div className="p-6 max-w-lg mx-auto">
        <div className="rounded-xl bg-[#1c1c21] border border-white/5 p-5 flex gap-3">
          <AlertCircle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-sm text-[#a1a1aa] space-y-2">
            <p className="text-[#fafafa] font-medium">No documents showing yet</p>
            {!status.phase2_tables_ok ? (
              <>
                <p>Phase 2 database tables are missing. Run the Phase 2 SQL migration in Supabase:</p>
                <ol className="list-decimal list-inside space-y-1 text-[#fafafa]">
                  <li>Open Supabase Dashboard → SQL Editor → New query</li>
                  <li>Paste the contents of <code className="bg-[#27272a] px-1 rounded">supabase_phase2.sql</code></li>
                  <li>Click Run</li>
                  <li>Restart the backend: <code className="bg-[#27272a] px-1 rounded">docker compose restart backend</code></li>
                </ol>
                {status.db_error && <p className="text-red-400 text-xs mt-2">{status.db_error}</p>}
              </>
            ) : status.files_count === 0 ? (
              <>
                <p>No supported files in the watched folder. Put PDF, DOCX, TXT, CSV, Excel, or Markdown files in:</p>
                <p className="text-[#fafafa] font-mono text-xs break-all">{status.documents_folder}</p>
                <p>On your host that is the <code className="bg-[#27272a] px-1 rounded">documents/</code> folder in the project root. Then restart the backend so it picks them up.</p>
              </>
            ) : (
              <>
                <p>Backend sees {status.files_count} file(s) on disk but none are in the database yet. Check backend logs:</p>
                <p className="font-mono text-xs text-[#fafafa]">docker compose logs backend</p>
                <p>Look for &quot;Processed existing file&quot; or errors (e.g. OpenAI key, missing tables).</p>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {docs.map((d) => (
        <div
          key={d.id}
          className="rounded-xl bg-[#1c1c21] border border-white/5 p-4 flex flex-col gap-2 hover:border-white/10 transition-colors"
        >
          <div className="flex items-start gap-3">
            <div className="shrink-0 w-12 h-12 rounded-lg bg-[#27272a] flex items-center justify-center">
              {iconForType(d.file_type)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-[#fafafa] truncate" title={d.filename}>
                {d.filename}
              </p>
              <p className="text-xs text-[#71717a] mt-0.5">
                {formatBytes(d.file_size)} · {formatDate(d.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-[#71717a]">{d.chunk_count} chunks</span>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                d.status === 'ready'
                  ? 'bg-green-500/20 text-green-400'
                  : d.status === 'error'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-amber-500/20 text-amber-400 animate-pulse'
              }`}
            >
              {d.status === 'ready' ? 'Ready' : d.status === 'error' ? 'Error' : 'Processing'}
            </span>
          </div>
          {d.status === 'error' && d.error_message && (
            <p className="text-xs text-red-400 mt-1 line-clamp-2" title={d.error_message}>
              {d.error_message}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
