import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCallback } from 'react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { ImageDropzone, type SelectedFile } from '../components/upload/ImageDropzone'
import { useNotify } from '../components/common/Notification'
import imageService from '../services/imageService'
import { describeError } from '../services/apiClient'
import type { ImageRecord } from '../types'

export function UploadPage() {
  const [selected, setSelected] = useState<SelectedFile | null>(null)
  const [label, setLabel] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [notes, setNotes] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploaded, setUploaded] = useState<ImageRecord | null>(null)
  const { notify } = useNotify()
  const navigate = useNavigate()

  const resetForm = useCallback(() => {
    setSelected(null)
    setLabel('')
    setSubjectId('')
    setNotes('')
  }, [])

  const handleUpload = useCallback(async () => {
    if (!selected) return
    setUploading(true)
    setProgress(0)
    try {
      const response = await imageService.upload(
        selected.file,
        { label: label || undefined, subject_id: subjectId || undefined, notes: notes || undefined },
        setProgress,
      )
      setUploaded(response.image)
      notify('Image uploaded and validated successfully.', 'success')
      if (response.warnings) {
        for (const warning of response.warnings) {
          if (warning) notify(warning, 'info')
        }
      }
    } catch (error) {
      notify(describeError(error), 'error')
    } finally {
      setUploading(false)
    }
  }, [selected, label, subjectId, notes, notify])

  const clearAll = useCallback(() => {
    resetForm()
  }, [resetForm])

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Upload a palmprint image"
        description="The file is validated against its actual content (not just the extension) before it is stored. The original is kept unmodified."
      />

      <div className="grid gap-4 md:gap-5 lg:grid-cols-2">
        <Card title="Image" className="h-full">
          <ImageDropzone value={selected} onChange={setSelected} disabled={uploading} />
        </Card>

        <Card title="Optional annotations" className="h-full">
          <div className="space-y-4">
            <div>
              <label className="label" htmlFor="label">Label</label>
              <input id="label" className="input" placeholder="e.g., Left Hand" value={label} onChange={(event) => setLabel(event.target.value)} maxLength={120} disabled={uploading} />
            </div>
            <div>
              <label className="label" htmlFor="subject">Subject identifier</label>
              <input id="subject" className="input" placeholder="e.g., S-001" value={subjectId} onChange={(event) => setSubjectId(event.target.value)} maxLength={120} disabled={uploading} />
              <p className="mt-1 text-xs text-slate-500">A consistent pseudonymous identifier can be used for multiple samples from the same research participant.</p>
            </div>
            <div>
              <label className="label" htmlFor="notes">Notes</label>
              <textarea id="notes" className="input" rows={4} placeholder="Add observations or research notes about this palmprint..." value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={500} disabled={uploading} />
            </div>
          </div>
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="button" className="btn-primary" disabled={!selected || uploading} onClick={handleUpload}>
          {uploading ? 'Uploading...' : 'Upload image'}
        </button>
        {(selected || label || subjectId || notes) && !uploading && (
          <button type="button" className="btn-secondary" onClick={clearAll}>Clear</button>
        )}
      </div>

      {uploading && (
        <div className="mt-4">
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-primary-600 transition-all" style={{ width: progress + '%' }} />
          </div>
          <p className="mt-1 text-xs text-slate-500">{progress}% uploaded</p>
        </div>
      )}

      {uploaded && (
        <Card title="Uploaded image" className="mt-6">
          <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div><dt className="text-slate-400">ID</dt><dd className="truncate font-mono text-xs">{uploaded.id}</dd></div>
            <div><dt className="text-slate-400">Dimensions</dt><dd>{uploaded.width} × {uploaded.height}</dd></div>
            <div><dt className="text-slate-400">Format</dt><dd>{uploaded.media_type}</dd></div>
            <div><dt className="text-slate-400">SHA-256</dt><dd className="truncate font-mono text-xs">{uploaded.checksum_sha256.slice(0,12)}…</dd></div>
          </dl>
          <div className="mt-4 flex gap-3">
            <button type="button" className="btn-primary" onClick={() => navigate('/processing?image=' + uploaded.id)}>Process this image</button>
            <button type="button" className="btn-secondary" onClick={() => { setSelected(null); setUploaded(null); setLabel(''); setSubjectId(''); setNotes(''); }}>Upload another</button>
          </div>
        </Card>
      )}
    </div>
  )
}

export default UploadPage
