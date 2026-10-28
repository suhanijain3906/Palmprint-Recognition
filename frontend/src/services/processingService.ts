import apiClient from './apiClient'
import type { ProcessingResponse } from '../types'

export interface RoiParams {
  image_id: string
  algorithm?: string
  parameters?: Record<string, unknown>
}

export interface EnhancementParams {
  image_id: string
  algorithm?: string
  parameters?: Record<string, unknown>
}

export interface QualityParams {
  image_id: string
}

export interface FeatureParams {
  image_id: string
  detector?: string
  parameters?: Record<string, unknown>
}

export interface LandmarkParams {
  image_id: string
  detector?: string
  parameters?: Record<string, unknown>
}

export const processingService = {
  async extractRoi(params: RoiParams): Promise<ProcessingResponse> {
    const { data } = await apiClient.post<ProcessingResponse>('/processing/roi', params)
    return data
  },

  async enhance(params: EnhancementParams): Promise<ProcessingResponse> {
    const { data } = await apiClient.post<ProcessingResponse>('/processing/enhancement', params)
    return data
  },

  async quality(params: QualityParams): Promise<ProcessingResponse> {
    const { data } = await apiClient.post<ProcessingResponse>('/processing/quality', params)
    return data
  },

  async features(params: FeatureParams): Promise<ProcessingResponse> {
    const { data } = await apiClient.post<ProcessingResponse>('/processing/features', params)
    return data
  },

  async landmarks(params: LandmarkParams): Promise<ProcessingResponse> {
    const { data } = await apiClient.post<ProcessingResponse>('/processing/landmarks', params)
    return data
  },

  async analyzePalmprint(params: { image_id?: string; file?: File }): Promise<any> {
    if (params.file) {
      const form = new FormData()
      form.append('file', params.file)
      const { data } = await apiClient.post('/analysis/palmprint', form)
      return data
    }
    const { data } = await apiClient.post('/analysis/palmprint', { image_id: params.image_id })
    return data
  },

  async getAnalysis(analysisId: string): Promise<any> {
    const { data } = await apiClient.get(`/analysis/${analysisId}`)
    return data
  },
}

export default processingService
