import { ShieldCheck, Microscope, Layers, AlertTriangle } from 'lucide-react'
import { PageHeader } from '../components/common/PageHeader'
import { Card } from '../components/common/Card'

const PRINCIPLES = [
  {
    icon: ShieldCheck,
    title: 'No fabricated results',
    body: 'Every metric shown in the interface comes from the ML service at request time. Nothing is mocked, hard-coded or copied from publications. Empty states are honest about missing data.',
  },
  {
    icon: Layers,
    title: 'Strict separation of concerns',
    body: 'The frontend never talks to the ML service directly. The backend stores images and orchestrates requests; the ML service performs all computer-vision processing. No image processing happens in the backend.',
  },
  {
    icon: Microscope,
    title: 'Research-grade honesty',
    body: 'Recognition is an uncalibrated classical matcher, not a trained identity model. Landmark detection returns feature points, not anatomical landmarks. Combined quality scores are experimental heuristics.',
  },
  {
    icon: AlertTriangle,
    title: 'Biometric data responsibility',
    body: 'No biometric dataset is bundled. The dataset catalogue links to official sources and states each licence. Obtain data directly from the hosting institution and follow its terms.',
  },
]

const STACK = [
  ['Frontend', 'React 18, TypeScript, Vite, Tailwind CSS, Recharts'],
  ['Backend', 'FastAPI, SQLAlchemy, Alembic, PostgreSQL / SQLite, Pydantic v2'],
  ['ML service', 'FastAPI, NumPy, Pillow, OpenCV-style pipelines (feature-based)'],
  ['Deployment', 'Docker Compose with isolated internal network for the ML service'],
]

export function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="About this platform"
        description="A reproducible research environment for palmprint biometrics experiments, built around the principle that no result is ever invented."
      />

      <div className="grid gap-4 sm:grid-cols-2">
        {PRINCIPLES.map(({ icon: Icon, title, body }) => (
          <Card key={title} title={title}>
            <Icon className="mb-2 h-5 w-5 text-primary-600" />
            <p className="text-sm text-slate-600">{body}</p>
          </Card>
        ))}
      </div>

      <Card title="Technology stack" className="mt-4">
        <dl className="divide-y divide-slate-100">
          {STACK.map(([label, value]) => (
            <div key={label} className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3">
              <dt className="text-sm font-medium text-navy-900">{label}</dt>
              <dd className="text-sm text-slate-600 sm:col-span-2">{value}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <Card title="Scope and limitations" className="mt-4">
        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>
            This is a research and teaching tool. It is not certified for security, access control or
            forensic use.
          </li>
          <li>
            Recognition scores are not calibrated probabilities and must not be presented as
            accuracy figures.
          </li>
          <li>
            Benchmark counts are shown only when a local installation was verified; otherwise the
            dataset is reported as not installed.
          </li>
        </ul>
      </Card>
    </div>
  )
}

export default AboutPage
