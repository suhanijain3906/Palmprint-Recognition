// API types mirroring the backend Pydantic schemas.

export interface ApiErrorPayload {
  status: 'error'
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}

export interface PageMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface Page<T> {
  items: T[]
  meta: PageMeta
}

export interface MessageResponse {
  status: string
  message: string
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  environment: string
  database: string
  storage: string
  ml_service: Record<string, unknown>
  auth_enabled: boolean
  demo_mode: boolean
}

export interface ImageRecord {
  id: string
  original_filename: string
  media_type: string
  size_bytes: number
  width: number
  height: number
  checksum_sha256: string
  label?: string | null
  subject_id?: string | null
  notes?: string | null
  created_at: string
  download_url: string
  processing_status?: string | null
  last_operation?: string | null
}

export interface ImageUploadResponse {
  status: string
  image: ImageRecord
  validation: Record<string, unknown>
  warnings: string[]
}

export interface Artifact {
  id: string
  kind: string
  media_type: string
  size_bytes: number
  download_url: string
}

export interface ProcessingResponse {
  status: string
  job_id: string
  operation: string
  algorithm: string
  algorithm_version?: string | null
  image_id: string
  processing_time_ms: number
  metrics: Record<string, unknown>
  result: Record<string, unknown>
  artifacts: Artifact[]
  warnings: string[]
  limitations: string[]
  created_at?: string | null
}

export interface JobRecord {
  id: string
  image_id?: string | null
  operation: string
  algorithm: string
  algorithm_version?: string | null
  status: string
  parameters: Record<string, unknown>
  metrics: Record<string, unknown>
  warnings: string[]
  duration_ms?: number | null
  error_code?: string | null
  error_message?: string | null
  created_at: string
  completed_at?: string | null
}

export interface RecognitionResponse {
  status: string
  job_id: string
  similarity_score?: number | null
  score_kind: string
  is_trained_model: boolean
  is_calibrated_probability: boolean
  trained_model_available: boolean
  matcher: string
  matcher_version: string
  details: Record<string, unknown>
  artifacts: Artifact[]
  warnings: string[]
  limitations: string[]
  processing_time_ms: number
}

export interface ComparisonResponse {
  status: string
  job_id: string
  psnr_db?: number | null
  ssim?: number | null
  aligned: boolean
  resized: boolean
  metrics: Record<string, unknown>
  artifacts: Artifact[]
  warnings: string[]
  limitations: string[]
  processing_time_ms: number
}

export interface ExperimentResult {
  id: string
  kind: string
  label?: string | null
  value?: number | null
  unit?: string | null
  details: Record<string, unknown>
  image_id?: string | null
  order_index: number
}

export interface Experiment {
  id: string
  name: string
  description?: string | null
  operation: string
  algorithm: string
  parameters: Record<string, unknown>
  image_ids: string[]
  status: string
  duration_ms?: number | null
  error_message?: string | null
  report_id?: string | null
  created_at: string
  results: ExperimentResult[]
}

export interface ExperimentRequest {
  name: string
  description?: string
  operation: string
  algorithm: string
  parameters: Record<string, unknown>
  image_ids: string[]
}

export interface DatasetAvailability {
  status: string
  installed: boolean
  verified_image_count?: number | null
  verified_subject_count?: number | null
  local_path?: string | null
  message: string
}

export interface Dataset {
  id: string
  name: string
  description: string
  official_source: string
  licence: string
  access_requirements: string
  modality: string
  reference?: string | null
  availability: DatasetAvailability
  notes?: string | null
}

export interface Report {
  id: string
  title: string
  report_type: string
  status: string
  size_bytes?: number | null
  experiment_id?: string | null
  job_id?: string | null
  error_message?: string | null
  created_at: string
  generated_at?: string | null
  download_url?: string | null
}

export interface ReportCreateRequest {
  title: string
  report_type: string
  job_ids: string[]
  experiment_id?: string | null
  include_images: boolean
}

export interface AuthMode {
  auth_enabled: boolean
  allow_registration: boolean
  mode: 'authenticated' | 'academic_demo'
  message: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  display_name: string
  password: string
}

export interface UserInfo {
  id: string
  email: string
  display_name: string
  is_demo_account: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}
