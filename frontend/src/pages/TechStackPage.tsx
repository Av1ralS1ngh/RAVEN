import { useMemo, useState } from 'react'
import { useTechStack } from '@/hooks/useTechStack'
import type { FileImpactEntry } from '@/types/blast.types'
import type { DepBlastEntry } from '@/types/blast.types'
import DependencyBubbleChart from '@/components/blast/DependencyBubbleChart'

type BlastFilter = 'all' | 'high' | 'medium' | 'low'
type RankedDepBlastEntry = DepBlastEntry & { impactScore: number }

function impactMeta(score: number): { label: string; color: string; dot: string; guidance: string } {
  if (score >= 80) {
    return {
      label: 'Major Rewrite',
      color: 'text-[#ff8b7d]',
      dot: 'bg-[#ff8b7d]',
      guidance: 'Broad refactor likely needed across logic and dependencies.',
    }
  }
  if (score >= 60) {
    return {
      label: 'Significant Update',
      color: 'text-[#f3bd7a]',
      dot: 'bg-[#f3bd7a]',
      guidance: 'Multiple edits expected in this file and nearby modules.',
    }
  }
  if (score >= 35) {
    return {
      label: 'Localized Update',
      color: 'text-[#b8c9dc]',
      dot: 'bg-[#b8c9dc]',
      guidance: 'Targeted edits in one area, not a system-wide rewrite.',
    }
  }
  return {
    label: 'Minor Tuning',
    color: 'text-[#8a95a2]',
    dot: 'bg-[#687280]',
    guidance: 'Small adjustments are usually enough.',
  }
}

function scoreFromDepth(depth: number): number {
  if (depth <= 1) {
    return 88
  }
  if (depth === 2) {
    return 66
  }
  if (depth === 3) {
    return 44
  }
  return 22
}

function splitPath(path: string): { fileName: string; folder: string } {
  const normalized = path.replace(/\\/g, '/')
  const parts = normalized.split('/').filter(Boolean)
  if (parts.length === 0) {
    return { fileName: path, folder: 'root' }
  }
  if (parts.length === 1) {
    return { fileName: parts[0], folder: 'root' }
  }
  return {
    fileName: parts[parts.length - 1],
    folder: parts[parts.length - 2],
  }
}

function stableHash(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function chooseBySeed<T>(items: T[], seed: number): T {
  return items[Math.abs(seed) % items.length]
}

function tierFromScore(score: number): 'major' | 'significant' | 'localized' | 'minor' {
  if (score >= 80) {
    return 'major'
  }
  if (score >= 60) {
    return 'significant'
  }
  if (score >= 35) {
    return 'localized'
  }
  return 'minor'
}

function inferFileRole(path: string): 'ui' | 'api' | 'service' | 'data' | 'test' | 'general' {
  const lower = path.toLowerCase()
  const extension = lower.split('.').pop() ?? ''

  if (lower.includes('/test') || lower.includes('.spec.') || lower.includes('.test.')) {
    return 'test'
  }
  if (lower.includes('/component') || extension === 'tsx' || extension === 'jsx') {
    return 'ui'
  }
  if (lower.includes('/api') || lower.includes('/route') || lower.includes('/controller')) {
    return 'api'
  }
  if (lower.includes('/service') || lower.includes('/client')) {
    return 'service'
  }
  if (lower.includes('/model') || lower.includes('/schema') || lower.includes('/types') || lower.includes('/data')) {
    return 'data'
  }
  return 'general'
}

function normalizeStack(recruiterStack: string[], priorityStack: string[]): string[] {
  const merged = [...priorityStack, ...recruiterStack]
  const seen = new Set<string>()
  const normalized: string[] = []
  for (const tech of merged) {
    const trimmed = tech.trim()
    if (!trimmed) {
      continue
    }
    const key = trimmed.toLowerCase()
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    normalized.push(trimmed)
  }
  return normalized
}

function shouldExcludeDependency(libName: string): boolean {
  const normalized = libName.trim().toLowerCase()
  if (!normalized) {
    return true
  }

  return normalized.startsWith('@') || normalized.includes('eslint') || normalized.includes('heroicons') || normalized.includes('github.com/')
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function suggestedFixLine(
  impact: FileImpactEntry,
  recruiterStack: string[],
  priorityStack: string[],
  score: number,
): string {
  const stack = normalizeStack(recruiterStack, priorityStack)
  const seed = stableHash(`${impact.path}:${impact.repo}:${score}`)

  const techPrimary = stack.length > 0 ? chooseBySeed(stack, seed) : 'target stack'
  const techSecondary = stack.length > 1 ? chooseBySeed(stack, seed + 7) : techPrimary
  const role = inferFileRole(impact.path)
  const tier = tierFromScore(score)

  const templatesByRole: Record<'ui' | 'api' | 'service' | 'data' | 'test' | 'general', Record<'major' | 'significant' | 'localized' | 'minor', string[]>> = {
    ui: {
      major: [
        `Refactor this UI file to isolate data-fetching into a ${techPrimary} hook and keep this component purely presentational.`,
        `Split this component into a view layer plus a ${techPrimary}-aligned adapter to remove direct dependency coupling.`,
        `Move stateful integration logic from this screen into a ${techPrimary} boundary and keep rendering concerns here only.`,
      ],
      significant: [
        `Replace direct integration calls in this component with a ${techPrimary} facade and update event handlers to consume typed outputs.`,
        `Introduce a ${techPrimary}-style mapper in this file so UI props are derived from one normalized model.`,
        `Route this component's external dependency usage through a ${techPrimary} utility and reduce duplicated transform logic.`,
      ],
      localized: [
        `Add a small ${techPrimary} wrapper in this file for the main dependency call and keep JSX structure unchanged.`,
        `Normalize one high-impact prop path in this component using a ${techPrimary} helper to reduce blast surface.`,
        `Patch this UI file to consume a ${techPrimary}-compatible shape before rendering.`,
      ],
      minor: [
        `Apply a targeted ${techPrimary} compatibility helper around the single highest-risk call in this component.`,
        `Keep behavior intact and add one ${techPrimary} mapping function to stabilize this file's input contract.`,
        `Tighten this component with a lightweight ${techPrimary} adapter for the primary integration touchpoint.`,
      ],
    },
    api: {
      major: [
        `Restructure this API boundary around a ${techPrimary} contract and remove direct dependency-specific payload handling.`,
        `Introduce a ${techPrimary} request/response adapter layer in this route file and centralize protocol translation.`,
        `Break this endpoint logic into controller + ${techPrimary} gateway so integration blast stays outside route handlers.`,
      ],
      significant: [
        `Replace this file's high-blast dependency calls with a ${techPrimary} client interface and typed DTO mapping.`,
        `Wrap external calls here with a ${techPrimary} transport abstraction and unify error paths in one function.`,
        `Move protocol conversion in this file to a ${techPrimary}-aligned serializer to reduce coupling.`,
      ],
      localized: [
        `Patch this API file by introducing one ${techPrimary} client shim for the main downstream call.`,
        `Add a ${techPrimary} DTO mapper in this endpoint and keep route signatures stable.`,
        `Isolate one high-impact branch behind a ${techPrimary} adapter function in this file.`,
      ],
      minor: [
        `Apply a small ${techPrimary} compatibility layer to this endpoint's primary dependency call path.`,
        `Add one ${techPrimary} translation helper for this route and preserve current API response shape.`,
        `Keep this API file mostly unchanged and wrap only the top-risk integration touchpoint with ${techPrimary}.`,
      ],
    },
    service: {
      major: [
        `Refactor this service around a ${techPrimary}/${techSecondary} interface so providers can be swapped without call-site changes.`,
        `Split this service into domain logic plus a ${techPrimary} connector to isolate external dependency churn.`,
        `Move dependency-specific code in this service behind a ${techPrimary} strategy and keep business rules provider-agnostic.`,
      ],
      significant: [
        `Replace direct provider wiring in this service with a ${techPrimary} abstraction and central retry/error policy.`,
        `Introduce a ${techPrimary} gateway in this service file and map results to one canonical domain type.`,
        `Consolidate integration calls in this service through a ${techPrimary} client factory to reduce drift.`,
      ],
      localized: [
        `Add a ${techPrimary} adapter function in this service for its highest-impact dependency call.`,
        `Patch this service by mapping one dependency response into a ${techPrimary}-aligned domain object.`,
        `Keep service flow intact and introduce a ${techPrimary} helper for one volatile integration branch.`,
      ],
      minor: [
        `Apply a minimal ${techPrimary} compatibility wrapper in this service for the top-risk call path.`,
        `Add one ${techPrimary} utility in this service to normalize dependency output before returning.`,
        `Preserve this service behavior and isolate one call with a ${techPrimary} shim.`,
      ],
    },
    data: {
      major: [
        `Rework this data/model file to define a single ${techPrimary}-aligned schema and migrate all inbound mappings to it.`,
        `Create one canonical ${techPrimary} model in this file and remove duplicated dependency-shaped structures.`,
        `Refactor this schema layer to enforce ${techPrimary} contracts before persistence or transport boundaries.`,
      ],
      significant: [
        `Update this data file to map dependency payloads into a ${techPrimary}-compatible type before use.`,
        `Introduce ${techPrimary} validation/typing in this model file and gate unsafe fields at construction time.`,
        `Normalize this file's core type definitions to match ${techPrimary} expectations and reduce conversion spread.`,
      ],
      localized: [
        `Add one ${techPrimary} transform in this data file for the highest-impact payload path.`,
        `Patch this model file by tightening one type contract around ${techPrimary} usage.`,
        `Keep current structures and add a focused ${techPrimary} mapper for one volatile field group.`,
      ],
      minor: [
        `Apply a small ${techPrimary} type or schema tweak in this file to reduce mismatch risk.`,
        `Introduce one ${techPrimary} guard in this data file for safer downstream consumption.`,
        `Keep this file stable and add a minimal ${techPrimary} normalization helper.`,
      ],
    },
    test: {
      major: [
        `Rewrite this test file around a ${techPrimary} fixture contract so integration changes do not break broad assertions.`,
        `Create ${techPrimary}-aligned mocks in this test file and separate provider behavior from business assertions.`,
        `Refactor this suite to use a ${techPrimary} test adapter and stabilize high-blast integration cases.`,
      ],
      significant: [
        `Update this test file with a ${techPrimary} mock boundary for the primary dependency path.`,
        `Switch this suite to ${techPrimary}-compatible fixtures and keep assertions focused on domain output.`,
        `Add a ${techPrimary} stub layer in this test file to isolate dependency response churn.`,
      ],
      localized: [
        `Patch one high-impact test case here to consume a ${techPrimary} fixture shape.`,
        `Add a focused ${techPrimary} mock in this file for the top-risk branch.`,
        `Keep this suite intact and add one ${techPrimary} fixture mapper for brittle assertions.`,
      ],
      minor: [
        `Apply a lightweight ${techPrimary} fixture update in this test file for better contract alignment.`,
        `Adjust one assertion path here to use a ${techPrimary}-compatible mock output.`,
        `Make a small ${techPrimary} test-helper tweak in this file to reduce integration drift.`,
      ],
    },
    general: {
      major: [
        `Refactor this file to isolate dependency-facing logic behind a ${techPrimary} boundary and keep core flow technology-agnostic.`,
        `Split this file so ${techPrimary} integration concerns are separated from business logic and shared as one adapter.`,
        `Move direct external coupling in this file into a ${techPrimary} interface with stable internal contracts.`,
      ],
      significant: [
        `Replace one high-blast dependency path in this file with a ${techPrimary} abstraction and normalized outputs.`,
        `Introduce a ${techPrimary} helper layer in this file and route external calls through it.`,
        `Update this file's integration branch to a ${techPrimary}-compatible adapter and keep call sites unchanged.`,
      ],
      localized: [
        `Add one ${techPrimary} shim in this file for the highest-impact dependency call path.`,
        `Patch this file with a focused ${techPrimary} compatibility mapper at the integration edge.`,
        `Keep this file stable and isolate one volatile dependency branch behind ${techPrimary}.`,
      ],
      minor: [
        `Apply a targeted ${techPrimary} compatibility edit in this file while preserving current behavior.`,
        `Add one small ${techPrimary} wrapper in this file to reduce dependency mismatch risk.`,
        `Keep behavior unchanged and introduce a minimal ${techPrimary} adapter for the main touchpoint.`,
      ],
    },
  }

  return chooseBySeed(templatesByRole[role][tier], seed + role.length)
}

export default function TechStackPage() {
  const {
    recruiterUrl,
    setRecruiterUrl,
    githubUsername,
    setGithubUsername,
    isLoading,
    error,
    result,
    selectedLib,
    selectLib,
    isLoadingDetail,
    submit,
  } = useTechStack()

  const [selectedRepo, setSelectedRepo] = useState('')
  const [blastFilter, setBlastFilter] = useState<BlastFilter>('all')
  const [blastQuery, setBlastQuery] = useState('')
  const [openFixKey, setOpenFixKey] = useState<string | null>(null)

  const repoOptions = useMemo(
    () => result?.repo_analysis.map(repo => repo.repo_name) ?? [],
    [result],
  )

  const activeRepo = useMemo(() => {
    if (!result) {
      return ''
    }

    if (selectedRepo && repoOptions.includes(selectedRepo)) {
      return selectedRepo
    }

    const contender = result.best_contender?.repo_name ?? ''
    if (contender && repoOptions.includes(contender)) {
      return contender
    }

    return repoOptions[0] ?? ''
  }, [result, repoOptions, selectedRepo])

  const repoImpacts = useMemo(() => {
    if (!result || !activeRepo) {
      return []
    }
    return result.file_impacts
      .filter(item => item.repo === activeRepo)
      .sort((a, b) => {
        const scoreA = typeof a.change_score === 'number' ? a.change_score : scoreFromDepth(a.depth)
        const scoreB = typeof b.change_score === 'number' ? b.change_score : scoreFromDepth(b.depth)
        return a.depth - b.depth || scoreB - scoreA || a.path.localeCompare(b.path)
      })
  }, [result, activeRepo])

  const selectedRepoAnalysis = useMemo(() => {
    if (!result || !activeRepo) {
      return null
    }
    return result.repo_analysis.find(item => item.repo_name === activeRepo) ?? null
  }, [result, activeRepo])

  const displayedTechStack = useMemo(
    () => result?.tech_stack.slice(0, 8) ?? [],
    [result],
  )

  const searchedDeps = useMemo(() => {
    if (!result) {
      return []
    }

    const query = blastQuery.trim().toLowerCase()
    const items = result.dep_blast
      .filter(item => !shouldExcludeDependency(item.lib_name))
      .filter(item => (query ? item.lib_name.toLowerCase().includes(query) : true))

    return items.sort(
      (a, b) => b.affected_count - a.affected_count || a.lib_name.localeCompare(b.lib_name),
    )
  }, [result, blastQuery])

  const tieredDeps = useMemo<RankedDepBlastEntry[]>(() => {
    const repoLibSet = new Set(
      (selectedRepoAnalysis?.detected_stack ?? [])
        .map(item => item.trim().toLowerCase())
        .filter(item => item.length > 0),
    )

    const ranked = [...searchedDeps].sort((a, b) => {
      const aInRepo = repoLibSet.has(a.lib_name.toLowerCase()) ? 1 : 0
      const bInRepo = repoLibSet.has(b.lib_name.toLowerCase()) ? 1 : 0
      return bInRepo - aInRepo || b.affected_count - a.affected_count || a.lib_name.localeCompare(b.lib_name)
    })

    if (ranked.length === 0) {
      return []
    }

    if (ranked.length <= 2) {
      return ranked.map((item, index) => {
        const severity: DepBlastEntry['severity'] = index === 0 ? 'high' : 'medium'
        const base = severity === 'high' ? 75 : 55
        return {
          ...item,
          severity,
          impactScore: base,
        }
      })
    }

    let highCount = Math.max(1, Math.min(4, Math.round(ranked.length * 0.18)))
    highCount = Math.min(highCount, ranked.length - 1)

    const reserveLow = ranked.length >= 5 ? 1 : 0
    const minMedium = ranked.length >= 5 ? Math.min(3, ranked.length - highCount - reserveLow) : Math.min(2, ranked.length - highCount)
    const maxMedium = Math.min(8, ranked.length - highCount - reserveLow)
    let mediumCount = clamp(Math.round(ranked.length * 0.4), minMedium, Math.max(minMedium, maxMedium))
    mediumCount = Math.min(mediumCount, ranked.length - highCount - reserveLow)

    return ranked.map((item, index) => {
      const isInRepo = repoLibSet.has(item.lib_name.toLowerCase())
      if (index < highCount) {
        const rankRatio = ranked.length <= 1 ? 1 : 1 - (index / (ranked.length - 1))
        const affectedBoost = Math.min(22, Math.round(Math.log10(item.affected_count + 1) * 14))
        const score = clamp(68 + affectedBoost + Math.round(rankRatio * 18) + (isInRepo ? 6 : 0), 20, 98)
        return { ...item, severity: 'high' as const, impactScore: score }
      }
      if (index < highCount + mediumCount) {
        const rankRatio = ranked.length <= 1 ? 1 : 1 - (index / (ranked.length - 1))
        const affectedBoost = Math.min(18, Math.round(Math.log10(item.affected_count + 1) * 11))
        const score = clamp(44 + affectedBoost + Math.round(rankRatio * 14) + (isInRepo ? 4 : 0), 16, 92)
        return { ...item, severity: 'medium' as const, impactScore: score }
      }
      const rankRatio = ranked.length <= 1 ? 1 : 1 - (index / (ranked.length - 1))
      const affectedBoost = Math.min(14, Math.round(Math.log10(item.affected_count + 1) * 9))
      const score = clamp(24 + affectedBoost + Math.round(rankRatio * 10) + (isInRepo ? 2 : 0), 12, 78)
      return { ...item, severity: 'low' as const, impactScore: score }
    })
  }, [searchedDeps, selectedRepoAnalysis])

  const depBlastCounts = useMemo(() => {
    return {
      all: tieredDeps.length,
      high: tieredDeps.filter(item => item.severity === 'high').length,
      medium: tieredDeps.filter(item => item.severity === 'medium').length,
      low: tieredDeps.filter(item => item.severity === 'low').length,
    }
  }, [tieredDeps])

  const filteredDeps = useMemo(() => {
    if (blastFilter === 'all') {
      return tieredDeps
    }
    return tieredDeps.filter(item => item.severity === blastFilter)
  }, [tieredDeps, blastFilter])

  const maxAffectedCount = useMemo(() => {
    if (filteredDeps.length === 0) {
      return 1
    }
    return Math.max(...filteredDeps.map(item => item.impactScore), 1)
  }, [filteredDeps])

  const scoreStats = useMemo(() => {
    if (repoImpacts.length === 0) {
      return null
    }
    const scores = repoImpacts.map(item => (
      typeof item.change_score === 'number' ? item.change_score : scoreFromDepth(item.depth)
    ))

    const min = Math.min(...scores)
    const max = Math.max(...scores)
    const avg = Math.round(scores.reduce((sum, value) => sum + value, 0) / scores.length)

    return { min, max, avg }
  }, [repoImpacts])

  return (
    <>
      <section className="grid grid-cols-1 xl:grid-cols-2 gap-6 p-6 md:p-10 border-b border-[#2b3440]">
        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6 md:p-8 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
          <div className="mb-7">
            <h2 className="font-headline font-extrabold text-2xl text-[#eef3f8] tracking-tight mb-2">Tech Stack Analyzer</h2>
            <p className="text-[#99a5b3] text-sm font-body">Scan recruiter signals and compare them against your latest repositories.</p>
          </div>

          <div className="space-y-5 max-w-2xl">
            <div className="space-y-1">
              <label className="font-label text-[10px] text-[#778392] uppercase tracking-[0.2em]">LinkedIn URL</label>
              <input
                type="text"
                placeholder="https://www.linkedin.com/in/recruiter-profile"
                value={recruiterUrl}
                onChange={e => setRecruiterUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && void submit()}
                className="w-full bg-[#0a0f15] border border-[#2b3440] px-4 py-3 text-[#eef3f8] font-label rounded-lg focus:outline-none focus:border-[#9db3ca] transition-colors"
              />
            </div>

            <div className="space-y-1">
              <label className="font-label text-[10px] text-[#778392] uppercase tracking-[0.2em]">GitHub Username</label>
              <input
                type="text"
                placeholder="your-github-username"
                value={githubUsername}
                onChange={e => setGithubUsername(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && void submit()}
                className="w-full bg-[#0a0f15] border border-[#2b3440] px-4 py-3 text-[#eef3f8] font-label rounded-lg focus:outline-none focus:border-[#9db3ca] transition-colors"
              />
            </div>

            <button
              onClick={() => void submit()}
              disabled={isLoading}
              className="btn-shine bg-[linear-gradient(120deg,#c9d5e1,#90a5bc)] text-[#0b1118] px-8 py-3 border border-[#b9c8d8] rounded-lg font-label font-bold uppercase tracking-widest text-sm hover:brightness-105 transition-all disabled:opacity-50"
            >
              {isLoading ? 'Analyzing...' : 'Run Analysis'}
            </button>

            {error && <p className="text-sm font-label text-[#ff8b7d] mt-1">{String(error)}</p>}
          </div>
        </div>

        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6 md:p-8 shadow-[0_20px_60px_rgba(0,0,0,0.35)] flex flex-col">
          <div className="mb-6">
            <h2 className="font-headline font-extrabold text-2xl text-[#eef3f8] tracking-tight mb-2">Detected Stack</h2>
            <p className="text-[#99a5b3] text-sm font-body">Technologies extracted from recruiter context and fallback signals.</p>
          </div>

          <div className="flex flex-wrap gap-3 flex-1 content-start">
            {!result && !isLoading && (
              <div className="font-label text-sm text-[#6f7b89] py-4">Awaiting analysis...</div>
            )}
            {isLoading && !result && (
              <div className="font-label text-sm text-[#b7c8da] animate-pulse py-4">Extracting recruiter stack...</div>
            )}
            {result && displayedTechStack.map((ts, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 bg-[#101923] border border-[#2b3440] px-3 py-2 rounded-md"
                title={`Confidence: ${(ts.confidence * 100).toFixed(0)}%`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${idx < 3 ? 'bg-[#d6e1ec]' : 'bg-[#708090]'}`} />
                <span className="font-label text-xs tracking-wide uppercase text-[#e6edf5]">{ts.name}</span>
              </div>
            ))}
          </div>

          {result && (
            <div className="mt-8">
              <div className="relative w-full h-[2px] bg-[#2b3440] rounded">
                <div
                  className="absolute top-0 left-0 h-full bg-[linear-gradient(90deg,#a7b9cc,#e7eff7)] rounded"
                  style={{ width: `${Math.round(result.tech_stack[0]?.confidence * 100 || 0)}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 font-label text-[10px] text-[#778392] tracking-[0.14em] uppercase">
                <span>Peak Confidence</span>
                <span>{result.tech_stack[0] ? (result.tech_stack[0].confidence * 100).toFixed(1) : '0.0'}%</span>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-6 p-6 md:p-10">
        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6 md:p-8 shadow-[0_16px_40px_rgba(0,0,0,0.32)]">
          <h3 className="font-headline font-bold text-lg text-[#eef3f8] mb-3 tracking-tight">Dependency Blast Summary</h3>
          <p className="text-[#7f8c9a] text-xs mb-5">
            Shows each dependency's blast impact: how many files are affected if that dependency changes.
            Bubble size increases from low to high impact; hover to inspect and click a bubble to focus it.
            Scoped packages and lint/icon deps are hidden, and this panel follows the selected repository where possible.
          </p>

          <div className="grid grid-cols-3 gap-3 mb-5">
            <div className="rounded-lg border border-[#2b3440] bg-[#0b1118] p-3">
              <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a]">Dependencies</div>
              <div className="text-[#e8eff7] text-lg font-semibold mt-1">{result ? depBlastCounts.all : '--'}</div>
            </div>
            <div className="rounded-lg border border-[#2b3440] bg-[#0b1118] p-3">
              <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a]">Total Reach</div>
              <div className="text-[#e8eff7] text-lg font-semibold mt-1">{result ? result.dep_blast.reduce((acc, b) => acc + b.affected_count, 0) : '--'}</div>
            </div>
            <div className="rounded-lg border border-[#2b3440] bg-[#0b1118] p-3">
              <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a]">Repos</div>
              <div className="text-[#e8eff7] text-lg font-semibold mt-1">{result ? result.repos_analyzed : '--'}</div>
            </div>
          </div>

          {result && (
            <>
              <div className="flex flex-wrap gap-2 mb-3">
                {([
                  { key: 'all', label: `All (${depBlastCounts.all})` },
                  { key: 'high', label: `High (${depBlastCounts.high})` },
                  { key: 'medium', label: `Medium (${depBlastCounts.medium})` },
                  { key: 'low', label: `Low (${depBlastCounts.low})` },
                ] as Array<{ key: BlastFilter; label: string }>).map(item => (
                  <button
                    key={item.key}
                    onClick={() => setBlastFilter(item.key)}
                    className={`px-2.5 py-1 rounded-md text-[10px] font-label uppercase tracking-[0.14em] border transition-colors ${
                      blastFilter === item.key
                        ? 'border-[#9db3ca] bg-[#1a2431] text-[#e5edf6]'
                        : 'border-[#2b3440] bg-[#101923] text-[#8591a0] hover:text-[#cbd7e4]'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              <input
                type="text"
                value={blastQuery}
                onChange={e => setBlastQuery(e.target.value)}
                placeholder="Search dependency..."
                className="w-full bg-[#0a0f15] border border-[#2b3440] px-3 py-2 mb-4 text-[#eef3f8] font-label text-xs rounded-lg focus:outline-none focus:border-[#9db3ca]"
              />

              <DependencyBubbleChart
                deps={filteredDeps}
                selectedLib={selectedLib}
                onSelect={libName => void selectLib(libName)}
              />

              <div className="bg-[#0b1118] p-3 border border-[#2b3440] rounded-lg max-h-[250px] overflow-y-auto space-y-2">
                {filteredDeps.length === 0 && (
                  <div className="text-[#7b8693] text-xs py-2">No dependencies match this filter.</div>
                )}

                {filteredDeps.map(dep => {
                  const ratio = Math.max(4, Math.round((dep.impactScore / maxAffectedCount) * 100))
                  const selected = dep.lib_name === selectedLib
                  return (
                    <button
                      key={dep.lib_name}
                      onClick={() => void selectLib(dep.lib_name)}
                      className={`w-full text-left rounded-md border px-3 py-2 transition-colors ${selected ? 'border-[#9db3ca] bg-[#15202d]' : 'border-[#2b3440] bg-[#101923] hover:bg-[#15202d]'} `}
                    >
                      <div className="flex items-center justify-between gap-3 mb-1.5">
                        <div className="text-[#e5edf6] text-xs truncate">{dep.lib_name}</div>
                        <div className="text-[10px] uppercase tracking-[0.14em] font-label text-[#98acbf] shrink-0">{dep.severity}</div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="h-1.5 bg-[#273341] rounded w-full overflow-hidden">
                          <div className="h-full bg-[linear-gradient(90deg,#7f9ab6,#d8e4f0)]" style={{ width: `${ratio}%` }} />
                        </div>
                        <div className="text-[#c5d3e1] text-xs shrink-0">{dep.impactScore}</div>
                      </div>
                    </button>
                  )
                })}
              </div>

            </>
          )}
        </div>

        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6 md:p-8 shadow-[0_16px_40px_rgba(0,0,0,0.32)]">
          <h3 className="font-headline font-bold text-lg text-[#eef3f8] mb-6 tracking-tight">Impact Ranked Files</h3>
          <p className="text-[#7f8c9a] text-xs mb-2">
            Change Score is a relative effort score (not a bug count): higher means wider blast reach, weaker recruiter-fit, and heavier dependency coupling.
          </p>
          <p className="text-[#6f7b89] text-[11px] mb-4">
            If scores looked low earlier, calibration was conservative; they are now stretched to better separate medium/high impact files.
          </p>

          <div className="mb-4 space-y-3">
            {result && (
              <>
                <div className="flex items-center justify-between gap-4">
                  <label className="font-label text-[10px] text-[#778392] uppercase tracking-[0.2em]">Repository</label>
                  <span className="font-label text-[10px] text-[#b8c9dc] uppercase tracking-[0.16em]">
                    Best: {result.best_contender?.repo_name ?? 'N/A'}
                  </span>
                </div>
                <select
                  value={activeRepo}
                  onChange={e => setSelectedRepo(e.target.value)}
                  className="w-full bg-[#0a0f15] border border-[#2b3440] px-3 py-2 text-[#eef3f8] font-label text-xs rounded-lg focus:outline-none focus:border-[#9db3ca]"
                >
                  {repoOptions.map(repo => (
                    <option key={repo} value={repo}>{repo}</option>
                  ))}
                </select>
              </>
            )}
          </div>

          {selectedRepoAnalysis && (
            <div className="mb-4 p-3 rounded-lg border border-[#2b3440] bg-[#0b1118]">
              <div className="font-label text-[10px] uppercase tracking-[0.16em] text-[#7f8c9a] mb-1">Selected Repo Fit</div>
              <div className="text-sm text-[#dbe5ef]">
                Overlap Score: {(selectedRepoAnalysis.overlap_score * 100).toFixed(1)}%
              </div>
            </div>
          )}

          {scoreStats && (
            <div className="mb-4 p-3 rounded-lg border border-[#2b3440] bg-[#0b1118] grid grid-cols-3 gap-3">
              <div>
                <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a]">Min</div>
                <div className="text-[#e7eef6] text-sm">{scoreStats.min}</div>
              </div>
              <div>
                <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a]">Avg</div>
                <div className="text-[#e7eef6] text-sm">{scoreStats.avg}</div>
              </div>
              <div>
                <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a]">Max</div>
                <div className="text-[#e7eef6] text-sm">{scoreStats.max}</div>
              </div>
            </div>
          )}

          <div className="space-y-1 max-h-[330px] overflow-y-auto pr-1">
            {!result && (
              <div className="font-label text-sm text-[#6f7b89] py-2">Run analysis to rank file impacts by repository.</div>
            )}
            {isLoadingDetail && (
              <div className="font-label text-sm text-[#b7c8da] animate-pulse py-2">Calculating impact detail...</div>
            )}
            {result && activeRepo && repoImpacts.length === 0 && (
              <div className="font-label text-sm text-[#7b8693] py-2">No indexed files were found for this repository.</div>
            )}
            {repoImpacts.map((impact, i) => {
              const score = typeof impact.change_score === 'number' ? impact.change_score : scoreFromDepth(impact.depth)
              const meta = impactMeta(score)
              const short = splitPath(impact.path)
              const rowKey = `${impact.repo}:${impact.path}:${i}`
              const fixLine = suggestedFixLine(
                impact,
                result?.recruiter_stack ?? [],
                selectedRepoAnalysis?.missing_stack ?? [],
                score,
              )
              return (
                <div key={rowKey} className="rounded-md border border-[#25303c] bg-[#101923] px-2">
                  <div className="group flex items-center gap-4 py-2.5 hover:bg-[#141d28] rounded-md transition-colors cursor-default">
                    <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />

                    <div className="min-w-0 flex-1">
                      <div className="font-label text-xs text-[#e4ebf2] truncate">{short.fileName}</div>
                      <div className="font-label text-[10px] text-[#7f8c9a] truncate">folder: {short.folder}</div>
                    </div>

                    <div className="text-right shrink-0" title={meta.guidance}>
                      <div className="font-label text-[10px] text-[#9db0c5]">Change Score</div>
                      <div className="font-label text-xs text-[#e9eef4]">{score}/100</div>
                      <div className={`font-label text-[10px] uppercase tracking-widest ${meta.color}`}>{meta.label}</div>
                    </div>

                    <button
                      onClick={() => setOpenFixKey(current => (current === rowKey ? null : rowKey))}
                      className="shrink-0 font-label text-[10px] uppercase tracking-[0.14em] text-[#9db3ca] hover:text-[#dbe7f3]"
                    >
                      {openFixKey === rowKey ? 'Hide Fix' : 'Suggested Fix'}
                    </button>
                  </div>

                  {openFixKey === rowKey && (
                    <div className="px-2 pb-3">
                      <div className="rounded-md border border-[#2b3440] bg-[#0b1118] px-3 py-2.5">
                        <div className="font-label text-[10px] uppercase tracking-[0.14em] text-[#7f8c9a] mb-1">One-line suggested fix</div>
                        <p className="text-[#d7e2ed] text-xs leading-relaxed">{fixLine}</p>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {result && (
            <div className="mt-8 grid grid-cols-2 gap-6 opacity-70">
              <div className="border-l-2 border-[#2e3947] pl-4">
                <div className="font-label text-[10px] uppercase tracking-widest text-[#7a8694]">Query Latency</div>
                <div className="font-label text-xl text-[#e9eef4]">{result.query_time_ms.toFixed(0)} ms</div>
              </div>
              <div className="border-l-2 border-[#2e3947] pl-4">
                <div className="font-label text-[10px] uppercase tracking-widest text-[#7a8694]">Files Listed</div>
                <div className="font-label text-xl text-[#e9eef4]">{repoImpacts.length}</div>
              </div>
            </div>
          )}
        </div>
      </section>

      <footer className="fixed bottom-0 md:left-64 right-0 h-10 bg-[#0f141b] border-t border-[#2b3440] flex items-center justify-between px-6 z-40">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 ${isLoading || isLoadingDetail ? 'bg-[#b7c8da] animate-pulse' : 'bg-[#d8e2ec]'} rounded-full`} />
            <span className="font-label text-[9px] uppercase tracking-widest text-[#778392]">
              {isLoading ? 'Analyzer Active' : 'System Idle'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-label text-[9px] uppercase tracking-widest text-[#778392]">Target: {selectedLib || 'NONE'}</span>
        </div>
      </footer>
    </>
  )
}
