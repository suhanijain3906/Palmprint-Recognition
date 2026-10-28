// lucide types removed
import { Link } from 'react-router-dom'

interface StatCardProps {
  label: string
  value: string | number
  icon: any
  to: string
}

/** A dashboard counter that links to the relevant tool. */
export function StatCard({ label, value, icon: Icon, to }: StatCardProps) {
  return (
    <Link to={to} className="card p-5 transition hover:border-primary-300">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-600">{label}</span>
        <Icon className="h-4 w-4 text-primary-600" aria-hidden="true" />
      </div>
      <p className="mt-2 text-2xl font-semibold capitalize text-navy-900">{value}</p>
    </Link>
  )
}

export default StatCard
