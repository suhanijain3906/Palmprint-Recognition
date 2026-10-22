import axios, { AxiosError } from 'axios'
import type { ApiErrorPayload } from '../types'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL,
  timeout: 120000,
  withCredentials: true,
})

/** Normalise an unknown error into a human readable message. */
export function describeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorPayload>
    const payload = axiosError.response?.data
    if (payload && payload.error && payload.error.message) {
      return payload.error.message
    }
    if (axiosError.code === 'ECONNABORTED') {
      return 'The request timed out. The server took too long to respond.'
    }
    if (!axiosError.response) {
      return 'The API could not be reached. Is the backend running?'
    }
    return `Request failed with status ${axiosError.response.status}.`
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred.'
}

/** Extract the structured error code when available. */
export function errorCode(error: unknown): string | undefined {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as ApiErrorPayload | undefined)?.error?.code
  }
  return undefined
}

/** Absolute URL for a download/inline resource served by the backend. */
export function absoluteUrl(path: string): string {
  if (path.startsWith('http')) return path
  const root = baseURL.replace(/\/api\/v1\/?$/, '')
  return `${root}${path}`
}

export default apiClient
