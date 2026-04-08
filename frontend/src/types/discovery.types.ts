export type QuizBackground = 'creative' | 'logical' | 'people'
export type QuizIntensity = 'startup' | 'corporate' | 'research'
export type QuizSolving = 'code' | 'ux' | 'strategy'
export type QuizInfluence = 'impact' | 'elegance' | 'creation'
export type QuizBreadth = 'generalist' | 'specialist'

export interface SkillQuizAnswers {
  background: QuizBackground
  intensity: QuizIntensity
  solving: QuizSolving
  influence: QuizInfluence
  breadth: QuizBreadth
}

export interface DiscoveryAnalyzeRequest {
  answers: SkillQuizAnswers
  related_limit?: number
  resource_limit?: number
}

export type DiscoveryNodeType =
  | 'RoleNode'
  | 'SkillNode'
  | 'DomainNode'
  | 'TraitNode'
  | 'LearningResourceNode'
  | 'LibNode'
  | 'FileNode'

export interface DiscoveryNode {
  id: string
  node_type: DiscoveryNodeType
  label: string
  category: string
  score: number
}

export interface DiscoveryEdge {
  edge_type:
    | 'IMPORTS'
    | 'CALLS'
    | 'LIB_DEPENDS_ON'
    | 'ROLE_REQUIRES_SKILL'
    | 'SKILL_RELATES_TO_SKILL'
    | 'SKILL_IN_DOMAIN'
    | 'TRAIT_ALIGNS_ROLE'
    | 'RESOURCE_TEACHES_SKILL'
    | 'SKILL_USES_LIB'
    | 'ROLE_IN_DOMAIN'
    | 'ROLE_USES_LIB'
    | 'TRAIT_RELATES_TO_SKILL'
    | 'RESOURCE_IN_DOMAIN'
    | 'FILE_SUPPORTS_SKILL'
    | 'DOMAIN_RELATES_TO_DOMAIN'
  src_id: string
  src_type: string
  tgt_id: string
  tgt_type: string
  weight: number
}

export interface SkillCluster {
  category: string
  skills: string[]
}

export interface DiscoveryGraph {
  nodes: DiscoveryNode[]
  edges: DiscoveryEdge[]
  node_count: number
  edge_count: number
}

export interface DiscoveryAnalyzeResult {
  recommendation_title: string
  recommendation_desc: string
  graph: DiscoveryGraph
  clusters: SkillCluster[]
  query_time_ms: number
}

export interface DiscoveryAnalyzeResponse {
  success: boolean
  data: DiscoveryAnalyzeResult | null
  error: string | null
}

export interface TrendingSkillItem {
  name: string
  category: string
  score: number
  connected_roles: string[]
}

export interface TrendingSkillsResult {
  skills: TrendingSkillItem[]
  query_time_ms: number
}

export interface TrendingSkillsResponse {
  success: boolean
  data: TrendingSkillsResult | null
  error: string | null
}
