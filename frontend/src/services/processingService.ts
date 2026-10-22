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
}

export default processingService
