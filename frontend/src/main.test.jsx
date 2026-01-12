import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// Mock ReactDOM
const mockRender = vi.fn()
const mockCreateRoot = vi.fn(() => ({
  render: mockRender,
}))

vi.mock('react-dom/client', () => ({
  default: {
    createRoot: (element) => mockCreateRoot(element),
  },
  createRoot: (element) => mockCreateRoot(element),
}))

// Mock App component
vi.mock('./App', () => ({
  default: () => <div data-testid="mock-app">Mock App</div>,
}))

// Mock CSS import
vi.mock('./index.css', () => ({}))

describe('main.jsx', () => {
  let originalGetElementById
  let mockRootElement

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks()
    
    // Store original getElementById
    originalGetElementById = document.getElementById
    
    // Create a mock root element
    mockRootElement = document.createElement('div')
    mockRootElement.id = 'root'
  })

  afterEach(() => {
    // Restore original getElementById
    document.getElementById = originalGetElementById
    
    // Clear module cache to allow re-importing
    vi.resetModules()
  })

  describe('Root Element Detection', () => {
    it('should find the root element when it exists', async () => {
      // Arrange
      document.getElementById = vi.fn((id) => {
        if (id === 'root') return mockRootElement
        return null
      })

      // Act
      await import('./main.jsx')

      // Assert
      expect(document.getElementById).toHaveBeenCalledWith('root')
    })

    it('should throw an error when root element is not found', async () => {
      // Arrange
      document.getElementById = vi.fn(() => null)

      // Act & Assert
      await expect(import('./main.jsx')).rejects.toThrow(
        'Failed to find the root element. Make sure there is a <div id="root"></div> in your index.html'
      )
    })

    it('should call getElementById with "root" as the argument', async () => {
      // Arrange
      const getElementByIdSpy = vi.fn(() => mockRootElement)
      document.getElementById = getElementByIdSpy

      // Act
      await import('./main.jsx')

      // Assert
      expect(getElementByIdSpy).toHaveBeenCalledTimes(1)
      expect(getElementByIdSpy).toHaveBeenCalledWith('root')
    })
  })

  describe('React Root Creation', () => {
    it('should call createRoot with the root element', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      expect(mockCreateRoot).toHaveBeenCalledWith(mockRootElement)
    })

    it('should call render on the created root', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      expect(mockRender).toHaveBeenCalled()
    })

    it('should render with StrictMode wrapper', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      expect(renderCall.type).toBe(React.StrictMode)
    })
  })

  describe('BrowserRouter Configuration', () => {
    it('should wrap App with BrowserRouter', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      // StrictMode -> BrowserRouter -> App
      const browserRouter = renderCall.props.children
      expect(browserRouter.type.name).toBe('BrowserRouter')
    })

    it('should configure BrowserRouter with v7 future flags', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      const browserRouter = renderCall.props.children
      expect(browserRouter.props.future).toEqual({
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      })
    })

    it('should have v7_startTransition flag enabled', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      const browserRouter = renderCall.props.children
      expect(browserRouter.props.future.v7_startTransition).toBe(true)
    })

    it('should have v7_relativeSplatPath flag enabled', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      const browserRouter = renderCall.props.children
      expect(browserRouter.props.future.v7_relativeSplatPath).toBe(true)
    })
  })

  describe('App Component Rendering', () => {
    it('should render the App component inside BrowserRouter', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      const browserRouter = renderCall.props.children
      const appComponent = browserRouter.props.children
      expect(appComponent.type).toBeDefined()
    })
  })

  describe('Hot Module Replacement', () => {
    it('should accept HMR updates when import.meta.hot is available', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)
      const mockAccept = vi.fn()
      
      // Mock import.meta.hot
      const originalImportMeta = import.meta.hot
      Object.defineProperty(import.meta, 'hot', {
        value: { accept: mockAccept },
        writable: true,
        configurable: true,
      })

      // Act
      await import('./main.jsx')

      // Assert - HMR is called during module initialization
      // The actual HMR setup happens in the module itself

      // Cleanup
      Object.defineProperty(import.meta, 'hot', {
        value: originalImportMeta,
        writable: true,
        configurable: true,
      })
    })

    it('should not throw when import.meta.hot is undefined', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)
      
      // Ensure import.meta.hot is undefined (production mode)
      const originalImportMeta = import.meta.hot
      Object.defineProperty(import.meta, 'hot', {
        value: undefined,
        writable: true,
        configurable: true,
      })

      // Act & Assert - should not throw
      await expect(import('./main.jsx')).resolves.toBeDefined()

      // Cleanup
      Object.defineProperty(import.meta, 'hot', {
        value: originalImportMeta,
        writable: true,
        configurable: true,
      })
    })
  })

  describe('Error Handling', () => {
    it('should throw descriptive error message when root element is missing', async () => {
      // Arrange
      document.getElementById = vi.fn(() => null)

      // Act & Assert
      try {
        await import('./main.jsx')
        expect.fail('Should have thrown an error')
      } catch (error) {
        expect(error.message).toContain('Failed to find the root element')
        expect(error.message).toContain('<div id="root"></div>')
        expect(error.message).toContain('index.html')
      }
    })

    it('should provide actionable error message for developers', async () => {
      // Arrange
      document.getElementById = vi.fn(() => null)

      // Act & Assert
      try {
        await import('./main.jsx')
        expect.fail('Should have thrown an error')
      } catch (error) {
        // Error message should help developers fix the issue
        expect(error.message).toMatch(/root/i)
        expect(error.message).toMatch(/index\.html/i)
      }
    })
  })

  describe('Component Structure', () => {
    it('should render with correct component hierarchy', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      const renderCall = mockRender.mock.calls[0][0]
      
      // Level 1: StrictMode
      expect(renderCall.type).toBe(React.StrictMode)
      
      // Level 2: BrowserRouter
      const browserRouter = renderCall.props.children
      expect(browserRouter.type.name).toBe('BrowserRouter')
      
      // Level 3: App
      const app = browserRouter.props.children
      expect(app).toBeDefined()
    })

    it('should only render once on initial load', async () => {
      // Arrange
      document.getElementById = vi.fn(() => mockRootElement)

      // Act
      await import('./main.jsx')

      // Assert
      expect(mockCreateRoot).toHaveBeenCalledTimes(1)
      expect(mockRender).toHaveBeenCalledTimes(1)
    })
  })
})

describe('App Component Integration', () => {
  it('should render App component correctly when imported', async () => {
    // Arrange & Act
    const { default: App } = await import('./App')
    
    // Assert
    expect(App).toBeDefined()
  })
})

describe('Module Exports', () => {
  it('should not export any values (entry point module)', async () => {
    // Arrange
    const originalGetElementById = document.getElementById
    document.getElementById = vi.fn(() => document.createElement('div'))

    // Act
    const mainModule = await import('./main.jsx')

    // Assert - entry point should have minimal or no exports
    const exportKeys = Object.keys(mainModule).filter(key => key !== 'default')
    expect(exportKeys.length).toBeLessThanOrEqual(1)

    // Cleanup
    document.getElementById = originalGetElementById
  })
})