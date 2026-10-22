import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { Layout } from '../src/components/layout/Layout'
import { HomePage } from '../src/pages/HomePage'
import { NotFoundPage } from '../src/pages/NotFoundPage'

vi.mock('../src/services/healthService', () => ({
  default: { check: vi.fn().mockResolvedValue({ status: 'ok' }) },
}))

describe('Layout navigation', () => {
  it('renders every primary navigation entry', () => {
    render(
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    const nav = screen.getByRole('navigation')
    const labels = Array.from(nav.querySelectorAll('a')).map((link) => link.textContent?.trim())
    expect(labels).toEqual([
      'Home',
      'Dashboard',
      'Upload',
      'Processing',
      'Quality',
      'Recognition',
      'Comparison',
      'Landmarks',
      'Datasets',
      'Experiments',
      'Reports',
      'About',
    ])
  })

  it('navigates to another route when a nav link is activated', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="about" element={<div>About page content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('link', { name: 'About' }))
    await waitFor(() => {
      expect(screen.getByText('About page content')).toBeInTheDocument()
    })
  })
})

describe('NotFoundPage', () => {
  it('shows a helpful message and a link back home', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    )
    expect(screen.getByRole('heading', { name: /page not found/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to home/i })).toHaveAttribute('href', '/')
  })
})
