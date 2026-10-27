import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { LoadingState } from '../components/common/StateViews'

const LoginPage = lazy(() => import('../pages/LoginPage'))
const HomePage = lazy(() => import('../pages/HomePage'))
const DashboardPage = lazy(() => import('../pages/DashboardPage'))
const UploadPage = lazy(() => import('../pages/UploadPage'))
const ProcessingPage = lazy(() => import('../pages/ProcessingPage'))
const QualityPage = lazy(() => import('../pages/QualityPage'))
const RecognitionPage = lazy(() => import('../pages/RecognitionPage'))
const ComparisonPage = lazy(() => import('../pages/ComparisonPage'))
const LandmarksPage = lazy(() => import('../pages/LandmarksPage'))
const DatasetsPage = lazy(() => import('../pages/DatasetsPage'))
const ExperimentsPage = lazy(() => import('../pages/ExperimentsPage'))
const ReportsPage = lazy(() => import('../pages/ReportsPage'))
const AboutPage = lazy(() => import('../pages/AboutPage'))
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'))

function withSuspense(element: ReactNode) {
  return <Suspense fallback={<LoadingState label="Loading page..." />}>{element}</Suspense>
}

export const router = createBrowserRouter([
  { path: '/login', element: withSuspense(<LoginPage />) },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: withSuspense(<HomePage />) },
      { path: 'dashboard', element: withSuspense(<DashboardPage />) },
      { path: 'upload', element: withSuspense(<UploadPage />) },
      { path: 'upload-image', element: withSuspense(<UploadPage />) },
      { path: 'palmprint-upload', element: withSuspense(<UploadPage />) },
      { path: 'processing', element: withSuspense(<ProcessingPage />) },
      { path: 'quality', element: withSuspense(<QualityPage />) },
      { path: 'recognition', element: withSuspense(<RecognitionPage />) },
      { path: 'comparison', element: withSuspense(<ComparisonPage />) },
      { path: 'landmarks', element: withSuspense(<LandmarksPage />) },
      { path: 'datasets', element: withSuspense(<DatasetsPage />) },
      { path: 'experiments', element: withSuspense(<ExperimentsPage />) },
      { path: 'reports', element: withSuspense(<ReportsPage />) },
      { path: 'about', element: withSuspense(<AboutPage />) },
      { path: '*', element: withSuspense(<NotFoundPage />) },
    ],
  },
])
