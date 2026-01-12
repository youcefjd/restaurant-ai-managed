import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

/**
 * Main entry point for the React application
 * 
 * Sets up:
 * - React 18 concurrent rendering with createRoot
 * - BrowserRouter for client-side routing
 * - StrictMode for development warnings and checks
 */

// Get the root element from the DOM
const rootElement = document.getElementById('root')

// Ensure the root element exists before rendering
if (!rootElement) {
  throw new Error(
    'Failed to find the root element. Make sure there is a <div id="root"></div> in your index.html'
  )
}

// Create the React root and render the application
const root = ReactDOM.createRoot(rootElement)

root.render(
  <React.StrictMode>
    {/* 
      BrowserRouter provides routing context for the entire application
      Uses the HTML5 history API for clean URLs without hash fragments
    */}
    <BrowserRouter
      future={{
        // Enable future flags for React Router v7 compatibility
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <App />
    </BrowserRouter>
  </React.StrictMode>
)

// Enable hot module replacement for development
if (import.meta.hot) {
  import.meta.hot.accept()
}