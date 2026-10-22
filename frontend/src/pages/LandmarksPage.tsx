import { useCallback, useState } from 'react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState, EmptyState } from '../components/common/StateViews'
import { ImageRecordPicker } from '../components/common/ImageRecordPicker'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import processingService from '../services/processingService'
import imageService from '../services/imageService'
import { absoluteUrl, describeError } from '../services/apiClient'
import type { ProcessingResponse } from '../types'

interface LandmarkDetail {
  detector?: string
  keypoint_count?: number
  points?: Array<{ x: number; y: number }>
  note?: string
  is_anatomical?: boolean
  warnings?: string[]
  limitations?: string[]
}

export function LandmarksPage() {
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 24 }), []))
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [result, setResult] = useState<ProcessingResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const { notify } = useNotify()

  const run = useCallback(async () => {
    if (!selectedId) return
    setBusy(true)
    try {
      setResult(await processingService.landmarks({ image_id: selectedId }))
    } catch (error) {
      notify(describeError(error), 'error')
      setResult(null)
    } finally {
      setBusy(false)
    }
  }, [selectedId, notify])

  const detail = (result?.result ?? {}) as LandmarkDetail
  const points = detail.points ?? []

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Landmarks & feature points"
        description="Feature-point visualisation. Detected ORB keypoints are NOT anatomical palm landmarks and are labelled accordingly."
      />

      <Card title="Select an image" className="mb-4">
        {images.loading && <LoadingState />}
        {images.error && <ErrorState message={images.error} />}
        {images.data && (
          <ImageRecordPicker images={images.data.items} value={selectedId} onChange={setSelectedId} />
        )}
      </Card>

      <button type="button" className="btn-primary mb-4" disabled={!selectedId || busy} onClick={run}>
        {busy ? 'Detecting…' : 'Detect feature points'}
      </button>

      {result && (
        <>
          <Card title="Overlay">
            {result.artifacts.length > 0 ? (
              <img
                src={absoluteUrl(result.artifacts[0].download_url)}
                alt="Feature point overlay"
                className="mx-auto max-h-96 object-contain"
              />
            ) : (
              <EmptyState
                title="No overlay was produced"
                description="The selected algorithm did not return a visualisation."
              />
            )}
          </Card>

          <Card title="Detection details" className="mt-4">
            <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <div>
                <dt className="text-slate-400">Detector</dt>
                <dd>{detail.detector ?? result.algorithm}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Points</dt>
                <dd>{detail.keypoint_count ?? points.length}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Anatomical</dt>
                <dd>{detail.is_anatomical ? 'Yes' : 'No (feature points)'}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Time</dt>
                <dd>{result.processing_time_ms.toFixed(1)} ms</dd>
              </div>
            </dl>

            {detail.note && (
              <p className="mt-3 rounded border border-blue-200 bg-blue-50 px-2 py-1 text-xs text-blue-800">
                {detail.note}
              </p>
            )}

            {points.length > 0 && (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm text-slate-600">
                  Show coordinates ({points.length})
                </summary>
                <div className="mt-2 max-h-48 overflow-auto rounded border border-slate-200 p-2 font-mono text-xs">
                  {points.slice(0, 100).map((point, index) => (
                    <div key={index}>
                      ({point.x}, {point.y})
                    </div>
                  ))}
                </div>
              </details>
            )}

            {[...(detail.limitations ?? []), ...(detail.warnings ?? []), ...result.limitations].map((item) => (
              <p key={item} className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
                {item}
              </p>
            ))}
          </Card>
        </>
      )}

      {!selectedId && (
        <EmptyState title="No image selected" description="Choose an image to detect feature points." />
      )}
    </div>
  )
}

export default LandmarksPage
