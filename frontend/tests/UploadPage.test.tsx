import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { UploadPage } from '../src/pages/UploadPage'
import { validateFile } from '../src/components/upload/ImageDropzone'
import { NotificationProvider } from '../src/components/common/Notification'

vi.mock('../src/services/imageService', () => ({
  default: {
    upload: vi.fn(),
    list: vi.fn(),
  },
}))

vi.mock('../src/services/apiClient', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  describeError: (error: unknown) =>
    error instanceof Error ? error.message : 'An unexpected error occurred.',
  errorCode: () => undefined,
  absoluteUrl: (path: string) => path,
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <NotificationProvider>
        <UploadPage />
      </NotificationProvider>
    </MemoryRouter>,
  )
}

describe('validateFile', () => {
  it('rejects an unsupported mime type', () => {
    const file = new File(['x'], 'notes.txt', { type: 'text/plain' })
    expect(validateFile(file)).toContain('Unsupported format')
  })

  it('rejects an empty file', () => {
    const file = new File([], 'empty.png', { type: 'image/png' })
    expect(validateFile(file)).toBe('The selected file is empty.')
  })

  it('rejects a file above the size limit', () => {
    const file = new File(['x'], 'big.png', { type: 'image/png' })
    Object.defineProperty(file, 'size', { value: 13 * 1024 * 1024 })
    expect(validateFile(file)).toContain('too large')
  })

  it('accepts a supported png', () => {
    const file = new File(['x'], 'palm.png', { type: 'image/png' })
    expect(validateFile(file)).toBeNull()
  })
})

describe('UploadPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page heading and keeps the upload button disabled initially', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /upload a palmprint image/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /upload image/i })).toBeDisabled()
  })

  it('explains that validation is content based', () => {
    renderPage()
    expect(screen.getByText(/validated against its actual content/i)).toBeInTheDocument()
  })
})
