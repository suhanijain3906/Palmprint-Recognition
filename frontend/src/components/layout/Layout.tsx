import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  Home,
  LayoutDashboard,
  Upload,
  Image,
  BarChart3,
  GitCompare,
  Target,
  MapPin,
  Database,
  FlaskConical,
  FileText,
  Info,
  LogOut,
} from 'lucide-react'
import { useAuth } from '../../app/AuthProvider'

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload', icon: Upload },
  { path: '/processing', label: 'Processing', icon: Image },
  { path: '/quality', label: 'Quality', icon: BarChart3 },
  { path: '/recognition', label: 'Recognition', icon: Target },
  { path: '/comparison', label: 'Comparison', icon: GitCompare },
  { path: '/landmarks', label: 'Landmarks', icon: MapPin },
  { path: '/datasets', label: 'Datasets', icon: Database },
  { path: '/experiments', label: 'Experiments', icon: FlaskConical },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/about', label: 'About', icon: Info },
]

export function Layout() {
  const { enabled, user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-navy-900 rounded-lg flex items-center justify-center">
                <span className="text-primary-400 font-bold text-sm">PP</span>
              </div>
              <h1 className="text-xl font-semibold text-navy-900">Palmprint Research Platform</h1>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              {user && <span className="hidden sm:inline">{user.display_name}</span>}
              {enabled && user && (
                <button
                  type="button"
                  className="btn-ghost flex items-center gap-1"
                  onClick={handleLogout}
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              )}
              {!enabled && <span>Experimental Research Platform</span>}
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex">
        <aside className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-73px)] sticky top-[73px]">
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-slate-700 hover:bg-slate-100'
                    }`
                  }
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>
        </aside>
        
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
