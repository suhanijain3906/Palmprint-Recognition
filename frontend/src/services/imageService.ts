import apiClient from './apiClient'
import type { ImageRecord, ImageUploadResponse, JobRecord, MessageResponse, Page } from '../types'

export interface ListImagesParams {
  page?: number
  page_size?: number
}

export const imageService = {
  async list(params: ListImagesParams = {}): Promise<Page<ImageRecord>> {
    const { data } = await apiClient.get<Page<ImageRecord>>('/images', { params })
    return data
  },

  async get(imageId: string): Promise<ImageRecord> {
    const { data } = await apiClient.get<ImageRecord>(`/images/${imageId}`)
    return data
  },

  async upload(
    file: File,
    meta: { label?: string; subject_id?: string; notes?: string } = {},
    onProgress?: (percent: number) => void,
  ): Promise<ImageUploadResponse> {
    const form = new FormData()
    form.append('file', file)
    if (meta.label) form.append('label', meta.label)
    if (meta.subject_id) form.append('subject_id', meta.subject_id)
    if (meta.notes) form.append('notes', meta.notes)

    const { data } = await apiClient.post<ImageUploadResponse>('/images/upload', form, {
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded / event.total) * 100))
        }
      },
    })
    return data
  },

  async update(
    imageId: string,
    meta: { label?: string; subject_id?: string; notes?: string },
  ): Promise<ImageRecord> {
    const { data } = await apiClient.patch<ImageRecord>(`/images/${imageId}`, meta)
    return data
  },

  async remove(imageId: string): Promise<MessageResponse> {
    const { data } = await apiClient.delete<MessageResponse>(`/images/${imageId}`)
    return data
  },

  async jobs(imageId: string): Promise<JobRecord[]> {
    const { data } = await apiClient.get<JobRecord[]>(`/images/${imageId}/jobs`)
    return data
  },
}

export default imageService
