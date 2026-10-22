import type { ReactNode } from 'react'
import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-slate-500">
      <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-red-200 bg-red-50 py-10 px-6 text-center">
      <AlertTriangle className="h-6 w-6 text-red-500" />
      <p className="text-sm text-red-700">{message}</p>
      {action}
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 py-12 px-6 text-center">
      <Inbox className="h-6 w-6 text-slate-400" />
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="max-w-md text-xs text-slate-500">{description}</p>}
      {action}
    </div>
  )
}

export default { LoadingState, ErrorState, EmptyState }
