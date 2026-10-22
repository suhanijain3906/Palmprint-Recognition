import type { ReactNode } from 'react'
import { NotificationProvider } from '../components/common/Notification'
import { AuthProvider } from './AuthProvider'

/**
 * Global providers of the application.
 *
 * Kept in a dedicated module so that tests and the production entry point
 * compose exactly the same provider tree.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <NotificationProvider>
      <AuthProvider>{children}</AuthProvider>
    </NotificationProvider>
  )
}

export default AppProviders
