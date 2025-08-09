import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { vi, afterEach } from 'vitest'
import React from 'react'

// Make React available globally
global.React = React

// Mock Next.js router
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  pathname: '/',
  query: {},
  asPath: '/',
  route: '/',
}

vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock fetch globally
global.fetch = vi.fn()

// Mock DOM methods
Object.defineProperty(Element.prototype, 'scrollIntoView', {
  value: vi.fn(),
  writable: true,
})

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  error: vi.fn(),
  warn: vi.fn(),
  log: vi.fn(),
}

// Clean up after each test
afterEach(async () => {
  // Clean up React Testing Library
  cleanup()

  vi.clearAllTimers()
  vi.clearAllMocks()
  // Restore real timers after each test
  vi.useRealTimers()

  // Wait for any pending promises to resolve
  await new Promise(resolve => setTimeout(resolve, 0))

  // Force garbage collection of any remaining async operations
  if (global.gc) {
    global.gc()
  }
})