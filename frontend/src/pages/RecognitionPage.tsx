import { useCallback, useState } from 'react'
import { AlertTriangle, Info } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState } from '../components/common/StateViews'
import { ImageRecordPicker } from '../components/common/ImageRecordPicker'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import recognitionService from '../services/recognitionService'
import imageService from '../services/imageService'
import { describeError } from '../services/apiClient'
import type { RecognitionResponse } from '../types'

export function RecognitionPage() {
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 24 }), []))
  const [imageA, setImageA] = useState<string | null>(null)
  const [imageB, setImageB] = useState<string | null>(null)
  const [loweRatio, setLoweRatio] = useState(0.75)
  const [result, setResult] = useState<RecognitionResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const { notify } = useNotify()

  const run = useCallback(async () => {
    if (!imageA || !imageB) {
      notify('Select two images to compare.', 'error')
      return
    }
    if (imageA === imageB) {
      notify('Select two different images.', 'error')
      return
    }
    setBusy(true)
    try {
      setResult(
        await recognitionService.compare({ image_a_id: imageA, image_b_id: imageB, lowe_ratio: loweRatio }),
      )
    } catch (error) {
      notify(describeError(error), 'error')
      setResult(null)
    } finally {
      setBusy(false)
    }
  }, [imageA, imageB, loweRatio, notify])

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Recognition (experimental)"
        description="Feature-based similarity between two palmprints. This is an uncalibrated matcher, not a trained biometric identity model."
      />

      <div className="mb-4 flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          The similarity score is a matching-statistics index. It is <strong>not</strong> a
          calibrated probability and must not be interpreted as identity confidence.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Image A">
          {images.loading && <LoadingState />}
          {images.error && <ErrorState message={images.error} />}
          {images.data && (
            <ImageRecordPicker images={images.data.items} value={imageA} onChange={setImageA} />
          )}
        </Card>
        <Card title="Image B">
          {images.data && (
            <ImageRecordPicker images={images.data.items} value={imageB} onChange={setImageB} />
          )}
        </Card>
      </div>

      <Card title="Matcher parameters" className="mt-4">
        <label className="label" htmlFor="lowe">
          Lowe ratio ({loweRatio.toFixed(2)})
        </label>
        <input
          id="lowe"
          type="range"
          min={0.3}
          max={0.95}
          step={0.01}
          value={loweRatio}
          onChange={(event) => setLoweRatio(Number(event.target.value))}
          className="w-full max-w-sm"
        />
      </Card>

      <button type="button" className="btn-primary mt-4" disabled={busy || !imageA || !imageB} onClick={run}>
        {busy ? 'Comparing…' : 'Run experimental comparison'}
      </button>

      {result && (
        <Card title="Result" className="mt-4">
          {!result.trained_model_available && (
            <div className="mb-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>No trained recognition model is installed. This result uses the classical feature matcher only.</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-400">Similarity</p>
              <p className="text-2xl font-semibold text-navy-900">
                {result.similarity_score != null ? result.similarity_score.toFixed(3) : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Score kind</p>
              <p className="text-sm">{result.score_kind}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Matcher</p>
              <p className="text-sm">
                {result.matcher} v{result.matcher_version}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Trained model</p>
              <p className="text-sm">{result.trained_model_available ? 'Available' : 'Not available'}</p>
            </div>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-600 sm:grid-cols-4">
            {Object.entries(result.details).map(([key, value]) => (
              <div key={key}>
                <dt className="capitalize text-slate-400">{key.replace(/_/g, ' ')}</dt>
                <dd className="font-medium">{String(value)}</dd>
              </div>
            ))}
          </dl>
          {result.limitations.map((item) => (
            <p key={item} className="mt-2 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600">
              {item}
            </p>
          ))}
        </Card>
      )}
    </div>
  )
}

export default RecognitionPage
