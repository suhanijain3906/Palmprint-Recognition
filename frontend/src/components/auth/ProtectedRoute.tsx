import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { LoadingState } from '../common/StateViews'
import { useAuth } from '../../app/AuthProvider'

/** Redirects unauthenticated visitors to the login page when auth is enabled. */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { loading, enabled, user } = useAuth()
  const location = useLocation()

  if (loading) {
    return <LoadingState label="Checking your session..." />
  }
  if (enabled && !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}

export default ProtectedRoute
