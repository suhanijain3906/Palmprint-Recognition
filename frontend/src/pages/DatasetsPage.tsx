import { useCallback } from 'react'
import { ExternalLink, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState } from '../components/common/StateViews'
import { useAsyncData } from '../hooks/useAsync'
import datasetService from '../services/datasetService'

export function DatasetsPage() {
  const datasets = useAsyncData(useCallback(() => datasetService.list(), []))

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Benchmark datasets"
        description="Catalogue of public palmprint benchmarks with official sources, licences and access procedures. No data is bundled or redistributed."
      />

      <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          These are biometric datasets. You must obtain them directly from the hosting institution
          and comply with its licence. Counts are shown only when a local installation was actually
          verified.
        </p>
      </div>

      {datasets.loading && <LoadingState label="Loading dataset catalogue…" />}
      {datasets.error && <ErrorState message={datasets.error} />}

      {datasets.data && (
        <div className="space-y-4">
          {datasets.data.map((dataset) => (
            <Card key={dataset.id} title={dataset.name}>
              <p className="text-sm text-slate-600">{dataset.description}</p>
              <dl className="mt-4 grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
                <div>
                  <dt className="text-slate-400">Modality</dt>
                  <dd className="text-slate-700">{dataset.modality}</dd>
                </div>
                <div>
                  <dt className="text-slate-400">Licence</dt>
                  <dd className="text-slate-700">{dataset.licence}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-slate-400">Access requirements</dt>
                  <dd className="text-slate-700">{dataset.access_requirements}</dd>
                </div>
                {dataset.reference && (
                  <div className="sm:col-span-2">
                    <dt className="text-slate-400">Reference</dt>
                    <dd className="text-slate-700">{dataset.reference}</dd>
                  </div>
                )}
              </dl>

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <a
                  href={dataset.official_source}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="btn-secondary"
                >
                  <ExternalLink className="mr-2 h-4 w-4" /> Official source
                </a>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs ${
                    dataset.availability.installed
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {dataset.availability.installed && <CheckCircle2 className="h-3 w-3" />}
                  {dataset.availability.installed ? 'Installed locally' : 'Not installed'}
                </span>
                {dataset.availability.verified_image_count != null && (
                  <span className="text-xs text-slate-500">
                    {dataset.availability.verified_image_count} images
                    {dataset.availability.verified_subject_count != null &&
                      ` · ${dataset.availability.verified_subject_count} subjects`}
                  </span>
                )}
              </div>
              <p className="mt-2 text-xs text-slate-500">{dataset.availability.message}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default DatasetsPage
