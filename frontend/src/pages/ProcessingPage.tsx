import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Download } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState, EmptyState } from '../components/common/StateViews'
import { ImageRecordPicker } from '../components/common/ImageRecordPicker'
import { ImagePanel } from '../components/visualization/ImagePanel'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import processingService from '../services/processingService'
import imageService from '../services/imageService'
import { absoluteUrl, describeError } from '../services/apiClient'
import type { ProcessingResponse } from '../types'

const ENHANCEMENT_ALGORITHMS = [
  { id: 'histogram_equalization', label: 'Histogram equalisation' },
  { id: 'clahe', label: 'CLAHE' },
  { id: 'median_filter', label: 'Median filter' },
  { id: 'gaussian_filter', label: 'Gaussian filter' },
  { id: 'sharpen', label: 'Sharpening' },
]

export function ProcessingPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 24 }), []))
  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get('image'))
  const [algorithm, setAlgorithm] = useState('clahe')
  const [roi, setRoi] = useState<ProcessingResponse | null>(null)
  const [enhanced, setEnhanced] = useState<ProcessingResponse | null>(null)
  const [busy, setBusy] = useState<'roi' | 'enhance' | null>(null)
  const { notify } = useNotify()

  useEffect(() => {
    if (selectedId) setSearchParams({ image: selectedId })
  }, [selectedId, setSearchParams])

  const runRoi = useCallback(async () => {
    if (!selectedId) return
    setBusy('roi')
    try {
      setRoi(await processingService.extractRoi({ image_id: selectedId }))
    } catch (error) {
      notify(describeError(error), 'error')
      setRoi(null)
    } finally {
      setBusy(null)
    }
  }, [selectedId, notify])

  const runEnhance = useCallback(async () => {
    if (!selectedId) return
    setBusy('enhance')
    try {
      setEnhanced(await processingService.enhance({ image_id: selectedId, algorithm }))
    } catch (error) {
      notify(describeError(error), 'error')
      setEnhanced(null)
    } finally {
      setBusy(null)
    }
  }, [selectedId, algorithm, notify])

  const selectedImage = images.data?.items.find((image) => image.id === selectedId)

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Processing"
        description="Run ROI extraction and enhancement pipelines. Every result is produced by the ML service and recorded as a job."
      />

      <Card title="Select an image" className="mb-4">
        {images.loading && <LoadingState />}
        {images.error && <ErrorState message={images.error} />}
        {images.data && (
          <ImageRecordPicker images={images.data.items} value={selectedId} onChange={setSelectedId} />
        )}
      </Card>

      {selectedImage && (
        <Card className="mb-4" title="Original image">
          <ImagePanel
            src={absoluteUrl(selectedImage.download_url)}
            alt={selectedImage.original_filename}
            caption={`${selectedImage.width} x ${selectedImage.height} px - ${(selectedImage.size_bytes / 1024).toFixed(1)} KiB`}
          />
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="ROI extraction" subtitle="Approximate region proposal (not anatomical)">
          <button
            type="button"
            className="btn-primary"
            disabled={!selectedId || busy !== null}
            onClick={runRoi}
          >
            {busy === 'roi' ? 'Running…' : 'Extract ROI'}
          </button>
          {roi && (
            <div className="mt-4 space-y-3">
              <p className="text-xs text-slate-500">
                Algorithm: {roi.algorithm} v{roi.algorithm_version} · {roi.processing_time_ms.toFixed(1)} ms
              </p>
              {roi.artifacts.length > 0 ? (
                <ImagePanel
                  src={absoluteUrl(roi.artifacts[0].download_url)}
                  alt="ROI output"
                  caption="Approximate region proposal produced by the classical contour pipeline."
                />
              ) : (
                <p className="text-sm text-slate-500">No ROI image was returned.</p>
              )}
              {roi.warnings.map((warning) => (
                <p key={warning} className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
                  {warning}
                </p>
              ))}
              {roi.artifacts[0] && (
                <a href={absoluteUrl(roi.artifacts[0].download_url)} download className="btn-secondary">
                  <Download className="mr-2 h-4 w-4" /> Download ROI
                </a>
              )}
            </div>
          )}
        </Card>

        <Card title="Enhancement">
          <label className="label" htmlFor="algorithm">
            Algorithm
          </label>
          <select
            id="algorithm"
            className="input mb-3"
            value={algorithm}
            onChange={(event) => setAlgorithm(event.target.value)}
          >
            {ENHANCEMENT_ALGORITHMS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="btn-primary"
            disabled={!selectedId || busy !== null}
            onClick={runEnhance}
          >
            {busy === 'enhance' ? 'Running…' : 'Apply enhancement'}
          </button>
          {enhanced && (
            <div className="mt-4 space-y-3">
              <p className="text-xs text-slate-500">
                {enhanced.algorithm} v{enhanced.algorithm_version} · {enhanced.processing_time_ms.toFixed(1)} ms
              </p>
              {enhanced.artifacts.length > 0 ? (
                <ImagePanel
                  src={absoluteUrl(enhanced.artifacts[0].download_url)}
                  alt="Enhanced output"
                  caption={`Enhanced with ${enhanced.algorithm}; the original is never modified.`}
                />
              ) : (
                <p className="text-sm text-slate-500">No enhanced image was returned.</p>
              )}
              {enhanced.artifacts[0] && (
                <a
                  href={absoluteUrl(enhanced.artifacts[0].download_url)}
                  download
                  className="btn-secondary"
                >
                  <Download className="mr-2 h-4 w-4" /> Download enhanced
                </a>
              )}
            </div>
          )}
        </Card>
      </div>

      {!selectedId && (
        <div className="mt-4">
          <EmptyState title="No image selected" description="Choose an uploaded image to begin processing." />
        </div>
      )}
    </div>
  )
}

export default ProcessingPage
