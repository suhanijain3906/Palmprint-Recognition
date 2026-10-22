import apiClient from './apiClient'
import type { HealthResponse } from '../types'

export const healthService = {
  async get(): Promise<HealthResponse> {
    const { data } = await apiClient.get<HealthResponse>('/health')
    return data
  },
}

export default healthService
