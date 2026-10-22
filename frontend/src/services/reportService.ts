import apiClient from './apiClient'
import type { Page, Report, ReportCreateRequest } from '../types'

export const reportService = {
  async list(params: { page?: number; page_size?: number } = {}): Promise<Page<Report>> {
    const { data } = await apiClient.get<Page<Report>>('/reports', { params })
    return data
  },

  async get(reportId: string): Promise<Report> {
    const { data } = await apiClient.get<Report>(`/reports/${reportId}`)
    return data
  },

  async create(payload: ReportCreateRequest): Promise<Report> {
    const { data } = await apiClient.post<Report>('/reports', payload)
    return data
  },

  /** Trigger a browser download of the generated PDF report. */
  async download(report: Report): Promise<void> {
    const response = await apiClient.get(`/reports/${report.id}/download`, {
      responseType: 'blob',
    })
    const blobUrl = window.URL.createObjectURL(
      new Blob([response.data], { type: 'application/pdf' }),
    )
    const anchor = document.createElement('a')
    anchor.href = blobUrl
    anchor.download = `report-${report.id}.pdf`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.URL.revokeObjectURL(blobUrl)
  },
}

export default reportService
