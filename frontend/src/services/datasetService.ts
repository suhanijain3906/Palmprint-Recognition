import apiClient from './apiClient'
import type { Dataset } from '../types'

export const datasetService = {
  async list(): Promise<Dataset[]> {
    const { data } = await apiClient.get<Dataset[]>('/datasets')
    return data
  },

  async get(datasetId: string): Promise<Dataset> {
    const { data } = await apiClient.get<Dataset>(`/datasets/${datasetId}`)
    return data
  },
}

export default datasetService
