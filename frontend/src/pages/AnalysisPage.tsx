import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AlertTriangle, BarChart3, FileImage, Info, RefreshCw } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState, EmptyState } from '../components/common/StateViews'
import { ImageRecordPicker } from '../components/common/ImageRecordPicker'
import { ImagePanel } from '../components/visualization/ImagePanel'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import imageService from '../services/imageService'
import processingService from '../services/processingService'
import { absoluteUrl, describeError } from '../services/apiClient'
import type { ProcessingResponse } from '../types'

export function AnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 48 }), []))
  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get('image') || searchParams.get('image_id'))
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [roi, setRoi] = useState<ProcessingResponse | null>(null)
  const [quality, setQuality] = useState<ProcessingResponse | null>(null)
  const [enhanced, setEnhanced] = useState<ProcessingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { notify } = useNotify()
  const navigate = useNavigate()

  useEffect(() => {
    if (selectedId) {
      setSearchParams({ image: selectedId })
    }
  }, [selectedId, setSearchParams])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    setRoi(null)
    setQuality(null)
    setEnhanced(null)
    const f = e.target.files?.[0]
    if (!f) {
      setFile(null)
      setPreview(null)
      return
    }
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp']
    if (!validTypes.includes(f.type)) {
      setError('Invalid file type. Please upload a PNG, JPEG, TIFF, or BMP image.')
      setFile(null)
      setPreview(null)
      return
    }
    if (f.size > 12 * 1024 * 1024) {
      setError('File too large. Maximum size is 12 MB.')
      setFile(null)
      setPreview(null)
      return
    }
    setFile(f)
    const reader = new FileReader()
    reader.onload = () => setPreview(reader.result as string)
    reader.readAsDataURL(f)
  }, [])

  const runAnalysis = useCallback(async () => {
    if (!selectedId && !file) {
      notify('Select an existing image or upload a new one.', 'error')
      return
    }
    setAnalyzing(true)
    setError(null)
    try {
      let imageId = selectedId
      if (!imageId && file) {
        const res = await imageService.upload(file)
        imageId = res.image.id
        setSelectedId(imageId)
        notify('Image uploaded successfully.', 'success')
      }
      if (!imageId) throw new Error('No image available for analysis')
      
      const [roiRes, qualityRes, enhRes] = await Promise.allSettled([
        processingService.extractRoi({ image_id: imageId }),
        processingService.quality({ image_id: imageId }),
        processingService.enhance({ image_id: imageId, algorithm: 'clahe' }),
      ])
      
      if (roiRes.status === 'fulfilled') setRoi(roiRes.value)
      if (qualityRes.status === 'fulfilled') setQuality(qualityRes.value)
      if (enhRes.status === 'fulfilled') setEnhanced(enhRes.value)
      
      const failures = [roiRes, qualityRes, enhRes].filter(r => r.status === 'rejected')
      if (failures.length === 3) {
        throw new Error(describeError((failures[0] as PromiseRejectedResult).reason))
      }
      if (failures.length > 0) {
        notify('Some analysis steps completed with issues.', 'info')
      } else {
        notify('Analysis completed.', 'success')
      }
    } catch (err) {
      const msg = describeError(err)
      setError(msg)
      notify(msg, 'error')
    } finally {
      setAnalyzing(false)
    }
  }, [selectedId, file, notify])

  const reset = useCallback(() => {
    setFile(null)
    setPreview(null)
    setRoi(null)
    setQuality(null)
    setEnhanced(null)
    setError(null)
    setAnalyzing(false)
  }, [])

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Palmprint Analysis"
        description="Upload or select a palmprint image and run a full analysis pipeline (ROI extraction, quality assessment, and enhancement)."
      />

      <div className="mb-4 flex items-start gap-2 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          Results are produced by the classical computer-vision pipeline and are not probabilistic identity matches.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Select existing image">
          {images.loading && <LoadingState />}
          {images.error && <ErrorState message={images.error} />}
          {images.data && (
            <ImageRecordPicker images={images.data.items} value={selectedId} onChange={setSelectedId} />
          )}
        </Card>
        <Card title="Or upload a new image">
          <div className="space-y-3">
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 p-6 text-center hover:border-primary-400">
              <FileImage className="h-8 w-8 text-slate-400" />
              <span className="mt-2 text-sm text-slate-600">Click to select or drop image</span>
              <span className="mt-1 text-xs text-slate-400">PNG, JPEG, TIFF, BMP (max 12 MB)</span>
              <input type="file" accept="image/png,image/jpeg,image/jpg,image/tiff,image/bmp" className="hidden" onChange={handleFileSelect} disabled={analyzing} />
            </label>
            {file && <p className="text-sm text-slate-600">Selected: {file.name}</p>}
            {preview && (
              <div className="overflow-hidden rounded-lg border border-slate-200">
                <img src={preview} alt="Preview" className="max-h-64 w-full object-contain" />
              </div>
            )}
          </div>
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="button" className="btn-primary" disabled={analyzing || (!selectedId && !file)} onClick={runAnalysis}>
          {analyzing ? 'Analyzing...' : 'Analyze'}
        </button>
        <button type="button" className="btn-secondary" disabled={analyzing} onClick={reset}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Reset
        </button>
        {selectedId && (
          <button type="button" className="btn-secondary" onClick={() => navigate(`/processing?image=${selectedId}`)}>
            Open in Processing
          </button>
        )}
      </div>

      {analyzing && (
        <div className="mt-4">
          <LoadingState label="Running analysis pipeline..." />
        </div>
      )}

      {error && !analyzing && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      {(roi || quality || enhanced) && (
        <div className="mt-6 space-y-4">
          <h2 className="text-lg font-semibold text-navy-900">Analysis Results</h2>
          
          <div className="grid gap-4 lg:grid-cols-2">
            {roi && (
              <Card title="ROI Extraction" subtitle={`${roi.algorithm} v${roi.algorithm_version || '1.0.0'}`}>
                <p className="mb-2 text-xs text-slate-500">Processing time: {roi.processing_time_ms.toFixed(1)} ms</p>
                {roi.artifacts.length > 0 ? (
                  <ImagePanel src={absoluteUrl(roi.artifacts[0].download_url)} alt="ROI" caption="Region of interest proposal" />
                ) : (
                  <EmptyState title="No ROI artifact" description="ROI was computed but no image artifact was returned." />
                )}
                {roi.warnings?.map(w => (
                  <p key={w} className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800 flex items-start gap-1">
                    <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />{w}
                  </p>
                ))}
              </Card>
            )}
            
            {enhanced && (
              <Card title="Enhancement (CLAHE)" subtitle={`${enhanced.algorithm} v${enhanced.algorithm_version || '1.0.0'}`}>
                <p className="mb-2 text-xs text-slate-500">Processing time: {enhanced.processing_time_ms.toFixed(1)} ms</p>
                {enhanced.artifacts.length > 0 ? (
                  <ImagePanel src={absoluteUrl(enhanced.artifacts[0].download_url)} alt="Enhanced" caption="Enhanced image" />
                ) : (
                  <EmptyState title="No enhancement artifact" description="Enhancement completed without an artifact." />
                )}
              </Card>
            )}
          </div>

          {quality && (
            <Card title="Quality Assessment">
              <div className="mb-2 flex items-center gap-2 text-sm text-slate-600">
                <BarChart3 className="h-4 w-4" />
                <span>{quality.algorithm} v{quality.algorithm_version || '1.0.0'} • {quality.processing_time_ms.toFixed(1)} ms</span>
              </div>
              {quality.metrics && Object.keys(quality.metrics).length > 0 && (
                <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                  {Object.entries(quality.metrics).map(([k, v]) => (
                    <div key={k} className="rounded border border-slate-200 p-2">
                      <dt className="text-xs capitalize text-slate-400">{k.replace(/_/g, ' ')}</dt>
                      <dd className="font-medium">{typeof v === 'number' ? v.toFixed(3) : String(v)}</dd>
                    </div>
                  ))}
                </dl>
              )}
              {quality.warnings?.map(w => (
                <p key={w} className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800 flex items-start gap-1">
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />{w}
                </p>
              ))}
              <p className="mt-2 text-xs text-slate-500">Quality scores are heuristic measurements, not calibrated biometric quality scores.</p>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default AnalysisPage


