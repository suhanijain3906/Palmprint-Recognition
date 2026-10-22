import { useCallback, useState } from 'react'
import { Play } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState, EmptyState } from '../components/common/StateViews'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import experimentService from '../services/experimentService'
import imageService from '../services/imageService'
import { describeError } from '../services/apiClient'
import type { Experiment } from '../types'

const OPERATIONS = [
  { id: 'enhancement', label: 'Enhancement' },
  { id: 'roi', label: 'ROI extraction' },
  { id: 'quality', label: 'Quality assessment' },
  { id: 'features', label: 'Feature extraction' },
]

function StatusBadge({ status }: { status: string }) {
  const colour =
    status === 'completed'
      ? 'bg-emerald-50 text-emerald-700'
      : status === 'failed'
        ? 'bg-red-50 text-red-700'
        : 'bg-slate-100 text-slate-600'
  return <span className={`rounded-full px-2 py-0.5 text-xs ${colour}`}>{status}</span>
}

export function ExperimentsPage() {
  const experiments = useAsyncData(useCallback(() => experimentService.list({ page_size: 50 }), []))
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 50 }), []))
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [operation, setOperation] = useState('enhancement')
  const [algorithm, setAlgorithm] = useState('clahe')
  const [selectedImages, setSelectedImages] = useState<string[]>([])
  const [creating, setCreating] = useState(false)
  const [open, setOpen] = useState<string | null>(null)
  const { notify } = useNotify()

  const toggleImage = (imageId: string) => {
    setSelectedImages((prev) =>
      prev.includes(imageId) ? prev.filter((id) => id !== imageId) : [...prev, imageId],
    )
  }

  const create = useCallback(async () => {
    if (!name.trim()) {
      notify('Enter an experiment name.', 'error')
      return
    }
    setCreating(true)
    try {
      await experimentService.create({
        name: name.trim(),
        description: description || undefined,
        operation,
        algorithm,
        parameters: {},
        image_ids: selectedImages,
      })
      notify('Experiment created.', 'success')
      setName('')
      setDescription('')
      setSelectedImages([])
      experiments.reload()
    } catch (error) {
      notify(describeError(error), 'error')
    } finally {
      setCreating(false)
    }
  }, [name, description, operation, algorithm, selectedImages, notify, experiments])

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Experiments"
        description="Define reproducible processing or evaluation runs over selected images. Results are stored and can be exported as reports."
      />

      <Card title="New experiment" className="mb-6">
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <div>
              <label className="label" htmlFor="exp-name">
                Name
              </label>
              <input
                id="exp-name"
                className="input"
                value={name}
                onChange={(event) => setName(event.target.value)}
                maxLength={160}
              />
            </div>
            <div>
              <label className="label" htmlFor="exp-desc">
                Description
              </label>
              <textarea
                id="exp-desc"
                className="input"
                rows={2}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                maxLength={2000}
              />
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="label" htmlFor="exp-ops">
                Operation
              </label>
              <select
                id="exp-ops"
                className="input"
                value={operation}
                onChange={(event) => setOperation(event.target.value)}
              >
                {OPERATIONS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="exp-alg">
                Algorithm
              </label>
              <input
                id="exp-alg"
                className="input"
                value={algorithm}
                onChange={(event) => setAlgorithm(event.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="mt-4">
          <p className="label">Images ({selectedImages.length} selected)</p>
          {images.loading && <LoadingState />}
          {images.error && <ErrorState message={images.error} />}
          {images.data && images.data.items.length === 0 && (
            <p className="text-sm text-slate-500">No images available. Upload images first.</p>
          )}
          {images.data && images.data.items.length > 0 && (
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-6">
              {images.data.items.map((image) => {
                const active = selectedImages.includes(image.id)
                return (
                  <button
                    key={image.id}
                    type="button"
                    onClick={() => toggleImage(image.id)}
                    className={`overflow-hidden rounded-lg border text-left ${
                      active ? 'border-primary-500 ring-2 ring-primary-200' : 'border-slate-200'
                    }`}
                  >
                    <span className="block truncate px-2 py-1 text-xs">{image.original_filename}</span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <button type="button" className="btn-primary mt-4" disabled={creating} onClick={create}>
          <Play className="mr-2 h-4 w-4" /> {creating ? 'Creating…' : 'Create experiment'}
        </button>
      </Card>

      <h2 className="mb-3 text-base font-semibold text-navy-900">History</h2>
      {experiments.loading && <LoadingState />}
      {experiments.error && <ErrorState message={experiments.error} />}
      {experiments.data && experiments.data.items.length === 0 && (
        <EmptyState title="No experiments yet" description="Create your first experiment above." />
      )}
      {experiments.data && experiments.data.items.length > 0 && (
        <div className="space-y-3">
          {experiments.data.items.map((experiment: Experiment) => (
            <Card key={experiment.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-navy-900">{experiment.name}</p>
                  <p className="text-xs text-slate-500">
                    {experiment.operation} · {experiment.algorithm} ·{' '}
                    {new Date(experiment.created_at).toLocaleString()}
                  </p>
                </div>
                <StatusBadge status={experiment.status} />
              </div>
              {experiment.description && (
                <p className="mt-2 text-sm text-slate-600">{experiment.description}</p>
              )}
              {experiment.error_message && (
                <p className="mt-2 rounded border border-red-200 bg-red-50 px-2 py-1 text-xs text-red-700">
                  {experiment.error_message}
                </p>
              )}
              {experiment.results.length > 0 && (
                <div className="mt-3">
                  <button
                    type="button"
                    className="text-xs text-primary-700 hover:underline"
                    onClick={() => setOpen(open === experiment.id ? null : experiment.id)}
                  >
                    {open === experiment.id ? 'Hide' : 'Show'} {experiment.results.length} result(s)
                  </button>
                  {open === experiment.id && (
                    <table className="mt-2 w-full text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-left text-slate-500">
                          <th className="py-1">Label</th>
                          <th className="py-1">Value</th>
                          <th className="py-1">Image</th>
                        </tr>
                      </thead>
                      <tbody>
                        {experiment.results.map((result) => (
                          <tr key={result.id} className="border-b border-slate-100">
                            <td className="py-1">{result.label ?? result.kind}</td>
                            <td className="py-1 font-mono">
                              {result.value != null ? `${result.value} ${result.unit ?? ''}` : '—'}
                            </td>
                            <td className="py-1 font-mono text-slate-400">
                              {result.image_id ? result.image_id.slice(0, 8) : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default ExperimentsPage
