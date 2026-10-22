import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { RecognitionPage } from '../src/pages/RecognitionPage'
import { NotificationProvider } from '../src/components/common/Notification'

const listMock = vi.fn()
const compareMock = vi.fn()

vi.mock('../src/services/imageService', () => ({
  default: { list: (...args: unknown[]) => listMock(...args) },
}))

vi.mock('../src/services/recognitionService', () => ({
  default: { compare: (...args: unknown[]) => compareMock(...args) },
}))

vi.mock('../src/services/apiClient', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  describeError: (error: unknown) =>
    error instanceof Error ? error.message : 'An unexpected error occurred.',
  errorCode: () => undefined,
  absoluteUrl: (path: string) => path,
}))

const IMAGE = {
  id: 'img-1',
  original_filename: 'left.png',
  media_type: 'image/png',
  size_bytes: 1024,
  width: 320,
  height: 320,
  checksum_sha256: 'a'.repeat(64),
  created_at: '2026-01-01T00:00:00Z',
  download_url: '/api/v1/images/img-1/download',
}

const IMAGE_B = {
  ...IMAGE,
  id: 'img-2',
  original_filename: 'right.png',
  download_url: '/api/v1/images/img-2/download',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <NotificationProvider>
        <RecognitionPage />
      </NotificationProvider>
    </MemoryRouter>,
  )
}

/** Both pickers list every image, so the selector has to be scoped to one card. */
function cardFor(title: string): HTMLElement {
  const heading = screen.getByRole('heading', { name: title })
  const section = heading.closest('section')
  if (!section) throw new Error(`No card found for "${title}"`)
  return section
}

describe('RecognitionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listMock.mockResolvedValue({
      items: [IMAGE, IMAGE_B],
      meta: { page: 1, page_size: 24, total: 2, total_pages: 1 },
    })
    compareMock.mockResolvedValue({
      status: 'success',
      job_id: 'job-1',
      similarity_score: 0.42,
      score_kind: 'matching_statistics',
      is_trained_model: false,
      is_calibrated_probability: false,
      trained_model_available: false,
      matcher: 'bf_lk',
      matcher_version: '1.0.0',
      details: { matched_keypoints: 12 },
      artifacts: [],
      warnings: [],
      limitations: ['Not a calibrated probability.'],
      processing_time_ms: 12.5,
    })
  })

  it('states that the matcher is not a trained identity model', async () => {
    renderPage()
    expect(screen.getByText(/uncalibrated matcher, not a trained biometric identity model/i)).toBeInTheDocument()
    await waitFor(() =>
      expect(within(cardFor('Image A')).getAllByRole('button').length).toBeGreaterThan(0),
    )
  })

  it('warns that the score is not a calibrated probability', async () => {
    renderPage()
    expect(screen.getByText(/calibrated probability/i)).toBeInTheDocument()
    expect(screen.getByText(/must not be interpreted as identity confidence/i)).toBeInTheDocument()
  })

  it('runs the comparison and reports the uncalibrated result', async () => {
    renderPage()
    await waitFor(() =>
      expect(within(cardFor('Image A')).getAllByRole('button').length).toBeGreaterThan(0),
    )

    await userEvent.click(within(cardFor('Image A')).getByRole('button', { name: /left\.png/i }))
    await userEvent.click(within(cardFor('Image B')).getByRole('button', { name: /right\.png/i }))

    await userEvent.click(screen.getByRole('button', { name: /run experimental comparison/i }))

    await waitFor(() => expect(compareMock).toHaveBeenCalled())
    expect(compareMock.mock.calls[0][0]).toMatchObject({
      image_a_id: 'img-1',
      image_b_id: 'img-2',
    })
  })

  it('refuses to compare an image with itself', async () => {
    renderPage()
    await waitFor(() =>
      expect(within(cardFor('Image A')).getAllByRole('button').length).toBeGreaterThan(0),
    )

    await userEvent.click(within(cardFor('Image A')).getByRole('button', { name: /left\.png/i }))
    await userEvent.click(within(cardFor('Image B')).getByRole('button', { name: /left\.png/i }))

    await userEvent.click(screen.getByRole('button', { name: /run experimental comparison/i }))

    await waitFor(() => {
      expect(screen.getByText(/select two different images/i)).toBeInTheDocument()
    })
    expect(compareMock).not.toHaveBeenCalled()
  })
})
