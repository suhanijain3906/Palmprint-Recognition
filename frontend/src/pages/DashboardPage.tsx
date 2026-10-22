import { Link } from 'react-router-dom'
import { useCallback } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { Upload, FlaskConical, FileText, Activity } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { StatCard } from '../components/dashboard/StatCard'
import { LoadingState, ErrorState, EmptyState } from '../components/common/StateViews'
import { useAsyncData } from '../hooks/useAsync'
import healthService from '../services/healthService'
import imageService from '../services/imageService'
import experimentService from '../services/experimentService'
import reportService from '../services/reportService'

export function DashboardPage() {
  const health = useAsyncData(useCallback(() => healthService.get(), []))
  const images = useAsyncData(useCallback(() => imageService.list({ page_size: 5 }), []))
  const experiments = useAsyncData(useCallback(() => experimentService.list({ page_size: 5 }), []))
  const reports = useAsyncData(useCallback(() => reportService.list({ page_size: 5 }), []))

  const loading = images.loading || experiments.loading || reports.loading
  const error = images.error || experiments.error || reports.error

  const stats = [
    {
      label: 'Uploaded images',
      value: images.data?.meta.total ?? '—',
      icon: Upload,
      to: '/upload',
    },
    {
      label: 'Experiments',
      value: experiments.data?.meta.total ?? '—',
      icon: FlaskConical,
      to: '/experiments',
    },
    {
      label: 'Reports',
      value: reports.data?.meta.total ?? '—',
      icon: FileText,
      to: '/reports',
    },
    {
      label: 'ML service',
      value: health.data ? String(health.data.ml_service.status ?? 'unknown') : '—',
      icon: Activity,
      to: '/about',
    },
  ]

  const recentQuality =
    experiments.data?.items
      .flatMap((experiment) =>
        experiment.results
          .filter((result) => result.unit === 'score')
          .map((result) => ({ name: experiment.name.slice(0, 14), value: result.value ?? 0 })),
      )
      .slice(0, 8) ?? []

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Dashboard"
        description="Overview of processed images, experiments and results. Counts reflect only the data stored in this deployment."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      {loading && <LoadingState label="Loading dashboard data…" />}
      {error && !loading && <ErrorState message={error} />}

      {!loading && !error && (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card title="Recent uploads">
            {images.data && images.data.items.length > 0 ? (
              <ul className="divide-y divide-slate-100">
                {images.data.items.map((image) => (
                  <li key={image.id} className="flex items-center justify-between py-2 text-sm">
                    <span className="truncate text-slate-700">{image.original_filename}</span>
                    <span className="text-xs text-slate-400">
                      {new Date(image.created_at).toLocaleDateString()}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                title="No images yet"
                description="Upload your first palmprint image to get started."
                action={
                  <Link to="/upload" className="btn-primary">
                    Upload image
                  </Link>
                }
              />
            )}
          </Card>

          <Card title="Recent experiments">
            {experiments.data && experiments.data.items.length > 0 ? (
              <ul className="divide-y divide-slate-100">
                {experiments.data.items.map((experiment) => (
                  <li key={experiment.id} className="flex items-center justify-between py-2 text-sm">
                    <span className="truncate text-slate-700">{experiment.name}</span>
                    <span className="text-xs capitalize text-slate-400">{experiment.status}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No experiments yet" description="Configure an experiment to record results." />
            )}
          </Card>

          <Card title="Quality score distribution" subtitle="From recorded experiment results only" className="lg:col-span-2">
            {recentQuality.length > 0 ? (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={recentQuality}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#14b8a6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState
                title="No score data available"
                description="Charts appear only when real measured results exist. Demo data is never fabricated."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  )
}

export default DashboardPage
