import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'

export function NotFoundPage() {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center justify-center py-24 text-center">
      <Compass className="mb-4 h-10 w-10 text-primary-600" />
      <h1 className="text-3xl font-semibold text-navy-900">Page not found</h1>
      <p className="mt-2 text-sm text-slate-600">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link to="/" className="btn-primary mt-6">
        Back to home
      </Link>
    </div>
  )
}

export default NotFoundPage
