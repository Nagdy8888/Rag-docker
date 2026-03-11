import { useState, useCallback } from 'react'
import { Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { DocumentList } from './DocumentList'
import {
  uploadDocuments,
  isSupportedFile,
  getSupportedExtensionsString,
} from '../api/client'

const MAX_FILE_MB = 50

function filterFiles(files: FileList | File[]): File[] {
  const list = Array.from(files)
  return list.filter((file) => {
    if (!isSupportedFile(file)) return false
    if (file.size > MAX_FILE_MB * 1024 * 1024) return false
    return true
  })
}

export function DocumentsPage() {
  const [uploading, setUploading] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleFiles = useCallback(
    async (files: File[]) => {
      const valid = filterFiles(files)
      if (valid.length === 0) {
        toast.error(
          `No valid files. Use ${getSupportedExtensionsString()}, max ${MAX_FILE_MB} MB each.`
        )
        return
      }
      if (valid.length < files.length) {
        toast(`Using ${valid.length} of ${files.length} files (some skipped).`, {
          icon: 'ℹ️',
        })
      }
      setUploading(true)
      try {
        const res = await uploadDocuments(valid)
        const ok = res.results.filter((r) => r.success).length
        const failed = res.results.filter((r) => !r.success)
        if (ok > 0) {
          toast.success(`${ok} document(s) uploaded and processing.`)
          setRefreshTrigger((c) => c + 1)
        }
        failed.forEach((r) => {
          toast.error(`${r.filename}: ${r.error || 'Failed'}`)
        })
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Upload failed')
      } finally {
        setUploading(false)
      }
    },
    []
  )

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (uploading) return
      const files = e.dataTransfer?.files
      if (files?.length) handleFiles(Array.from(files))
    },
    [uploading, handleFiles]
  )

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const onFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files?.length) handleFiles(Array.from(files))
      e.target.value = ''
    },
    [handleFiles]
  )

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="shrink-0 px-4 lg:px-6 py-4 border-b border-white/5 space-y-3">
        <p className="text-sm text-[#a1a1aa]">
          Watched folder: <code className="text-[#fafafa] bg-[#27272a] px-1.5 py-0.5 rounded">documents/</code>
          {' · '}
          Uploaded files are saved there, then chunked and stored in Supabase for the chat agent.
        </p>

        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          className={`
            border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-2
            transition-colors
            ${uploading ? 'border-amber-500/50 bg-amber-500/5 cursor-wait' : 'border-white/10 hover:border-indigo-500/50 bg-white/[0.02]'}
          `}
        >
          <input
            type="file"
            multiple
            accept={['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.xls', '.md'].join(',')}
            onChange={onFileInputChange}
            disabled={uploading}
            className="hidden"
            id="doc-upload-input"
          />
          <label
            htmlFor="doc-upload-input"
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm cursor-pointer
              ${uploading ? 'pointer-events-none opacity-70' : 'bg-indigo-500 hover:bg-indigo-600 text-white'}
            `}
          >
            {uploading ? (
              <span className="animate-pulse">Processing…</span>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload documents
              </>
            )}
          </label>
          <p className="text-xs text-[#71717a]">
            {getSupportedExtensionsString()} · max {MAX_FILE_MB} MB per file
          </p>
          <p className="text-xs text-[#71717a]">
            Or drag and drop files here
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <DocumentList refreshTrigger={refreshTrigger} />
      </div>
    </div>
  )
}
