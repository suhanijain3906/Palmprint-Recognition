import { Link } from 'react-router-dom'
import {
  Upload,
  Scan,
  Sparkles,
  Gauge,
  GitCompare,
  Target,
  MapPin,
  FlaskConical,
  FileText,
  ShieldAlert,
} from 'lucide-react'

const features = [
  {
    title: 'ROI extraction',
    description: 'Classical, replaceable region-of-interest proposal with explicit accuracy caveats.',
    icon: Scan,
  },
  {
    title: 'Image enhancement',
    description: 'Histogram equalisation, CLAHE, median and Gaussian filtering, sharpening.',
    icon: Sparkles,
  },
  {
    title: 'Quality assessment',
    description: 'Brightness, contrast, blur proxy (variance of Laplacian) and dimensions.',
    icon: Gauge,
  },
  {
    title: 'Feature extraction',
    description: 'ORB and texture baselines with downloadable descriptors and reasoning.',
    icon: Target,
  },
  {
    title: 'Comparison metrics',
    description: 'PSNR, SSIM and absolute difference visualisation for aligned pairs.',
    icon: GitCompare,
  },
  {
    title: 'Landmark visualisation',
    description: 'Feature-point overlays clearly distinguished from anatomical landmarks.',
    icon: MapPin,
  },
]

const steps = [
  { label: 'Upload', detail: 'Validate, hash and store the original file unmodified.' },
  { label: 'Process', detail: 'Run ROI, enhancement, features and quality on the ML service.' },
  { label: 'Compare', detail: 'Measure pixel and feature similarity between two captures.' },
  { label: 'Report', detail: 'Export a reproducible PDF with parameters and measurements.' },
]

export function HomePage() {
  return (
    <div className="mx-auto max-w-5xl space-y-12">
      <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-8 sm:p-12">
        <span className="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">
          Experimental research platform
        </span>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-navy-900 sm:text-4xl">
          Palmprint processing, analysis and comparison
        </h1>
        <p className="mt-4 max-w-2xl text-slate-600">
          An open, modular research workspace for contactless palmprint studies. It provides
          reproducible classical image-processing pipelines, honest quality analysis and measurable
          image/feature comparison — without fabricated recognition results.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/upload" className="btn-primary">
            <Upload className="mr-2 h-4 w-4" />
            Upload a palmprint image
          </Link>
          <Link to="/analysis" className="btn-secondary">
            <Scan className="mr-2 h-4 w-4" />
            Palmprint Analysis
          </Link>
          <Link to="/dashboard" className="btn-secondary">
            Open the dashboard
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-navy-900">Capabilities</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div key={feature.title} className="card p-5">
                <Icon className="h-5 w-5 text-primary-600" />
                <h3 className="mt-3 text-sm font-semibold text-navy-900">{feature.title}</h3>
                <p className="mt-1 text-xs text-slate-600">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-navy-900">Processing workflow</h2>
        <ol className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <li key={step.label} className="card p-5">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-600 text-xs font-semibold text-white">
                {index + 1}
              </span>
              <h3 className="mt-3 text-sm font-semibold text-navy-900">{step.label}</h3>
              <p className="mt-1 text-xs text-slate-600">{step.detail}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <h2 className="text-base font-semibold text-navy-900">Research & evaluation</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-600">
            <li>• Genuine/impostor comparison tooling with ROC, AUC, FAR, FRR and EER.</li>
            <li>• Experiment history with algorithm parameters and measured results.</li>
            <li>• Exportable PDF reports documenting exactly what was executed.</li>
            <li>• Benchmark dataset catalogue with licence and access instructions.</li>
          </ul>
          <div className="mt-4 flex gap-3">
            <Link to="/experiments" className="btn-secondary">
              <FlaskConical className="mr-2 h-4 w-4" />
              Experiments
            </Link>
            <Link to="/reports" className="btn-secondary">
              <FileText className="mr-2 h-4 w-4" />
              Reports
            </Link>
          </div>
        </div>
        <div className="card p-5">
          <h2 className="text-base font-semibold text-navy-900">Supported formats</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-600">
            <li>PNG · JPEG · BMP · TIFF · WebP</li>
            <li>Up to 12 MB per file</li>
            <li>Original file stored unmodified</li>
          </ul>
        </div>
      </section>

      <section className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
        <p>
          <strong>Research-use disclaimer.</strong> This platform is an experimental research tool,
          not a production identity-verification system. Results are uncalibrated and must not be
          used for access control or any decision affecting individuals. Palmprints are biometric
          data — only upload images you are authorised to process and never redistribute them.
        </p>
      </section>
    </div>
  )
}

export default HomePage
