import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

// Mock matchMedia if not defined in jsdom
if (typeof window !== 'undefined' && !window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

describe('App Component', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('renders login screen when user is not authenticated', async () => {
    render(<App />)

    // Should redirect unauthenticated users to login and show Padho Abhi title
    await waitFor(() => {
      expect(screen.getByText('Padho Abhi')).toBeInTheDocument()
    })

    expect(screen.getByText('AI-Powered Smart Study Platform')).toBeInTheDocument()
    const loginButtons = screen.getAllByRole('button', { name: /login/i })
    expect(loginButtons.length).toBeGreaterThan(0)
    expect(loginButtons[0]).toBeInTheDocument()
  })

  it('renders main application layout when user is authenticated', async () => {
    const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' }
    localStorage.setItem('token', 'fake-token')
    localStorage.setItem('user', JSON.stringify(mockUser))

    // Mock fetch API response for initial profile / subjects call
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/auth/profile/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 1, daily_usage: 0, has_api_key: true }),
        })
      }
      if (url.includes('/api/subjects/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    })

    render(<App />)

    // Should render main dashboard welcome screen for authenticated user without subjects
    await waitFor(() => {
      expect(screen.getByText(/Welcome to Padho Abhi!/i)).toBeInTheDocument()
    })

    expect(screen.getByText('testuser')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start Learning Now/i })).toBeInTheDocument()
  })
})
