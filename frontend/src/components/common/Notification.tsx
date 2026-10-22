import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle2, Info, X, XCircle } from 'lucide-react'

export type NotificationKind = 'success' | 'error' | 'info'

interface Notification {
  id: number
  kind: NotificationKind
  message: string
}

interface NotificationContextValue {
  notify: (message: string, kind?: NotificationKind) => void
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

let counter = 0

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Notification[]>([])

  const dismiss = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id))
  }, [])

  const notify = useCallback(
    (message: string, kind: NotificationKind = 'info') => {
      const id = ++counter
      setItems((prev) => [...prev, { id, kind, message }])
      window.setTimeout(() => dismiss(id), 6000)
    },
    [dismiss],
  )

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {items.map((item) => {
          const Icon =
            item.kind === 'success' ? CheckCircle2 : item.kind === 'error' ? XCircle : Info
          const colour =
            item.kind === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : item.kind === 'error'
                ? 'border-red-200 bg-red-50 text-red-800'
                : 'border-slate-200 bg-white text-slate-800'
          return (
            <div
              key={item.id}
              role="status"
              className={`flex items-start gap-2 rounded-lg border p-3 shadow-sm ${colour}`}
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0" />
              <p className="flex-1 text-sm">{item.message}</p>
              <button
                type="button"
                onClick={() => dismiss(item.id)}
                aria-label="Dismiss notification"
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )
        })}
      </div>
    </NotificationContext.Provider>
  )
}

export function useNotify(): NotificationContextValue {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotify must be used inside a NotificationProvider')
  }
  return context
}
