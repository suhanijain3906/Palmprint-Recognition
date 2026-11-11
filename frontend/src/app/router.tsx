import { lazy, Suspense, type ComponentType, type ReactNode } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { LoadingState } from '../components/common/StateViews'
import { RouteErrorBoundary } from '../components/common/RouteErrorBoundary'

function lazyWithRetry<T extends ComponentType<any>>(
  factory: () => Promise<{ default: T }>,
) {
  return lazy(async () => {
    try {
      return await factory()
    } catch (err: any) {
      const msg = (err?.message || '').toLowerCase()
      if (
        msg.includes('failed to fetch dynamically imported module') ||
        msg.includes('error loading dynamically imported module') ||
        msg.includes('dynamically imported module')
      ) {
        const lastReload = parseInt(sessionStorage.getItem('last_chunk_reload') || '0', 10)
        const now = Date.now()
        if (now - lastReload > 8000) {
          sessionStorage.setItem('last_chunk_reload', String(now))
          window.location.reload()
          return new Promise(() => {}) // Halt rendering while reloading
        }
      }
      throw err
    }
  })
}

const LoginPage = lazyWithRetry(() => import('../pages/LoginPage'))
const HomePage = lazyWithRetry(() => import('../pages/HomePage'))
const DashboardPage = lazyWithRetry(() => import('../pages/DashboardPage'))
const UploadPage = lazyWithRetry(() => import('../pages/UploadPage'))
const ProcessingPage = lazyWithRetry(() => import('../pages/ProcessingPage'))
const QualityPage = lazyWithRetry(() => import('../pages/QualityPage'))
const RecognitionPage = lazyWithRetry(() => import('../pages/RecognitionPage'))
const ComparisonPage = lazyWithRetry(() => import('../pages/ComparisonPage'))
const LandmarksPage = lazyWithRetry(() => import('../pages/LandmarksPage'))
const DatasetsPage = lazyWithRetry(() => import('../pages/DatasetsPage'))
const ExperimentsPage = lazyWithRetry(() => import('../pages/ExperimentsPage'))
const ReportsPage = lazyWithRetry(() => import('../pages/ReportsPage'))
const AboutPage = lazyWithRetry(() => import('../pages/AboutPage'))
const AnalysisPage = lazyWithRetry(() => import('../pages/AnalysisPage'))
const NotFoundPage = lazyWithRetry(() => import('../pages/NotFoundPage'))

function withSuspense(element: ReactNode) {
  return <Suspense fallback={<LoadingState label="Loading page..." />}>{element}</Suspense>
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: withSuspense(<LoginPage />),
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/analysis',
    element: withSuspense(<AnalysisPage />),
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/analyze',
    element: withSuspense(<AnalysisPage />),
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/palmprint-analysis',
    element: withSuspense(<AnalysisPage />),
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    errorElement: <RouteErrorBoundary />,
    children: [
      { index: true, element: withSuspense(<HomePage />), errorElement: <RouteErrorBoundary /> },
      { path: 'dashboard', element: withSuspense(<DashboardPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'upload', element: withSuspense(<UploadPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'upload-image', element: withSuspense(<UploadPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'palmprint-upload', element: withSuspense(<UploadPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'processing', element: withSuspense(<ProcessingPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'quality', element: withSuspense(<QualityPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'recognition', element: withSuspense(<RecognitionPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'comparison', element: withSuspense(<ComparisonPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'landmarks', element: withSuspense(<LandmarksPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'datasets', element: withSuspense(<DatasetsPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'experiments', element: withSuspense(<ExperimentsPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'reports', element: withSuspense(<ReportsPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'about', element: withSuspense(<AboutPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'analysis', element: withSuspense(<AnalysisPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'analyze', element: withSuspense(<AnalysisPage />), errorElement: <RouteErrorBoundary /> },
      { path: 'palmprint-analysis', element: withSuspense(<AnalysisPage />), errorElement: <RouteErrorBoundary /> },
      { path: '*', element: withSuspense(<NotFoundPage />), errorElement: <RouteErrorBoundary /> },
    ],
  },
])
