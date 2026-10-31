import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './i18n'
import './index.css'
import Login from './pages/Login'
import Queue from './pages/Queue'
import ApplicationDetail from './pages/ApplicationDetail'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Queue /></PrivateRoute>} />
        <Route path="/applications/:id" element={<PrivateRoute><ApplicationDetail /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
