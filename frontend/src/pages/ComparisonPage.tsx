import { useCallback, useState } from 'react'
import { Download } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState } from '../components/common/StateViews'
import { ImageRecordPicker } from '../components/common/ImageRecordPicker'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import recognitionService from '../services/recognitionService'
import imageService from '../services/imageService'
import { absoluteUrl, describeError } from '../services/apiClient'
import type { ComparisonResponse } from '../types'

export function ComparisonPage() {
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 24 }), []))
  const [imageA, setImageA] = useState<string | null>(null)
  const [imageB, setImageB] = useState<string | null>(null)
  const [result, setResult] = useState<ComparisonResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const { notify } = useNotify()

  const run = useCallback(async () => {
    if (!imageA || !imageB) {
      notify('Select two images to compare.', 'error')
      return
    }
    setBusy(true)
    try {
      setResult(await recognitionService.imageCompare({ image_a_id: imageA, image_b_id: imageB }))
    } catch (error) {
      notify(describeError(error), 'error')
      setResult(null)
    } finally {
      setBusy(false)
    }
  }, [imageA, imageB, notify])

  const imageARecord = images.data?.items.find((image) => image.id === imageA)
  const imageBRecord = images.data?.items.find((image) => image.id === imageB)

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Comparison"
        description="Side-by-side and pixel-level comparison of two images. PSNR and SSIM assume aligned, comparable captures."
      />

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

      <button type="button" className="btn-primary mt-4" disabled={busy || !imageA || !imageB} onClick={run}>
        {busy ? 'Comparing…' : 'Compare images'}
      </button>

      {(imageARecord || imageBRecord) && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {imageARecord && (
            <Card title="A — original">
              <img
                src={absoluteUrl(imageARecord.download_url)}
                alt={imageARecord.original_filename}
                className="mx-auto max-h-64 object-contain"
              />
            </Card>
          )}
          {imageBRecord && (
            <Card title="B — original">
              <img
                src={absoluteUrl(imageBRecord.download_url)}
                alt={imageBRecord.original_filename}
                className="mx-auto max-h-64 object-contain"
              />
            </Card>
          )}
        </div>
      )}

      {result && (
        <Card title="Comparison metrics" className="mt-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-400">PSNR (dB)</p>
              <p className="text-2xl font-semibold text-navy-900">
                {result.psnr_db != null ? result.psnr_db.toFixed(2) : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">SSIM</p>
              <p className="text-2xl font-semibold text-navy-900">
                {result.ssim != null ? result.ssim.toFixed(4) : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Aligned</p>
              <p className="text-sm">{result.aligned ? 'Yes' : 'No'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Resized</p>
              <p className="text-sm">{result.resized ? 'Yes' : 'No'}</p>
            </div>
          </div>

          {result.artifacts.length > 0 && (
            <div className="mt-4">
              <p className="label">Difference visualisation</p>
              <img
                src={absoluteUrl(result.artifacts[0].download_url)}
                alt="Difference image"
                className="mx-auto max-h-64 object-contain"
              />
              <a href={absoluteUrl(result.artifacts[0].download_url)} download className="btn-secondary mt-3">
                <Download className="mr-2 h-4 w-4" /> Download difference
              </a>
            </div>
          )}

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

export default ComparisonPage
