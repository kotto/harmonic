// ──────────────────────────────────────────────
// File Upload Component
// ──────────────────────────────────────────────
import { useCallback, useRef, useState, DragEvent, ChangeEvent } from 'react'
import { cn } from '../../utils/helpers'
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from './Button'
import { formatFileSize } from '../../utils/helpers'

interface UploadedFile {
  id: string
  file: File
  preview?: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string | null
  serverResponse?: unknown
}

interface FileUploadProps {
  accept?: string
  maxSize?: number // in bytes
  maxFiles?: number
  multiple?: boolean
  onUpload: (files: File[]) => Promise<unknown[]>
  onRemove?: (fileId: string) => void
  label?: string
  hint?: string
  disabled?: boolean
  showPreview?: boolean
}

export function FileUpload({
  accept,
  maxSize = 50 * 1024 * 1024, // 50MB default
  maxFiles = 1,
  multiple = false,
  onUpload,
  onRemove,
  label = 'Déposer les fichiers ici',
  hint,
  disabled,
  showPreview = true,
}: FileUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (maxSize && file.size > maxSize) {
      return `Le fichier dépasse la taille maximale de ${formatFileSize(maxSize)}`
    }
    if (accept) {
      const acceptedTypes = accept.split(',').map((t) => t.trim())
      const isValidType = acceptedTypes.some((type) => {
        if (type.endsWith('/*')) {
          return file.type.startsWith(type.slice(0, -1))
        }
        return file.type === type || file.name.endsWith(type)
      })
      if (!isValidType) {
        return `Type de fichier non autorisé. Types acceptés: ${accept}`
      }
    }
    return null
  }

  const generateId = () => Math.random().toString(36).substring(2, 9)

  const addFiles = useCallback(
    (newFiles: FileList | File[]) => {
      const fileArray = Array.from(newFiles)
      const availableSlots = maxFiles - files.length

      if (availableSlots <= 0) return

      const validFiles = fileArray.slice(0, availableSlots).map((file) => {
        const error = validateFile(file)
        return {
          id: generateId(),
          file,
          status: error ? 'error' as const : 'pending' as const,
          progress: 0,
          error,
        }
      })

      setFiles((prev) => [...prev, ...validFiles])
    },
    [files.length, maxFiles, validateFile]
  )

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) setIsDragging(true)
  }, [disabled])

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)
      if (!disabled && e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files)
      }
    },
    [disabled, addFiles]
  )

  const handleFileSelect = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        addFiles(e.target.files)
        e.target.value = ''
      }
    },
    [addFiles]
  )

  const removeFile = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
    onRemove?.(fileId)
  }, [onRemove])

  const handleUpload = useCallback(async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending' || f.status === 'error')
    if (pendingFiles.length === 0) return

    // Update status to uploading
    setFiles((prev) =>
      prev.map((f) => (pendingFiles.some((pf) => pf.id === f.id) ? { ...f, status: 'uploading' as const, progress: 0 } : f))
    )

    try {
      const fileObjects = pendingFiles.map((f) => f.file)
      const responses = await onUpload(fileObjects)

      setFiles((prev) =>
        prev.map((f) => {
          const responseIndex = pendingFiles.findIndex((pf) => pf.id === f.id)
          if (responseIndex >= 0) {
            return { ...f, status: 'success' as const, progress: 100, serverResponse: responses[responseIndex] }
          }
          return f
        })
      )
    } catch (error) {
      setFiles((prev) =>
        prev.map((f) => {
          if (pendingFiles.some((pf) => pf.id === f.id)) {
            return {
              ...f,
              status: 'error' as const,
              error: error instanceof Error ? error.message : 'Erreur lors du téléversement',
            }
          }
          return f
        })
      )
    }
  }, [files, onUpload])

  const retryUpload = useCallback(
    (fileId: string) => {
      const file = files.find((f) => f.id === fileId)
      if (!file || file.status !== 'error') return

      setFiles((prev) =>
        prev.map((f) => (f.id === fileId ? { ...f, status: 'pending' as const, error: undefined, progress: 0 } : f))
      )
    },
    [files]
  )

  const hasErrors = files.some((f) => f.status === 'error')
  const hasPending = files.some((f) => f.status === 'pending')
  const isUploading = files.some((f) => f.status === 'uploading')
  const allSuccess = files.length > 0 && files.every((f) => f.status === 'success')

  return (
    <div className="w-full">
      <div
        ref={(el) => {
          if (el) el.addEventListener('click', () => !disabled && fileInputRef.current?.click())
        }}
        className={cn(
          'relative border-2 border-dashed rounded-xl p-8 text-center transition-all',
          'cursor-pointer',
          disabled ? 'opacity-50 cursor-not-allowed' : '',
          isDragging ? 'border-primary-500 bg-primary-50' : 'border-slate-300 hover:border-primary-400',
          hasErrors && 'border-red-300 bg-red-50',
          allSuccess && 'border-green-300 bg-green-50'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={disabled}
          aria-label="Sélectionner des fichiers"
        />

        <div className="relative z-10">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 mb-4">
            <Upload className="w-6 h-6" />
          </div>
          <p className="text-lg font-medium text-slate-900">{label}</p>
          {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
          {maxSize && <p className="mt-1 text-xs text-slate-400">Taille max: {formatFileSize(maxSize)} par fichier</p>}
        </div>
      </div>

      {files.length > 0 && (
        <div className="mt-4 space-y-2" role="list" aria-label="Fichiers sélectionnés">
          {files.map((file) => (
            <div
              key={file.id}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                file.status === 'error' ? 'border-red-200 bg-red-50' : 'border-slate-200 bg-white'
              )}
              role="listitem"
            >
              {showPreview && file.preview && (
                <img src={file.preview} alt={file.file.name} className="w-10 h-10 rounded-lg object-cover" />
              )}
              {!showPreview || !file.preview ? (
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400">
                  <FileText className="w-5 h-5" />
                </div>
              ) : null}

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">{file.file.name}</p>
                <p className="text-xs text-slate-500">{formatFileSize(file.file.size)}</p>
                {file.status === 'uploading' && (
                  <div className="mt-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-600 transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
                {file.status === 'error' && file.error && (
                  <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {file.error}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {file.status === 'pending' && !hasErrors && (
                  <>
                    <Button variant="ghost" size="sm" onClick={() => removeFile(file.id)} aria-label="Supprimer">
                      <X className="w-4 h-4" />
                    </Button>
                  </>
                )}
                {file.status === 'error' && (
                  <Button variant="ghost" size="sm" onClick={() => retryUpload(file.id)} aria-label="Réessayer">
                    <Loader2 className="w-4 h-4" />
                  </Button>
                )}
                {file.status === 'success' && (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                )}
                {file.status === 'uploading' && (
                  <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {(hasPending || hasErrors) && !isUploading && (
        <div className="mt-4 flex justify-end">
          <Button onClick={handleUpload} isLoading={isUploading} disabled={isUploading || files.length === 0}>
            {isUploading ? 'Téléversement...' : 'Téléverser'}
          </Button>
        </div>
      )}

      {allSuccess && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-800">
          <CheckCircle className="w-5 h-5" />
          <span className="text-sm font-medium">Tous les fichiers ont été téléversés avec succès</span>
        </div>
      )}
    </div>
  )
}