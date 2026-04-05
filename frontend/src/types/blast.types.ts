/** TypeScript mirrors of backend Module 2 Pydantic models. */

export type TechCategory =
  | 'language'
  | 'framework'
  | 'tool'
  | 'platform'
  | 'database'
  | 'other'

export type Severity = 'high' | 'medium' | 'low'

export interface TechItem {
  name: string
  confidence: number
  category: TechCategory
}

export interface DepBlastEntry {
  lib_name: string
  affected_count: number
  severity: Severity
}

export interface FileImpactEntry {
  path: string
  repo: string
  depth: number
  language: string
}

export interface AnalyzeResult {
  tech_stack: TechItem[]
  top_tech_stack: TechItem[]
  dep_blast: DepBlastEntry[]
  file_impacts: FileImpactEntry[]
  repos_analyzed: number
  query_time_ms: number
}

export interface AnalyzeResponse {
  success: boolean
  data: AnalyzeResult | null
  error: string | null
}

export interface BlastDetailResponse {
  success: boolean
  data: FileImpactEntry[] | null
  error: string | null
}
