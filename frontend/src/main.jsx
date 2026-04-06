import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import AvatarSelect from './pages/AvatarSelect'
import Spaces from './pages/Spaces'
import Arena from './pages/Arena'
import './index.css'

/**
 * WHY React Router?
 * The app has 3 pages: Login, Space List, and Arena (the actual 2D room).
 * React Router handles navigation without full page reloads.
 *
 * WHY client-side routing?
 * In a single-page app, the browser never reloads. React Router swaps
 * components based on the URL. This feels faster and maintains WebSocket
 * connections when navigating between views.
 */

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/avatar" element={<AvatarSelect />} />
        <Route path="/spaces" element={<Spaces />} />
        <Route path="/arena/:spaceId" element={<Arena />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
