/** TypeScript mirrors of backend Module 1 Pydantic models. */

export interface PersonSummary {
  id: string
  name: string
  headline: string
  company: string
  linkedin_url: string
  mutual_count: number
}

export interface PathResult {
  path: PersonSummary[]
  hop_count: number
  alternative_paths: PersonSummary[][]
  total_connections_mapped: number
  query_time_ms: number
}

export interface PathResponse {
  success: boolean
  data: PathResult | null
  error: string | null
}

/** POST /api/path/find request body — mirrors backend PathRequest */
export interface PathRequest {
  recruiter_url: string       // Full LinkedIn profile URL
  your_linkedin_id: string   // Caller's LinkedIn public username, e.g. "john-doe"
  max_hops?: number           // Default 6, clamped 1–10
}
