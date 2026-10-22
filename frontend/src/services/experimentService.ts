import apiClient from './apiClient'
import type { Experiment, ExperimentRequest, Page } from '../types'

export const experimentService = {
  async list(params: { page?: number; page_size?: number } = {}): Promise<Page<Experiment>> {
    const { data } = await apiClient.get<Page<Experiment>>('/experiments', { params })
    return data
  },

  async get(experimentId: string): Promise<Experiment> {
    const { data } = await apiClient.get<Experiment>(`/experiments/${experimentId}`)
    return data
  },

  async create(payload: ExperimentRequest): Promise<Experiment> {
    const { data } = await apiClient.post<Experiment>('/experiments', payload)
    return data
  },
}

export default experimentService
