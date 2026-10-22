import { describe, expect, it } from 'vitest'
import { describeError, absoluteUrl, errorCode } from '../src/services/apiClient'
import { AxiosError, AxiosHeaders } from 'axios'

function axiosErrorWith(data: unknown, status = 400): AxiosError {
  const error = new AxiosError(
    'Request failed',
    'ERR_BAD_REQUEST',
    undefined,
    undefined,
    {
      status,
      statusText: 'Bad Request',
      data,
      headers: new AxiosHeaders(),
      config: { headers: new AxiosHeaders() },
    },
  )
  return error
}

describe('describeError', () => {
  it('uses the backend error message when present', () => {
    const error = axiosErrorWith({
      status: 'error',
      error: { code: 'VALIDATION_ERROR', message: 'Unsupported image format', details: {} },
    })
    expect(describeError(error)).toBe('Unsupported image format')
  })

  it('reports a timeout', () => {
    const error = new AxiosError('timeout', 'ECONNABORTED')
    expect(describeError(error)).toMatch(/timed out/i)
  })

  it('reports an unreachable API', () => {
    const error = new AxiosError('Network Error', 'ERR_NETWORK')
    expect(describeError(error)).toMatch(/could not be reached/i)
  })

  it('falls back to the status code', () => {
    const error = axiosErrorWith({ unexpected: true }, 503)
    expect(describeError(error)).toContain('503')
  })

  it('handles plain errors', () => {
    expect(describeError(new Error('boom'))).toBe('boom')
    expect(describeError('nope')).toBe('An unexpected error occurred.')
  })
})

describe('errorCode', () => {
  it('extracts the structured code', () => {
    const error = axiosErrorWith({
      status: 'error',
      error: { code: 'ML_SERVICE_UNAVAILABLE', message: 'x', details: {} },
    })
    expect(errorCode(error)).toBe('ML_SERVICE_UNAVAILABLE')
  })

  it('returns undefined for non axios errors', () => {
    expect(errorCode(new Error('boom'))).toBeUndefined()
  })
})

describe('absoluteUrl', () => {
  it('leaves absolute URLs untouched', () => {
    expect(absoluteUrl('https://example.org/x.png')).toBe('https://example.org/x.png')
  })

  it('prefixes relative paths with the API root', () => {
    expect(absoluteUrl('/api/v1/images/abc/download')).toMatch(/\/api\/v1\/images\/abc\/download$/)
  })
})
