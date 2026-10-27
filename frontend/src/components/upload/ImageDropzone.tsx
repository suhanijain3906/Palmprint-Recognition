import { useCallback, useRef, useState } from 'react'
import { ImageUp, X } from 'lucide-react'

export interface SelectedFile {
  file: File
  previewUrl: string
}

interface ImageDropzoneProps {
  value: SelectedFile | null
  onChange: (value: SelectedFile | null) => void
  disabled?: boolean
}

const ACCEPTED = ['image/png', 'image/jpeg', 'image/jpg']
const ACCEPTED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
const MAX_BYTES = 12 * 1024 * 1024

export function validateFile(file: File): string | null {
  const name = file.name.toLowerCase()
  const isValidType = ACCEPTED.includes(file.type) || ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
  if (!isValidType) {
    return `Unsupported format "${file.type || 'unknown'}". Use JPG, JPEG, or PNG.`
  }
  if (file.size === 0) {
    return 'The selected file is empty.'
  }
  if (file.size > MAX_BYTES) {
    return `The file is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). The limit is 12 MB.`
  }
  return null
}

export function ImageDropzone({ value, onChange, disabled }: ImageDropzoneProps) {
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(
    (file: File) => {
      const message = validateFile(file)
      if (message) {
        setError(message)
        return
      }
      setError(null)
      onChange({ file, previewUrl: URL.createObjectURL(file) })
    },
    [onChange],
  )

  if (value) {
    return (
      <div className="space-y-3">
        <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
          <img
            src={value.previewUrl}
            alt={value.file.name}
            className="mx-auto max-h-80 w-full object-contain"
          />
          <button
            type="button"
            onClick={() => {
              URL.revokeObjectURL(value.previewUrl)
              onChange(null)
              setError(null)
            }}
            disabled={disabled}
            className="absolute right-2 top-2 rounded-full bg-white/90 p-1.5 text-slate-700 shadow hover:bg-white"
            aria-label="Remove image"
            title="Remove image"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-slate-600 sm:grid-cols-4">
          <div>
            <dt className="text-slate-400">Name</dt>
            <dd className="truncate font-medium" title={value.file.name}>
              {value.file.name}
            </dd>
          </div>
          <div>
            <dt className="text-slate-400">Size</dt>
            <dd className="font-medium">{(value.file.size / 1024).toFixed(1)} KB</dd>
          </div>
          <div>
            <dt className="text-slate-400">MIME type</dt>
            <dd className="font-medium">{value.file.type || 'unknown'}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Last modified</dt>
            <dd className="font-medium">{new Date(value.file.lastModified).toLocaleString()}</dd>
          </div>
        </dl>
      </div>
    )
  }

  return (
    <div>
      <div
        onDragOver={(event) => {
          event.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          if (disabled) return
          const file = event.dataTransfer.files?.[0]
          if (file) handleFile(file)
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Select palmprint image"
        onKeyDown={(event) => {
          if ((event.key === 'Enter' || event.key === ' ') && !disabled) {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-14 text-center transition-colors ${
          dragging ? 'border-primary-500 bg-primary-50' : 'border-slate-300 bg-slate-50 hover:border-primary-400'
        } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
      >
        <ImageUp className="h-8 w-8 text-primary-600" />
        <p className="text-sm font-medium text-slate-700">
          Drag & drop a palmprint image, or click to browse
        </p>
        <p className="text-xs text-slate-500">JPG, JPEG, PNG up to 12 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          className="hidden"
          disabled={disabled}
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) handleFile(file)
            event.target.value = ''
          }}
        />
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600" role="alert" aria-live="polite">
          {error}
        </p>
      )}
    </div>
  )
}

export default ImageDropzone
