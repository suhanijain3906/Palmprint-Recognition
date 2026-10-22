import { absoluteUrl } from '../../services/apiClient'
import type { ImageRecord } from '../../types'

interface ImageRecordPickerProps {
  images: ImageRecord[]
  value: string | null
  onChange: (imageId: string) => void
  label?: string
}

export function ImageRecordPicker({ images, value, onChange, label }: ImageRecordPickerProps) {
  if (images.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No images available yet. Upload a palmprint image first.
      </p>
    )
  }

  return (
    <div>
      {label && <p className="label">{label}</p>}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {images.map((image) => {
          const selected = image.id === value
          return (
            <button
              key={image.id}
              type="button"
              onClick={() => onChange(image.id)}
              className={`overflow-hidden rounded-lg border text-left transition ${
                selected ? 'border-primary-500 ring-2 ring-primary-200' : 'border-slate-200 hover:border-primary-300'
              }`}
            >
              <img
                src={absoluteUrl(image.download_url)}
                alt={image.original_filename}
                className="h-24 w-full bg-slate-900/5 object-contain"
                loading="lazy"
              />
              <span className="block truncate px-2 py-1 text-xs text-slate-600">
                {image.original_filename}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default ImageRecordPicker
