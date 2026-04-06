"""Curated famous-person PersonGraph extension for demo and startup seeding.

Contains:
  - 10 profiles with real LinkedIn IDs (as provided by product requirements).
    - 90 profiles with realistic mock LinkedIn IDs in firstname-lastname-company format.
  - Realistic synthetic connection weights for BFS reachability and alternative paths.
"""

from __future__ import annotations

from collections import deque
import hashlib
import re
from dataclasses import dataclass


@dataclass(slots=True)
class FamousPerson:
    """Person record compatible with path module summary mapping."""

    id: str
    name: str
    linkedin_url: str
    headline: str
    company: str
    mutual_count: int = 0


def _token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _mock_id(name: str, company: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return f"unknown-{_token(company)}"
    first = _token(parts[0])
    last = _token(parts[-1])
    return f"{first}-{last}-{_token(company)}"


def _score(a: str, b: str, low: int, high: int) -> int:
    """Stable pseudo-random score in [low, high] based on pair IDs."""
    if low >= high:
        return low
    key = "::".join(sorted([a, b]))
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)
    return low + (h % (high - low + 1))


_REAL_PROFILES: list[tuple[str, str, str, str]] = [
    ("Jensen Huang", "jenhsunhuang", "Founder & CEO at NVIDIA", "NVIDIA"),
    ("Patrick Collison", "patrickcollison", "Co-Founder & CEO at Stripe", "Stripe"),
    ("John Collison", "johnbcollison", "President at Stripe", "Stripe"),
    ("Dario Amodei", "dario-amodei-3934934", "CEO at Anthropic", "Anthropic"),
    ("Daniela Amodei", "daniela-amodei-790bb22a", "President at Anthropic", "Anthropic"),
    ("Reid Hoffman", "reidhoffman", "Co-Founder at LinkedIn", "LinkedIn"),
    ("Brian Chesky", "brianchesky", "Co-Founder & CEO at Airbnb", "Airbnb"),
    ("Tobias Lutke", "tobiaslutke", "Co-Founder & CEO at Shopify", "Shopify"),
    ("Aravind Srinivas", "aravind-srinivas-16051987", "Co-Founder & CEO at Perplexity", "Perplexity"),
    ("Dylan Field", "dylanfield", "Co-Founder & CEO at Figma", "Figma"),
]

# Requested 90 additional top founders/CEOs with mock IDs.
_MOCK_PROFILES: list[tuple[str, str, str]] = [
    ("Sam Altman", "OpenAI", "CEO at OpenAI"),
    ("Satya Nadella", "Microsoft", "Chairman & CEO at Microsoft"),
    ("Sundar Pichai", "Google", "CEO at Google"),
    ("Mark Zuckerberg", "Meta", "Founder & CEO at Meta"),
    ("Andrej Karpathy", "Independent", "AI Researcher & Founder"),
    ("Garry Tan", "YCombinator", "President & CEO at Y Combinator"),
    ("Naval Ravikant", "AngelList", "Founder at AngelList"),
    ("Paul Graham", "YCombinator", "Co-Founder at Y Combinator"),
    ("Greg Brockman", "OpenAI", "Co-Founder at OpenAI"),
    ("Elon Musk", "Tesla", "CEO at Tesla & SpaceX"),
    ("Tim Cook", "Apple", "CEO at Apple"),
    ("Jeff Bezos", "Amazon", "Founder at Amazon"),
    ("Andy Jassy", "AWS", "CEO at Amazon"),
    ("Demis Hassabis", "DeepMind", "CEO at Google DeepMind"),
    ("Mustafa Suleyman", "MicrosoftAI", "CEO at Microsoft AI"),
    ("Travis Kalanick", "Uber", "Co-Founder at Uber"),
    ("Drew Houston", "Dropbox", "Co-Founder & CEO at Dropbox"),
    ("Stewart Butterfield", "Slack", "Co-Founder at Slack"),
    ("Ev Williams", "Twitter", "Co-Founder at Twitter"),
    ("Jack Dorsey", "Twitter", "Co-Founder at Twitter & Block"),
    ("Daniel Ek", "Spotify", "Co-Founder & CEO at Spotify"),
    ("Vlad Tenev", "Robinhood", "Co-Founder & CEO at Robinhood"),
    ("Baiju Bhatt", "Robinhood", "Co-Founder at Robinhood"),
    ("Zach Perret", "Plaid", "Co-Founder & CEO at Plaid"),
    ("Henrique Dubugras", "Brex", "Co-Founder at Brex"),
    ("Pedro Franceschi", "Brex", "Co-Founder at Brex"),
    ("Ivan Zhao", "Notion", "Co-Founder & CEO at Notion"),
    ("Emmett Shear", "Twitch", "Co-Founder at Twitch"),
    ("Logan Green", "Lyft", "Co-Founder at Lyft"),
    ("John Zimmer", "Lyft", "Co-Founder at Lyft"),
    ("Nikesh Arora", "PaloAltoNetworks", "CEO at Palo Alto Networks"),
    ("Arvind Krishna", "IBM", "Chairman & CEO at IBM"),
    ("Lisa Su", "AMD", "Chair & CEO at AMD"),
    ("Pat Gelsinger", "Intel", "CEO at Intel"),
    ("Marc Benioff", "Salesforce", "Chair & CEO at Salesforce"),
    ("Aaron Levie", "Box", "Co-Founder & CEO at Box"),
    ("Parker Conrad", "Rippling", "Co-Founder & CEO at Rippling"),
    ("Girish Mathrubootham", "Freshworks", "Founder & Executive Chair at Freshworks"),
    ("Nithin Kamath", "Zerodha", "Founder & CEO at Zerodha"),
    ("Vijay Shekhar Sharma", "Paytm", "Founder & CEO at Paytm"),
    ("Larry Page", "Alphabet", "Co-Founder at Google and Board Member at Alphabet"),
    ("Sergey Brin", "Alphabet", "Co-Founder at Google and Board Member at Alphabet"),
    ("Eric Yuan", "Zoom", "Founder & CEO at Zoom"),
    ("Brian Armstrong", "Coinbase", "Co-Founder & CEO at Coinbase"),
    ("Fred Ehrsam", "Paradigm", "Co-Founder at Coinbase and Co-Founder at Paradigm"),
    ("Melanie Perkins", "Canva", "Co-Founder & CEO at Canva"),
    ("Cliff Obrecht", "Canva", "Co-Founder & COO at Canva"),
    ("Tony Xu", "DoorDash", "Co-Founder & CEO at DoorDash"),
    ("Andy Fang", "DoorDash", "Co-Founder at DoorDash"),
    ("Stanley Tang", "DoorDash", "Co-Founder at DoorDash"),
    ("Apoorva Mehta", "Instacart", "Founder at Instacart"),
    ("Fidji Simo", "Instacart", "CEO at Instacart"),
    ("Whitney Wolfe Herd", "Bumble", "Founder at Bumble"),
    ("Daniel Dines", "UiPath", "Co-Founder & CEO at UiPath"),
    ("Nat Friedman", "NFDG", "Founder at NFDG and Former CEO at GitHub"),
    ("Arash Ferdowsi", "Dropbox", "Co-Founder at Dropbox"),
    ("Dustin Moskovitz", "Asana", "Co-Founder at Facebook and Co-Founder & CEO at Asana"),
    ("Justin Rosenstein", "Asana", "Co-Founder at Asana"),
    ("Sebastian Siemiatkowski", "Klarna", "Co-Founder & CEO at Klarna"),
    ("Nik Storonsky", "Revolut", "Co-Founder & CEO at Revolut"),
    ("Taavet Hinrikus", "Wise", "Co-Founder at Wise"),
    ("Kristo Kaarmann", "Wise", "Co-Founder & CEO at Wise"),
    ("Des Traynor", "Intercom", "Co-Founder at Intercom"),
    ("Eoghan McCabe", "Intercom", "Co-Founder at Intercom"),
    ("Hiten Shah", "Nira", "Co-Founder at Nira"),
    ("Jason Citron", "Discord", "Co-Founder & CEO at Discord"),
    ("Stanislav Vishnevskiy", "Discord", "Co-Founder & CTO at Discord"),
    ("David Baszucki", "Roblox", "Co-Founder & CEO at Roblox"),
    ("Ali Ghodsi", "Databricks", "Co-Founder & CEO at Databricks"),
    ("Matei Zaharia", "Databricks", "Co-Founder at Databricks"),
    ("Reynold Xin", "Databricks", "Co-Founder & Chief Architect at Databricks"),
    ("Andy Konwinski", "Databricks", "Co-Founder at Databricks"),
    ("Ben Silbermann", "Pinterest", "Co-Founder & Executive Chair at Pinterest"),
    ("Evan Sharp", "Pinterest", "Co-Founder at Pinterest"),
    ("Kevin Systrom", "Artifact", "Co-Founder at Instagram and Artifact"),
    ("Mike Krieger", "Anthropic", "Co-Founder at Instagram and CPO at Anthropic"),
    ("Jan Koum", "WhatsApp", "Co-Founder at WhatsApp"),
    ("Brian Acton", "Signal", "Co-Founder at WhatsApp and Executive Chair at Signal"),
    ("Adam DAngelo", "Quora", "Founder & CEO at Quora"),
    ("Alexandr Wang", "ScaleAI", "Founder & CEO at Scale AI"),
    ("Lucy Guo", "Passes", "Co-Founder at Scale AI and Founder at Passes"),
    ("Ritesh Agarwal", "OYO", "Founder & CEO at OYO"),
    ("Bhavish Aggarwal", "Ola", "Co-Founder at Ola and Founder at Krutrim"),
    ("Deepinder Goyal", "Zomato", "Founder & CEO at Zomato"),
    ("Nandan Nilekani", "Infosys", "Co-Founder at Infosys"),
    ("Narayana Murthy", "Infosys", "Co-Founder at Infosys"),
    ("Kunal Shah", "CRED", "Founder at CRED"),
    ("Harsh Jain", "Dream11", "Co-Founder & CEO at Dream11"),
    ("Harshil Mathur", "Razorpay", "Co-Founder & CEO at Razorpay"),
    ("Shashank Kumar", "Razorpay", "Co-Founder at Razorpay"),
]


def build_famous_people() -> list[FamousPerson]:
    """Return all famous profiles as Person-compatible records."""
    result: list[FamousPerson] = []

    for name, linkedin_id, headline, company in _REAL_PROFILES:
        famous_id = f"famous-{linkedin_id}"
        result.append(
            FamousPerson(
                id=famous_id,
                name=name,
                linkedin_url=f"https://www.linkedin.com/in/{linkedin_id}",
                headline=headline,
                company=company,
                mutual_count=45,
            )
        )

    for name, company, headline in _MOCK_PROFILES:
        pid = f"famous-{_mock_id(name, company)}"
        result.append(
            FamousPerson(
                id=pid,
                name=name,
                linkedin_url=f"https://www.linkedin.com/in/{pid}",
                headline=headline,
                company=company,
                mutual_count=28,
            )
        )

    return result


FAMOUS_PEOPLE: list[FamousPerson] = build_famous_people()
FAMOUS_INDEX: dict[str, FamousPerson] = {p.id: p for p in FAMOUS_PEOPLE}
for person in FAMOUS_PEOPLE:
    slug = person.linkedin_url.rstrip("/").rsplit("/in/", 1)[-1].split("?")[0].lower()
    FAMOUS_INDEX.setdefault(slug, person)
FAMOUS_INDEX_BY_URL: dict[str, FamousPerson] = {
    p.linkedin_url.rstrip("/").lower(): p for p in FAMOUS_PEOPLE
}

MIN_FAMOUS_HOPS = 5
MAX_FAMOUS_HOPS = 12


def _id_by_name() -> dict[str, str]:
    return {p.name: p.id for p in FAMOUS_PEOPLE}


def _bfs_distances(adjacency: dict[str, set[str]], src_id: str) -> dict[str, int]:
    """Return shortest hop distance from src_id to every reachable node."""
    if src_id not in adjacency:
        return {}

    dist: dict[str, int] = {src_id: 0}
    q: deque[str] = deque([src_id])
    while q:
        cur = q.popleft()
        for nxt in adjacency.get(cur, set()):
            if nxt in dist:
                continue
            dist[nxt] = dist[cur] + 1
            q.append(nxt)
    return dist


def _nearest_available_depth(
    desired_depth: int,
    depth_buckets: dict[int, list[str]],
) -> int | None:
    """Pick the nearest available depth bucket to the desired depth."""
    if not depth_buckets:
        return None

    min_depth = MIN_FAMOUS_HOPS - 1
    max_depth = MAX_FAMOUS_HOPS - 1
    desired = max(min_depth, min(max_depth, desired_depth))

    for delta in range(0, max_depth - min_depth + 1):
        lower = desired - delta
        upper = desired + delta
        if lower in depth_buckets:
            return lower
        if upper in depth_buckets:
            return upper
    return None


def _target_hop_for_index(index: int) -> int:
    """Cycle famous profiles across hop targets in [MIN_FAMOUS_HOPS, MAX_FAMOUS_HOPS]."""
    span = (MAX_FAMOUS_HOPS - MIN_FAMOUS_HOPS) + 1
    return MIN_FAMOUS_HOPS + (index % span)


def build_famous_edges(mock_people: list) -> list[tuple[str, str, int]]:
    """Build realistic synthetic CONNECTED_TO edges.

    Returns undirected edges as tuples: (src_id, tgt_id, mutual_count).
    """
    ids = _id_by_name()
    edge_map: dict[frozenset[str], int] = {}
    target_hops_by_id = {
        person.id: _target_hop_for_index(i)
        for i, person in enumerate(FAMOUS_PEOPLE)
    }

    def add_by_name(a_name: str, b_name: str, low: int, high: int) -> None:
        a = ids.get(a_name)
        b = ids.get(b_name)
        if not a or not b or a == b:
            return
        add_by_id(a, b, low, high)

    def add_by_id(a: str, b: str, low: int, high: int) -> None:
        if not a or not b or a == b:
            return

        # Keep famous-to-famous edges within the same hop band so we preserve
        # the intended 5..12 hop spread from the caller node.
        if a in target_hops_by_id and b in target_hops_by_id:
            if target_hops_by_id[a] != target_hops_by_id[b]:
                return

        key = frozenset({a, b})
        edge_map[key] = max(edge_map.get(key, 0), _score(a, b, low, high))

    strong_pairs = [
        ("Patrick Collison", "John Collison", 44, 50),
        ("Dario Amodei", "Daniela Amodei", 40, 48),
        ("Vlad Tenev", "Baiju Bhatt", 36, 46),
        ("Henrique Dubugras", "Pedro Franceschi", 36, 46),
        ("Logan Green", "John Zimmer", 36, 46),
        ("Sam Altman", "Greg Brockman", 34, 45),
        ("Brian Chesky", "Reid Hoffman", 18, 30),
        ("Paul Graham", "Garry Tan", 30, 40),
        ("Sundar Pichai", "Demis Hassabis", 24, 36),
        ("Satya Nadella", "Mustafa Suleyman", 24, 36),
        ("Jensen Huang", "Lisa Su", 16, 28),
        ("Jensen Huang", "Pat Gelsinger", 14, 24),
        ("Elon Musk", "Jeff Bezos", 10, 18),
        ("Jack Dorsey", "Ev Williams", 26, 36),
        ("Marc Benioff", "Reid Hoffman", 14, 26),
        ("Dylan Field", "Mark Zuckerberg", 10, 20),
        ("Aravind Srinivas", "Sam Altman", 10, 18),
    ]
    for a, b, low, high in strong_pairs:
        add_by_name(a, b, low, high)

    company_groups: list[tuple[list[str], int, int]] = [
        (["Patrick Collison", "John Collison"], 24, 40),
        (["Dario Amodei", "Daniela Amodei", "Sam Altman", "Greg Brockman", "Andrej Karpathy", "Emmett Shear"], 16, 30),
        (["Sundar Pichai", "Demis Hassabis"], 18, 30),
        (["Satya Nadella", "Mustafa Suleyman"], 18, 30),
        (["Vlad Tenev", "Baiju Bhatt"], 22, 34),
        (["Henrique Dubugras", "Pedro Franceschi"], 22, 34),
        (["Logan Green", "John Zimmer"], 22, 34),
        (["Paul Graham", "Garry Tan", "Sam Altman", "Drew Houston", "Patrick Collison", "John Collison"], 12, 22),
        (["Jeff Bezos", "Andy Jassy"], 16, 30),
        (["Mark Zuckerberg", "Reid Hoffman", "Brian Chesky"], 10, 20),
    ]

    for members, low, high in company_groups:
        valid_ids = [ids[m] for m in members if m in ids]
        for i, src in enumerate(valid_ids):
            for tgt in valid_ids[i + 1 :]:
                add_by_id(src, tgt, low, high)

    bridge_pairs = [
        ("Sam Altman", "Reid Hoffman", 12, 24),
        ("Sam Altman", "Brian Chesky", 8, 16),
        ("Satya Nadella", "Sundar Pichai", 8, 16),
        ("Satya Nadella", "Arvind Krishna", 8, 16),
        ("Sundar Pichai", "Mark Zuckerberg", 8, 16),
        ("Elon Musk", "Mark Zuckerberg", 8, 14),
        ("Tim Cook", "Sundar Pichai", 8, 14),
        ("Marc Benioff", "Satya Nadella", 8, 16),
        ("Jensen Huang", "Satya Nadella", 12, 22),
        ("Jensen Huang", "Sundar Pichai", 10, 20),
        ("Daniel Ek", "Stewart Butterfield", 8, 16),
        ("Ivan Zhao", "Dylan Field", 8, 16),
        ("Parker Conrad", "Henrique Dubugras", 8, 16),
        ("Nithin Kamath", "Vijay Shekhar Sharma", 8, 16),
    ]
    for a, b, low, high in bridge_pairs:
        add_by_name(a, b, low, high)

    # Distance-aware famous-to-mock attachments: every famous profile is
    # attached so shortest path from the caller is in [5, 12] hops.
    from app.data.mock_graph import ADJACENCY, L0_CALLER

    mock_dist = _bfs_distances(ADJACENCY, L0_CALLER.id)
    depth_buckets: dict[int, list[str]] = {}
    for pid, depth in mock_dist.items():
        if (MIN_FAMOUS_HOPS - 1) <= depth <= (MAX_FAMOUS_HOPS - 1):
            depth_buckets.setdefault(depth, []).append(pid)

    for bucket in depth_buckets.values():
        bucket.sort()

    def pick_anchor(person_id: str, desired_depth: int, salt: str) -> str | None:
        depth = _nearest_available_depth(desired_depth, depth_buckets)
        if depth is None:
            return None
        pool = depth_buckets[depth]
        if not pool:
            return None
        idx = _score(person_id, f"{salt}-{depth}", 0, len(pool) - 1)
        return pool[idx]

    for person in FAMOUS_PEOPLE:
        target_hops = target_hops_by_id[person.id]
        primary_depth = target_hops - 1
        secondary_depth = min(MAX_FAMOUS_HOPS - 1, target_hops)

        a1 = pick_anchor(person.id, primary_depth, "primary")
        a2 = pick_anchor(person.id, secondary_depth, "secondary")

        if a1 is not None:
            add_by_id(person.id, a1, 1, 3)
        if a2 is not None and a2 != a1:
            add_by_id(person.id, a2, 1, 3)

    edges: list[tuple[str, str, int]] = []
    for key, mutual in edge_map.items():
        src, tgt = sorted(key)
        edges.append((src, tgt, mutual))
    return edges


def build_famous_adjacency(mock_people: list) -> dict[str, set[str]]:
    """Adjacency derived from famous edges for demo-mode alternative path search."""
    adj: dict[str, set[str]] = {}
    for src, tgt, _ in build_famous_edges(mock_people):
        adj.setdefault(src, set()).add(tgt)
        adj.setdefault(tgt, set()).add(src)
    return adj
