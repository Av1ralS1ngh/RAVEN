/** TypeScript mirrors of backend Module 2 Pydantic models. */

export type TechCategory =
  | 'language'
  | 'framework'
  | 'tool'
  | 'platform'
  | 'database'
  | 'other'

export type Severity = 'high' | 'medium' | 'low'
export type BlastLabel = 'low' | 'medium' | 'high' | 'critical'

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
  change_score?: number
  language: string
}

export interface RepoAnalysisEntry {
  repo_name: string
  primary_language: string
  detected_stack: string[]
  overlap_stack: string[]
  missing_stack: string[]
  overlap_score: number
  file_count: number
  dependency_count: number
}

export interface MigrationShift {
  from_tech: string
  to_tech: string
  category: Exclude<TechCategory, 'other'>
  reason: string
  estimated_impacted_files: number
  affected_dependencies: string[]
}

export interface BestContenderAnalysis {
  repo_name: string
  overlap_stack: string[]
  missing_stack: string[]
  migration_shifts: MigrationShift[]
  blast_radius_score: number
  blast_radius_label: BlastLabel
  blast_radius_justification: string
}

export interface AnalyzeResult {
  tech_stack: TechItem[]
  top_tech_stack: TechItem[]
  recruiter_stack: string[]
  repo_analysis: RepoAnalysisEntry[]
  best_contender: BestContenderAnalysis | null
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
