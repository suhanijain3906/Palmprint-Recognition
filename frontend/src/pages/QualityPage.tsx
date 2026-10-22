import { useCallback, useState } from 'react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState } from '../components/common/StateViews'
import { ImageRecordPicker } from '../components/common/ImageRecordPicker'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import processingService from '../services/processingService'
import imageService from '../services/imageService'
import { describeError } from '../services/apiClient'
import type { ProcessingResponse } from '../types'

interface QualityDetail {
  brightness?: { mean_intensity?: number; median_intensity?: number; is_dark?: boolean; is_bright?: boolean }
  contrast?: { rms_contrast?: number; std_intensity?: number; interpretation?: string }
  sharpness?: { variance_of_laplacian?: number; interpretation?: string }
  dimensions?: { width?: number; height?: number; megapixels?: number }
  entropy?: number
  sub_scores?: Record<string, number>
  weights?: Record<string, number>
  combined_score?: number
  combined_score_is_experimental?: boolean
  warnings?: string[]
  limitations?: string[]
}

export function QualityPage() {
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 24 }), []))
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [result, setResult] = useState<ProcessingResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const { notify } = useNotify()

  const run = useCallback(async () => {
    if (!selectedId) return
    setBusy(true)
    try {
      setResult(await processingService.quality({ image_id: selectedId }))
    } catch (error) {
      notify(describeError(error), 'error')
      setResult(null)
    } finally {
      setBusy(false)
    }
  }, [selectedId, notify])

  const detail = (result?.result ?? {}) as QualityDetail

  const metrics: Array<{ label: string; value: string; explanation: string }> = [
    {
      label: 'Mean brightness',
      value: detail.brightness?.mean_intensity?.toFixed(1) ?? '—',
      explanation: 'Average pixel intensity (0–255). Extremely low values indicate under-exposure.',
    },
    {
      label: 'RMS contrast',
      value: detail.contrast?.rms_contrast?.toFixed(3) ?? '—',
      explanation: 'Standard deviation of intensity normalised to [0,1]. Low values indicate flat images.',
    },
    {
      label: 'Variance of Laplacian',
      value: detail.sharpness?.variance_of_laplacian?.toFixed(1) ?? '—',
      explanation: 'A blur proxy: sharper images have higher variance. Not an absolute focus measure.',
    },
    {
      label: 'Dimensions',
      value: detail.dimensions?.width
        ? `${detail.dimensions.width} × ${detail.dimensions.height}`
        : '—',
      explanation: 'Pixel resolution. Very small images may not resolve ridge detail.',
    },
    {
      label: 'Entropy',
      value: typeof detail.entropy === 'number' ? detail.entropy.toFixed(2) : '—',
      explanation: 'Shannon entropy of the intensity histogram — an information-content indicator.',
    },
  ]

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Quality assessment"
        description="Objective quality indicators with explicit interpretation caveats. The combined score is an experimental, unvalidated heuristic."
      />

      <Card title="Select an image" className="mb-4">
        {images.loading && <LoadingState />}
        {images.error && <ErrorState message={images.error} />}
        {images.data && (
          <ImageRecordPicker images={images.data.items} value={selectedId} onChange={setSelectedId} />
        )}
      </Card>

      <button type="button" className="btn-primary mb-4" disabled={!selectedId || busy} onClick={run}>
        {busy ? 'Analysing…' : 'Analyse quality'}
      </button>

      {result && (
        <>
          <Card title="Metrics" className="mb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                  <th className="py-2">Metric</th>
                  <th className="py-2">Value</th>
                  <th className="py-2">Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((metric) => (
                  <tr key={metric.label} className="border-b border-slate-100">
                    <td className="py-2 font-medium text-slate-700">{metric.label}</td>
                    <td className="py-2 font-mono text-slate-900">{metric.value}</td>
                    <td className="py-2 text-xs text-slate-500">{metric.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card title="Combined score" subtitle="Experimental heuristic — not scientifically validated">
            <p className="text-3xl font-semibold text-navy-900">
              {detail.combined_score?.toFixed(1) ?? '—'}
              <span className="ml-2 text-sm font-normal text-slate-400">/ 100</span>
            </p>
            {detail.sub_scores && (
              <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600 sm:grid-cols-4">
                {Object.entries(detail.sub_scores).map(([key, value]) => (
                  <div key={key}>
                    <dt className="capitalize text-slate-400">{key}</dt>
                    <dd className="font-medium">{typeof value === 'number' ? value.toFixed(3) : String(value)}</dd>
                  </div>
                ))}
              </dl>
            )}
            {(detail.limitations ?? result.limitations).map((item) => (
              <p key={item} className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
                {item}
              </p>
            ))}
          </Card>
        </>
      )}
    </div>
  )
}

export default QualityPage
