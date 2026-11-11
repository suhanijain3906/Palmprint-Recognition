import { useRouteError, isRouteErrorResponse } from 'react-router-dom'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'

export function RouteErrorBoundary() {
  const error = useRouteError()

  let title = 'Something went wrong'
  let message = 'An unexpected error occurred while loading this page.'
  let isChunkError = false

  if (isRouteErrorResponse(error)) {
    title = `${error.status} ${error.statusText}`
    message = error.data?.message || 'The requested page could not be displayed.'
  } else if (error instanceof Error) {
    const errorMsg = error.message.toLowerCase()
    if (
      errorMsg.includes('failed to fetch dynamically imported module') ||
      errorMsg.includes('error loading dynamically imported module') ||
      errorMsg.includes('dynamically imported module')
    ) {
      isChunkError = true
      title = 'Application Updated'
      message =
        'A new version of the platform has been deployed. Please reload the page to update your session with the latest modules.'
    } else {
      message = error.message
    }
  }

  const handleReload = () => {
    window.location.reload()
  }

  const handleGoHome = () => {
    window.location.href = '/'
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-600">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="mt-2 text-sm text-slate-600">{message}</p>

        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <button
            type="button"
            onClick={handleReload}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <RefreshCw className="h-4 w-4" />
            Reload Page
          </button>
          {!isChunkError && (
            <button
              type="button"
              onClick={handleGoHome}
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <Home className="h-4 w-4" />
              Go to Home
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
