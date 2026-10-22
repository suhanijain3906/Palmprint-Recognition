import apiClient from './apiClient'
import type { ComparisonResponse, RecognitionResponse } from '../types'

export interface RecognitionParams {
  image_a_id: string
  image_b_id: string
  detector?: string
  lowe_ratio?: number
}

export interface ComparisonParams {
  image_a_id: string
  image_b_id: string
}

export const recognitionService = {
  async compare(params: RecognitionParams): Promise<RecognitionResponse> {
    const { data } = await apiClient.post<RecognitionResponse>('/recognition/compare', params)
    return data
  },

  async imageCompare(params: ComparisonParams): Promise<ComparisonResponse> {
    const { data } = await apiClient.post<ComparisonResponse>('/comparison', params)
    return data
  },
}

export default recognitionService
