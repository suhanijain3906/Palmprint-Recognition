import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { Card } from '../components/common/Card'
import { useNotify } from '../components/common/Notification'
import { LoadingState } from '../components/common/StateViews'
import { useAuth } from '../app/AuthProvider'
import { describeError } from '../services/apiClient'

type Mode = 'login' | 'register'

function Field({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export function LoginPage() {
  const { loading, enabled, registrationEnabled, user, login, register } = useAuth()
  const { notify } = useNotify()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const from = (location.state as { from?: string } | null)?.from ?? '/'

  if (loading) {
    return <LoadingState label="Checking authentication mode..." />
  }

  if (user) {
    return <Navigate to={from} replace />
  }

  if (!enabled) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <Card className="w-full max-w-lg" title="Academic demo mode">
          <p className="text-sm text-slate-600">
            Authentication is disabled for this deployment. Every visitor shares the same
            demo account, so do not expose this instance to the public internet. Enable
            <code className="mx-1 rounded bg-slate-100 px-1 py-0.5">AUTH_ENABLED=true</code>
            to require accounts.
          </p>
          <Link to="/" className="btn-primary mt-4 inline-flex">
            Continue in demo mode
          </Link>
        </Card>
      </div>
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (mode === 'login') {
        await login({ email, password })
      } else {
        await register({ email, display_name: displayName, password })
      }
      notify(mode === 'login' ? 'Signed in.' : 'Account created.', 'success')
      navigate(from, { replace: true })
    } catch (cause) {
      setError(describeError(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-navy-900">
            <ShieldCheck className="h-5 w-5 text-primary-400" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-navy-900">Palmprint Research Platform</h1>
            <p className="text-sm text-slate-500">
              {mode === 'login' ? 'Sign in to your account' : 'Create a research account'}
            </p>
          </div>
        </div>

        <Card>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <Field label="Email">
              <input
                className="input"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </Field>

            {mode === 'register' && (
              <Field label="Display name">
                <input
                  className="input"
                  type="text"
                  autoComplete="name"
                  required
                  maxLength={120}
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                />
              </Field>
            )}

            <Field label="Password">
              <input
                className="input"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                minLength={mode === 'register' ? 8 : 1}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </Field>

            {error && (
              <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            )}

            <button type="submit" className="btn-primary w-full" disabled={busy}>
              {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          {registrationEnabled && (
            <button
              type="button"
              className="mt-4 text-sm font-medium text-primary-700 hover:underline"
              onClick={() => {
                setMode(mode === 'login' ? 'register' : 'login')
                setError(null)
              }}
            >
              {mode === 'login'
                ? 'No account yet? Create one'
                : 'Already have an account? Sign in'}
            </button>
          )}
        </Card>
      </div>
    </div>
  )
}

export default LoginPage
