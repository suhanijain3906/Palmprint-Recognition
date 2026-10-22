import { useCallback, useState } from 'react'
import { Download, FileText } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'
import { LoadingState, ErrorState, EmptyState } from '../components/common/StateViews'
import { useAsyncData } from '../hooks/useAsync'
import { useNotify } from '../components/common/Notification'
import reportService from '../services/reportService'
import { describeError } from '../services/apiClient'
import type { Report, ReportCreateRequest } from '../types'

const REPORT_TYPES = [
  { id: 'processing', label: 'Processing report' },
  { id: 'experiment', label: 'Experiment report' },
  { id: 'summary', label: 'Summary report' },
]

function StatusBadge({ status }: { status: string }) {
  const colour =
    status === 'ready' || status === 'completed'
      ? 'bg-emerald-50 text-emerald-700'
      : status === 'failed'
        ? 'bg-red-50 text-red-700'
        : 'bg-slate-100 text-slate-600'
  return <span className={`rounded-full px-2 py-0.5 text-xs ${colour}`}>{status}</span>
}

export function ReportsPage() {
  const reports = useAsyncData(useCallback(() => reportService.list({ page_size: 50 }), []))
  const [title, setTitle] = useState('Palmprint processing report')
  const [reportType, setReportType] = useState('processing')
  const [creating, setCreating] = useState(false)
  const [downloading, setDownloading] = useState<string | null>(null)
  const { notify } = useNotify()

  const create = useCallback(async () => {
    setCreating(true)
    try {
      const payload: ReportCreateRequest = {
        title: title.trim() || 'Palmprint processing report',
        report_type: reportType,
        job_ids: [],
        include_images: false,
      }
      await reportService.create(payload)
      notify('Report generated.', 'success')
      reports.reload()
    } catch (error) {
      notify(describeError(error), 'error')
    } finally {
      setCreating(false)
    }
  }, [title, reportType, notify, reports])

  const download = useCallback(
    async (report: Report) => {
      setDownloading(report.id)
      try {
        await reportService.download(report)
      } catch (error) {
        notify(describeError(error), 'error')
      } finally {
        setDownloading(null)
      }
    },
    [notify],
  )

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Reports"
        description="Generate PDF reports from processing runs and experiments. Reports summarise the recorded metrics and their stated limitations."
      />

      <Card title="New report" className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="report-title">
              Title
            </label>
            <input
              id="report-title"
              className="input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={200}
            />
          </div>
          <div>
            <label className="label" htmlFor="report-type">
              Report type
            </label>
            <select
              id="report-type"
              className="input"
              value={reportType}
              onChange={(event) => setReportType(event.target.value)}
            >
              {REPORT_TYPES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button type="button" className="btn-primary mt-4" disabled={creating} onClick={create}>
          <FileText className="mr-2 h-4 w-4" /> {creating ? 'Generating…' : 'Generate report'}
        </button>
        <p className="mt-2 text-xs text-slate-500">
          Empty reports are allowed: if no jobs or experiments are linked, the report documents that
          no runs were included rather than inventing results.
        </p>
      </Card>

      {reports.loading && <LoadingState />}
      {reports.error && <ErrorState message={reports.error} />}
      {reports.data && reports.data.items.length === 0 && (
        <EmptyState title="No reports yet" description="Generate a report to see it here." />
      )}
      {reports.data && reports.data.items.length > 0 && (
        <div className="space-y-3">
          {reports.data.items.map((report) => (
            <Card key={report.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-navy-900">{report.title}</p>
                  <p className="text-xs text-slate-500">
                    {report.report_type} · {new Date(report.created_at).toLocaleString()}
                    {report.size_bytes != null && ` · ${(report.size_bytes / 1024).toFixed(1)} KB`}
                  </p>
                </div>
                <StatusBadge status={report.status} />
              </div>
              {report.error_message && (
                <p className="mt-2 rounded border border-red-200 bg-red-50 px-2 py-1 text-xs text-red-700">
                  {report.error_message}
                </p>
              )}
              <button
                type="button"
                className="btn-secondary mt-3"
                disabled={downloading === report.id || report.status === 'failed'}
                onClick={() => download(report)}
              >
                <Download className="mr-2 h-4 w-4" />
                {downloading === report.id ? 'Downloading…' : 'Download PDF'}
              </button>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default ReportsPage
