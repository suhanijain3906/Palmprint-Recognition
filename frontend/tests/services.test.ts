import { describe, expect, it, vi, beforeEach } from 'vitest'
import { imageService } from '../src/services/imageService'
import { processingService } from '../src/services/processingService'
import { recognitionService } from '../src/services/recognitionService'
import { experimentService } from '../src/services/experimentService'
import { reportService } from '../src/services/reportService'
import { datasetService } from '../src/services/datasetService'
import apiClient from '../src/services/apiClient'

vi.mock('../src/services/apiClient', async () => {
  const actual = await vi.importActual<typeof import('../src/services/apiClient')>(
    '../src/services/apiClient',
  )
  return {
    ...actual,
    default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  }
})

const mocked = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

describe('service layer targets the documented API paths', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocked.get.mockResolvedValue({ data: {} })
    mocked.post.mockResolvedValue({ data: {} })
    mocked.patch.mockResolvedValue({ data: {} })
    mocked.delete.mockResolvedValue({ data: {} })
  })

  it('lists images', async () => {
    await imageService.list({ page_size: 5 })
    expect(mocked.get).toHaveBeenCalledWith('/images', { params: { page_size: 5 } })
  })

  it('uploads an image as multipart form data', async () => {
    const file = new File(['x'], 'palm.png', { type: 'image/png' })
    await imageService.upload(file, { label: 'left', subject_id: 'S-1' })
    const [path, form, config] = mocked.post.mock.calls[0]
    expect(path).toBe('/images/upload')
    expect(form).toBeInstanceOf(FormData)
    expect((form as FormData).get('label')).toBe('left')
    expect((form as FormData).get('subject_id')).toBe('S-1')
    expect(config).toHaveProperty('onUploadProgress')
  })

  it('uses the documented processing endpoints', async () => {
    await processingService.extractRoi({ image_id: 'i1' })
    expect(mocked.post.mock.calls[0][0]).toBe('/processing/roi')

    await processingService.enhance({ image_id: 'i1', algorithm: 'clahe' })
    expect(mocked.post.mock.calls[1][0]).toBe('/processing/enhancement')

    await processingService.quality({ image_id: 'i1' })
    expect(mocked.post.mock.calls[2][0]).toBe('/processing/quality')

    await processingService.features({ image_id: 'i1' })
    expect(mocked.post.mock.calls[3][0]).toBe('/processing/features')

    await processingService.landmarks({ image_id: 'i1' })
    expect(mocked.post.mock.calls[4][0]).toBe('/processing/landmarks')
  })

  it('uses the documented recognition and comparison endpoints', async () => {
    await recognitionService.compare({ image_a_id: 'a', image_b_id: 'b' })
    expect(mocked.post.mock.calls[0][0]).toBe('/recognition/compare')

    await recognitionService.imageCompare({ image_a_id: 'a', image_b_id: 'b' })
    expect(mocked.post.mock.calls[1][0]).toBe('/comparison')
  })

  it('uses the documented experiment and report endpoints', async () => {
    await experimentService.create({
      name: 'run',
      operation: 'enhancement',
      algorithm: 'clahe',
      parameters: {},
      image_ids: [],
    })
    expect(mocked.post.mock.calls[0][0]).toBe('/experiments')

    await reportService.create({
      title: 'r',
      report_type: 'processing',
      job_ids: [],
      include_images: false,
    })
    expect(mocked.post.mock.calls[1][0]).toBe('/reports')
  })

  it('lists datasets', async () => {
    await datasetService.list()
    expect(mocked.get).toHaveBeenCalledWith('/datasets')
  })
})
