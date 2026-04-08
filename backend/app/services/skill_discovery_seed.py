"""Startup seeding for skill discovery entities in DepGraph."""

from __future__ import annotations

import logging

from app.services.tigergraph_client import (
    DepEdge,
    DomainNode,
    FileNode,
    LearningResourceNode,
    LibNode,
    RoleNode,
    SkillNode,
    TigerGraphClient,
    TraitNode,
)

logger = logging.getLogger(__name__)

ROLE_SKILL_MAP: dict[str, list[str]] = {
    "Graph Database & Backend Researcher": [
        "TigerGraph",
        "Distributed Systems",
        "Performance Optimization",
        "FastAPI",
        "Database Design",
        "Docker",
    ],
    "Full-Stack Solutions Architect": [
        "TypeScript",
        "React",
        "FastAPI",
        "GraphQL",
        "Database Design",
        "Docker",
    ],
    "AI Product Lead": [
        "Product Strategy",
        "LLM Ops",
        "Agile Leadership",
        "UX Research",
        "Cloud Architecture",
    ],
    "Creative Frontend Engineer": [
        "React",
        "TypeScript",
        "Design Systems",
        "Framer Motion",
        "UX Research",
    ],
    "Design Systems Architect": [
        "Design Systems",
        "Figma API",
        "Framer Motion",
        "UX Research",
        "TypeScript",
    ],
    "Technical Generalist / PM": [
        "Product Strategy",
        "Agile Leadership",
        "GraphQL",
        "Cloud Architecture",
        "UX Research",
    ],
}

SKILL_CATEGORY_MAP: dict[str, str] = {
    "TigerGraph": "database",
    "Distributed Systems": "platform",
    "Performance Optimization": "tool",
    "FastAPI": "framework",
    "Database Design": "database",
    "Docker": "platform",
    "TypeScript": "language",
    "React": "framework",
    "GraphQL": "tool",
    "Product Strategy": "other",
    "LLM Ops": "platform",
    "Agile Leadership": "other",
    "UX Research": "other",
    "Cloud Architecture": "platform",
    "Design Systems": "other",
    "Framer Motion": "framework",
    "Figma API": "tool",
    "Python": "language",
    "Kubernetes": "platform",
}


def seed_skill_discovery_graph(client: TigerGraphClient) -> tuple[int, int]:
    """Upsert a dense role-skill-domain-trait-resource topology into DepGraph.

    Returns:
        Tuple of ``(node_count, edge_count)`` seeded.
    """
    skills = [
        SkillNode(name="TigerGraph", category="database", difficulty=4),
        SkillNode(name="Distributed Systems", category="platform", difficulty=5),
        SkillNode(name="Performance Optimization", category="tool", difficulty=4),
        SkillNode(name="FastAPI", category="framework", difficulty=2),
        SkillNode(name="Database Design", category="database", difficulty=3),
        SkillNode(name="Docker", category="platform", difficulty=2),
        SkillNode(name="TypeScript", category="language", difficulty=2),
        SkillNode(name="React", category="framework", difficulty=2),
        SkillNode(name="GraphQL", category="tool", difficulty=3),
        SkillNode(name="Product Strategy", category="other", difficulty=3),
        SkillNode(name="LLM Ops", category="platform", difficulty=4),
        SkillNode(name="Agile Leadership", category="other", difficulty=3),
        SkillNode(name="UX Research", category="other", difficulty=2),
        SkillNode(name="Cloud Architecture", category="platform", difficulty=4),
        SkillNode(name="Design Systems", category="other", difficulty=3),
        SkillNode(name="Framer Motion", category="framework", difficulty=2),
        SkillNode(name="Figma API", category="tool", difficulty=3),
        SkillNode(name="Python", category="language", difficulty=2),
        SkillNode(name="Kubernetes", category="platform", difficulty=3),
    ]

    roles = [RoleNode(name=role, level="mid") for role in ROLE_SKILL_MAP]

    domains = [
        DomainNode(name="backend-systems"),
        DomainNode(name="full-stack"),
        DomainNode(name="product"),
        DomainNode(name="design"),
        DomainNode(name="ai-systems"),
        DomainNode(name="leadership"),
    ]

    traits = [
        TraitNode(name="logical", trait_group="background"),
        TraitNode(name="creative", trait_group="background"),
        TraitNode(name="people", trait_group="background"),
        TraitNode(name="code", trait_group="solving"),
        TraitNode(name="ux", trait_group="solving"),
        TraitNode(name="strategy", trait_group="solving"),
        TraitNode(name="impact", trait_group="influence"),
        TraitNode(name="elegance", trait_group="influence"),
        TraitNode(name="creation", trait_group="influence"),
        TraitNode(name="startup", trait_group="intensity"),
        TraitNode(name="corporate", trait_group="intensity"),
        TraitNode(name="research", trait_group="intensity"),
        TraitNode(name="generalist", trait_group="breadth"),
        TraitNode(name="specialist", trait_group="breadth"),
    ]

    resources = [
        LearningResourceNode(
            id="res-tg-graph-modeling",
            title="TigerGraph Graph Modeling Playbook",
            resource_type="guide",
            url="https://docs.tigergraph.com/",
        ),
        LearningResourceNode(
            id="res-fastapi-production",
            title="FastAPI Production Patterns",
            resource_type="course",
            url="https://fastapi.tiangolo.com/",
        ),
        LearningResourceNode(
            id="res-react-architecture",
            title="React Architecture for Scale",
            resource_type="article",
            url="https://react.dev/",
        ),
        LearningResourceNode(
            id="res-llm-ops",
            title="Operational LLM Systems",
            resource_type="guide",
            url="https://python.langchain.com/",
        ),
        LearningResourceNode(
            id="res-product-strategy",
            title="Modern Product Strategy Toolkit",
            resource_type="book",
            url="https://www.svpg.com/",
        ),
        LearningResourceNode(
            id="res-design-systems",
            title="Design Systems Operations",
            resource_type="course",
            url="https://www.designsystems.com/",
        ),
        LearningResourceNode(
            id="res-distributed-systems",
            title="Distributed Systems Engineering Handbook",
            resource_type="book",
            url="https://example.com/distributed-systems",
        ),
        LearningResourceNode(
            id="res-cloud-architecture",
            title="Cloud Architecture Patterns",
            resource_type="guide",
            url="https://example.com/cloud-architecture",
        ),
    ]

    libs = [
        LibNode(name="pyTigerGraph", version="", ecosystem="pip"),
        LibNode(name="fastapi", version="", ecosystem="pip"),
        LibNode(name="react", version="", ecosystem="npm"),
        LibNode(name="typescript", version="", ecosystem="npm"),
        LibNode(name="framer-motion", version="", ecosystem="npm"),
        LibNode(name="langchain", version="", ecosystem="pip"),
        LibNode(name="docker", version="", ecosystem="other"),
        LibNode(name="kubernetes", version="", ecosystem="other"),
        LibNode(name="graphql", version="", ecosystem="npm"),
        LibNode(name="pydantic", version="", ecosystem="pip"),
        LibNode(name="d3", version="", ecosystem="npm"),
        LibNode(name="vite", version="", ecosystem="npm"),
        LibNode(name="redis", version="", ecosystem="other"),
        LibNode(name="postgresql", version="", ecosystem="other"),
        LibNode(name="numpy", version="", ecosystem="pip"),
    ]

    files = [
        FileNode(path="backend/app/api/routes/discovery.py", repo="recruitgraph", language="python"),
        FileNode(path="backend/app/services/skill_discovery_seed.py", repo="recruitgraph", language="python"),
        FileNode(path="backend/app/services/tigergraph_client.py", repo="recruitgraph", language="python"),
        FileNode(path="backend/app/models/discovery_models.py", repo="recruitgraph", language="python"),
        FileNode(path="backend/app/services/llm_extractor.py", repo="recruitgraph", language="python"),
        FileNode(path="backend/app/services/github_parser.py", repo="recruitgraph", language="python"),
        FileNode(path="frontend/src/pages/WhatToChoosePage.tsx", repo="recruitgraph", language="typescript"),
        FileNode(path="frontend/src/components/dashboard/SkillQuiz.tsx", repo="recruitgraph", language="typescript"),
        FileNode(path="frontend/src/components/dashboard/SkillGraphNetwork.tsx", repo="recruitgraph", language="typescript"),
        FileNode(path="frontend/src/components/dashboard/TopSkills.tsx", repo="recruitgraph", language="typescript"),
        FileNode(path="frontend/src/hooks/useSkillDiscovery.ts", repo="recruitgraph", language="typescript"),
        FileNode(path="frontend/src/api/discoveryApi.ts", repo="recruitgraph", language="typescript"),
    ]

    discovery_edges: list[DepEdge] = []
    dep_edges: list[DepEdge] = []

    seen_discovery: set[tuple[str, str, str, str, str]] = set()
    seen_dep: set[tuple[str, str, str, str, str]] = set()

    def add_discovery_edge(
        edge_type: str,
        src_type: str,
        src_id: str,
        tgt_type: str,
        tgt_id: str,
        attrs: dict[str, int | float | bool | str],
    ) -> None:
        key = (edge_type, src_type, src_id, tgt_type, tgt_id)
        if key in seen_discovery:
            return
        seen_discovery.add(key)
        discovery_edges.append(
            DepEdge(
                edge_type=edge_type,
                src_type=src_type,
                src_id=src_id,
                tgt_type=tgt_type,
                tgt_id=tgt_id,
                attrs=attrs,
            )
        )

    def add_dep_edge(
        edge_type: str,
        src_type: str,
        src_id: str,
        tgt_type: str,
        tgt_id: str,
        attrs: dict[str, int | float | bool | str],
    ) -> None:
        key = (edge_type, src_type, src_id, tgt_type, tgt_id)
        if key in seen_dep:
            return
        seen_dep.add(key)
        dep_edges.append(
            DepEdge(
                edge_type=edge_type,
                src_type=src_type,
                src_id=src_id,
                tgt_type=tgt_type,
                tgt_id=tgt_id,
                attrs=attrs,
            )
        )

    role_skill_union: dict[str, set[str]] = {
        role_name: set(role_skills) for role_name, role_skills in ROLE_SKILL_MAP.items()
    }

    # Role -> required skill edges.
    for role_name, role_skills in ROLE_SKILL_MAP.items():
        for idx, skill_name in enumerate(role_skills):
            weight = round(max(0.45, 1.0 - idx * 0.09), 2)
            role_skill_union.setdefault(role_name, set()).add(skill_name)
            add_discovery_edge(
                "ROLE_REQUIRES_SKILL",
                "RoleNode",
                role_name,
                "SkillNode",
                skill_name,
                {"weight": weight},
            )

    # Add shared bridge skills to every role to increase overlap.
    bridge_skills = ["Python", "GraphQL", "Kubernetes"]
    for role_name, role_skills in ROLE_SKILL_MAP.items():
        for idx, skill_name in enumerate(bridge_skills):
            if skill_name in role_skills:
                continue
            weight = round(max(0.42, 0.6 - idx * 0.07), 2)
            role_skill_union.setdefault(role_name, set()).add(skill_name)
            add_discovery_edge(
                "ROLE_REQUIRES_SKILL",
                "RoleNode",
                role_name,
                "SkillNode",
                skill_name,
                {"weight": weight},
            )

    # Trait -> role alignment edges from quiz dimensions.
    trait_role_weights: list[tuple[str, str, float]] = [
        ("logical", "Graph Database & Backend Researcher", 0.93),
        ("logical", "Full-Stack Solutions Architect", 0.68),
        ("creative", "Creative Frontend Engineer", 0.92),
        ("creative", "Design Systems Architect", 0.88),
        ("people", "AI Product Lead", 0.91),
        ("people", "Technical Generalist / PM", 0.82),
        ("code", "Graph Database & Backend Researcher", 0.88),
        ("code", "Full-Stack Solutions Architect", 0.9),
        ("ux", "Creative Frontend Engineer", 0.85),
        ("ux", "Design Systems Architect", 0.92),
        ("strategy", "AI Product Lead", 0.94),
        ("strategy", "Technical Generalist / PM", 0.86),
        ("impact", "AI Product Lead", 0.87),
        ("elegance", "Design Systems Architect", 0.84),
        ("creation", "Creative Frontend Engineer", 0.82),
        ("startup", "Full-Stack Solutions Architect", 0.76),
        ("corporate", "AI Product Lead", 0.74),
        ("research", "Graph Database & Backend Researcher", 0.9),
        ("generalist", "Technical Generalist / PM", 0.93),
        ("specialist", "Graph Database & Backend Researcher", 0.85),
        ("specialist", "Design Systems Architect", 0.79),
    ]

    for trait_name, role_name, weight in trait_role_weights:
        add_discovery_edge(
            "TRAIT_ALIGNS_ROLE",
            "TraitNode",
            trait_name,
            "RoleNode",
            role_name,
            {"weight": weight},
        )

    # Add broad low-weight trait links so every trait can reach every role.
    for trait in traits:
        for role in roles:
            add_discovery_edge(
                "TRAIT_ALIGNS_ROLE",
                "TraitNode",
                trait.name,
                "RoleNode",
                role.name,
                {"weight": 0.44},
            )

    # Trait -> skill overlays derived from high-confidence trait-role signals.
    for trait_name, role_name, role_weight in sorted(
        trait_role_weights,
        key=lambda item: item[2],
        reverse=True,
    ):
        for skill_name in sorted(role_skill_union.get(role_name, set())):
            trait_skill_weight = round(max(0.45, min(0.94, role_weight * 0.86)), 2)
            add_discovery_edge(
                "TRAIT_RELATES_TO_SKILL",
                "TraitNode",
                trait_name,
                "SkillNode",
                skill_name,
                {"weight": trait_skill_weight},
            )

    # Seed skill affinity graph.
    related_skill_pairs: list[tuple[str, str, float]] = [
        ("TigerGraph", "Distributed Systems", 0.88),
        ("Distributed Systems", "Performance Optimization", 0.9),
        ("FastAPI", "Python", 0.87),
        ("TypeScript", "React", 0.91),
        ("React", "Design Systems", 0.79),
        ("Design Systems", "Figma API", 0.84),
        ("Product Strategy", "Agile Leadership", 0.86),
        ("LLM Ops", "Product Strategy", 0.74),
        ("Docker", "Kubernetes", 0.83),
        ("Database Design", "GraphQL", 0.76),
        ("Cloud Architecture", "Kubernetes", 0.8),
        ("UX Research", "Product Strategy", 0.72),
        ("GraphQL", "TypeScript", 0.67),
        ("TigerGraph", "Database Design", 0.83),
        ("FastAPI", "Distributed Systems", 0.78),
    ]

    for left, right, affinity in related_skill_pairs:
        add_discovery_edge(
            "SKILL_RELATES_TO_SKILL",
            "SkillNode",
            left,
            "SkillNode",
            right,
            {"affinity": affinity},
        )
        add_discovery_edge(
            "SKILL_RELATES_TO_SKILL",
            "SkillNode",
            right,
            "SkillNode",
            left,
            {"affinity": affinity},
        )

    # Add same-category dense links.
    skills_by_category: dict[str, list[str]] = {}
    for skill in skills:
        skills_by_category.setdefault(skill.category, []).append(skill.name)

    for category, category_skills in skills_by_category.items():
        if len(category_skills) < 2:
            continue
        base_affinity = 0.71 if category in {"platform", "framework", "database"} else 0.64
        for i, left in enumerate(category_skills):
            for right in category_skills[i + 1:]:
                add_discovery_edge(
                    "SKILL_RELATES_TO_SKILL",
                    "SkillNode",
                    left,
                    "SkillNode",
                    right,
                    {"affinity": base_affinity},
                )
                add_discovery_edge(
                    "SKILL_RELATES_TO_SKILL",
                    "SkillNode",
                    right,
                    "SkillNode",
                    left,
                    {"affinity": base_affinity},
                )

    domain_by_skill: dict[str, list[str]] = {
        "TigerGraph": ["backend-systems", "ai-systems"],
        "Distributed Systems": ["backend-systems", "ai-systems"],
        "Performance Optimization": ["backend-systems", "full-stack"],
        "FastAPI": ["backend-systems", "full-stack"],
        "Database Design": ["backend-systems", "full-stack"],
        "Docker": ["backend-systems", "ai-systems"],
        "TypeScript": ["full-stack", "design"],
        "React": ["full-stack", "design"],
        "GraphQL": ["full-stack", "backend-systems"],
        "Cloud Architecture": ["ai-systems", "backend-systems"],
        "LLM Ops": ["ai-systems", "product"],
        "Product Strategy": ["product", "leadership"],
        "Agile Leadership": ["leadership", "product"],
        "UX Research": ["design", "product"],
        "Design Systems": ["design", "full-stack"],
        "Framer Motion": ["design", "full-stack"],
        "Figma API": ["design", "full-stack"],
        "Python": ["backend-systems", "ai-systems"],
        "Kubernetes": ["backend-systems", "ai-systems"],
    }

    for skill_name, domain_names in domain_by_skill.items():
        for domain_name in domain_names:
            add_discovery_edge(
                "SKILL_IN_DOMAIN",
                "SkillNode",
                skill_name,
                "DomainNode",
                domain_name,
                {},
            )

    role_domain_hits: dict[tuple[str, str], int] = {}
    for role_name, skill_names in role_skill_union.items():
        for skill_name in skill_names:
            for domain_name in domain_by_skill.get(skill_name, []):
                key = (role_name, domain_name)
                role_domain_hits[key] = role_domain_hits.get(key, 0) + 1

    for (role_name, domain_name), hit_count in role_domain_hits.items():
        total_skills = max(1, len(role_skill_union.get(role_name, set())))
        fit = round(min(0.95, max(0.45, hit_count / total_skills + 0.36)), 2)
        add_discovery_edge(
            "ROLE_IN_DOMAIN",
            "RoleNode",
            role_name,
            "DomainNode",
            domain_name,
            {"fit": fit},
        )

    domain_pair_hits: dict[tuple[str, str], int] = {}
    for domain_names in domain_by_skill.values():
        unique_domains = sorted(set(domain_names))
        for i, left in enumerate(unique_domains):
            for right in unique_domains[i + 1:]:
                key = (left, right)
                domain_pair_hits[key] = domain_pair_hits.get(key, 0) + 1

    for (left, right), hit_count in domain_pair_hits.items():
        affinity = round(min(0.92, 0.57 + hit_count * 0.11), 2)
        add_discovery_edge(
            "DOMAIN_RELATES_TO_DOMAIN",
            "DomainNode",
            left,
            "DomainNode",
            right,
            {"affinity": affinity},
        )
        add_discovery_edge(
            "DOMAIN_RELATES_TO_DOMAIN",
            "DomainNode",
            right,
            "DomainNode",
            left,
            {"affinity": affinity},
        )

    resource_skills: list[tuple[str, str, float]] = [
        ("res-tg-graph-modeling", "TigerGraph", 0.95),
        ("res-tg-graph-modeling", "Distributed Systems", 0.68),
        ("res-fastapi-production", "FastAPI", 0.93),
        ("res-fastapi-production", "Python", 0.74),
        ("res-react-architecture", "React", 0.91),
        ("res-react-architecture", "TypeScript", 0.7),
        ("res-llm-ops", "LLM Ops", 0.94),
        ("res-product-strategy", "Product Strategy", 0.9),
        ("res-product-strategy", "Agile Leadership", 0.73),
        ("res-design-systems", "Design Systems", 0.92),
        ("res-design-systems", "Figma API", 0.82),
        ("res-distributed-systems", "Distributed Systems", 0.95),
        ("res-distributed-systems", "Kubernetes", 0.78),
        ("res-cloud-architecture", "Cloud Architecture", 0.95),
        ("res-cloud-architecture", "Docker", 0.81),
    ]

    for resource_id, skill_name, strength in resource_skills:
        add_discovery_edge(
            "RESOURCE_TEACHES_SKILL",
            "LearningResourceNode",
            resource_id,
            "SkillNode",
            skill_name,
            {"strength": strength},
        )

    for resource_id, skill_name, strength in sorted(
        resource_skills,
        key=lambda item: item[2],
        reverse=True,
    ):
        for domain_name in domain_by_skill.get(skill_name, []):
            domain_strength = round(max(0.45, min(0.92, strength * 0.9)), 2)
            add_discovery_edge(
                "RESOURCE_IN_DOMAIN",
                "LearningResourceNode",
                resource_id,
                "DomainNode",
                domain_name,
                {"strength": domain_strength},
            )

    skill_lib_map: list[tuple[str, str, float]] = [
        ("TigerGraph", "pyTigerGraph", 0.96),
        ("FastAPI", "fastapi", 0.94),
        ("React", "react", 0.95),
        ("TypeScript", "typescript", 0.93),
        ("Framer Motion", "framer-motion", 0.92),
        ("LLM Ops", "langchain", 0.82),
        ("GraphQL", "graphql", 0.86),
        ("Docker", "docker", 0.9),
        ("Kubernetes", "kubernetes", 0.88),
        ("Database Design", "postgresql", 0.87),
        ("UX Research", "d3", 0.63),
        ("Design Systems", "vite", 0.59),
        ("Agile Leadership", "redis", 0.55),
        ("Performance Optimization", "numpy", 0.61),
        ("Python", "pydantic", 0.77),
    ]

    for skill_name, lib_name, relevance in skill_lib_map:
        add_discovery_edge(
            "SKILL_USES_LIB",
            "SkillNode",
            skill_name,
            "LibNode",
            lib_name,
            {"relevance": relevance},
        )

    category_libs: dict[str, list[str]] = {
        "language": ["typescript", "pydantic", "numpy"],
        "framework": ["react", "fastapi", "vite", "framer-motion"],
        "database": ["pyTigerGraph", "postgresql", "redis"],
        "platform": ["docker", "kubernetes", "langchain"],
        "tool": ["graphql", "d3", "numpy"],
        "other": ["redis", "d3", "vite"],
    }
    for skill in skills:
        for idx, lib_name in enumerate(category_libs.get(skill.category, ["redis", "d3"])):
            relevance = round(max(0.5, 0.78 - idx * 0.09), 2)
            add_discovery_edge(
                "SKILL_USES_LIB",
                "SkillNode",
                skill.name,
                "LibNode",
                lib_name,
                {"relevance": relevance},
            )

    skill_to_libs: dict[str, dict[str, float]] = {}
    lib_to_skills: dict[str, set[str]] = {}
    for edge in discovery_edges:
        if edge.edge_type != "SKILL_USES_LIB":
            continue
        relevance = edge.attrs.get("relevance", 0.5)
        try:
            relevance_value = float(relevance)
        except (TypeError, ValueError):
            relevance_value = 0.5

        skill_to_libs.setdefault(edge.src_id, {})[edge.tgt_id] = max(
            relevance_value,
            skill_to_libs.setdefault(edge.src_id, {}).get(edge.tgt_id, 0.0),
        )
        lib_to_skills.setdefault(edge.tgt_id, set()).add(edge.src_id)

    for role_name, skill_names in role_skill_union.items():
        lib_scores: dict[str, float] = {}
        for skill_name in skill_names:
            for lib_name, relevance in skill_to_libs.get(skill_name, {}).items():
                lib_scores[lib_name] = max(lib_scores.get(lib_name, 0.0), relevance)

        for lib_name, relevance in sorted(
            lib_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:10]:
            add_discovery_edge(
                "ROLE_USES_LIB",
                "RoleNode",
                role_name,
                "LibNode",
                lib_name,
                {"relevance": round(max(0.45, min(0.96, relevance)), 2)},
            )

    file_import_map: dict[str, list[str]] = {
        "backend/app/api/routes/discovery.py": ["fastapi", "pyTigerGraph", "pydantic", "redis"],
        "backend/app/services/skill_discovery_seed.py": ["pyTigerGraph", "numpy", "redis"],
        "backend/app/services/tigergraph_client.py": ["pyTigerGraph", "pydantic", "postgresql"],
        "backend/app/models/discovery_models.py": ["pydantic", "fastapi"],
        "backend/app/services/llm_extractor.py": ["langchain", "pydantic", "redis"],
        "backend/app/services/github_parser.py": ["fastapi", "numpy", "postgresql"],
        "frontend/src/pages/WhatToChoosePage.tsx": ["react", "typescript", "d3"],
        "frontend/src/components/dashboard/SkillQuiz.tsx": ["react", "typescript", "vite"],
        "frontend/src/components/dashboard/SkillGraphNetwork.tsx": ["react", "d3", "typescript"],
        "frontend/src/components/dashboard/TopSkills.tsx": ["react", "typescript", "vite"],
        "frontend/src/hooks/useSkillDiscovery.ts": ["react", "typescript", "graphql"],
        "frontend/src/api/discoveryApi.ts": ["typescript", "graphql", "react"],
    }
    for path, imported_libs in file_import_map.items():
        for idx, lib in enumerate(imported_libs):
            add_dep_edge(
                "IMPORTS",
                "FileNode",
                path,
                "LibNode",
                lib,
                {"import_count": max(1, 3 - idx)},
            )

        linked_skills: set[str] = set()
        for lib_idx, lib_name in enumerate(imported_libs):
            candidate_skills = sorted(lib_to_skills.get(lib_name, set()))
            for skill_idx, skill_name in enumerate(candidate_skills[:6]):
                if skill_name in linked_skills:
                    continue
                relevance = round(max(0.42, 0.9 - lib_idx * 0.08 - skill_idx * 0.05), 2)
                add_dep_edge(
                    "FILE_SUPPORTS_SKILL",
                    "FileNode",
                    path,
                    "SkillNode",
                    skill_name,
                    {"relevance": relevance},
                )
                linked_skills.add(skill_name)

    file_paths = [file.path for file in files]
    for i, src in enumerate(file_paths):
        tgt_primary = file_paths[(i + 1) % len(file_paths)]
        tgt_secondary = file_paths[(i + 3) % len(file_paths)]
        add_dep_edge("CALLS", "FileNode", src, "FileNode", tgt_primary, {})
        add_dep_edge("CALLS", "FileNode", src, "FileNode", tgt_secondary, {})

    lib_names = [lib.name for lib in libs]
    for i, src in enumerate(lib_names):
        tgt_primary = lib_names[(i + 1) % len(lib_names)]
        tgt_secondary = lib_names[(i + 2) % len(lib_names)]
        add_dep_edge(
            "LIB_DEPENDS_ON",
            "LibNode",
            src,
            "LibNode",
            tgt_primary,
            {"is_dev_dep": False},
        )
        add_dep_edge(
            "LIB_DEPENDS_ON",
            "LibNode",
            src,
            "LibNode",
            tgt_secondary,
            {"is_dev_dep": True},
        )

    client.upsert_dep_graph(files=files, libs=libs, edges=dep_edges)
    client.upsert_skill_graph(
        skills=skills,
        roles=roles,
        domains=domains,
        traits=traits,
        resources=resources,
        edges=discovery_edges,
    )

    node_count = (
        len(skills)
        + len(roles)
        + len(domains)
        + len(traits)
        + len(resources)
        + len(libs)
        + len(files)
    )
    edge_count = len(discovery_edges) + len(dep_edges)

    logger.info(
        "Seeded discovery graph with %d nodes and %d edges.",
        node_count,
        edge_count,
    )
    return node_count, edge_count
