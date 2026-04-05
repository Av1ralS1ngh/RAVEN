"""Mock LinkedIn graph — Extensively layered topology for 5 to 12 hops.

Used when DEMO_MODE is true to bypass LinkedIn scraping, natively queried via TigerGraph.
Layers are structured progressively from IIT Roorkee to Silicon Valley.
Founders are intentionally staggered across Layer 5, Layer 8, and Layer 12
to guarantee varied path lengths between 5 to 12 hops.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass

@dataclass
class MockPerson:
    id: str
    name: str
    linkedin_url: str
    headline: str
    company: str
    mutual_count: int = 0


def _hash(seed: str, max_val: int) -> int:
    return int(hashlib.md5(seed.encode()).hexdigest(), 16) % max_val

# ── Layer 0: The Caller ──────────────────────────────────────────────────────
L0_CALLER = MockPerson(
    id="aviral-singh-b854a6342",
    name="Aviral Singh",
    linkedin_url="https://www.linkedin.com/in/aviral-singh-b854a6342",
    headline="Computer Science Undergrad at IIT Roorkee",
    company="IIT Roorkee",
    mutual_count=0
)

# ── Generative Names ─────────────────────────────────────────────────────────
_IND_FIRST = ["Aarav","Vivaan","Aditya","Vihaan"," अर्जुन","Sai","Reyansh","Krishna","Ishan","Shaurya",
              "Anya","Diya","Priya","Anjali","Neha","Kavya","Ishita","Riya","Sneha","Vidya",
              "Rohan","Rahul","Nikhil","Pranav","Aryan", "Arjun", "Karan", "Siddharth", "Aman", "Rishabh",
              "Pooja", "Maya", "Ayesha", "Kriti", "Shruti", "Akshay", "Vikram", "Tarun", "Nishant", "Raj",
              "Divya", "Swati", "Nidhi", "Garima", "Megha"]
_IND_LAST  = ["Sharma","Patel","Singh","Kumar","Gupta","Desai","Mehta","Reddy","Joshi","Verma",
              "Choudhury","Yadav","Thakur","Nair","Menon", "Jain", "Agrawal", "Bansal", "Goel", "Garg",
              "Mishra", "Pandey", "Shukla", "Tiwari", "Dubey", "Sen", "Das", "Bose", "Dutta", "Mukherjee"]

_US_FIRST = ["James","Michael","Robert","John","David","William","Richard","Joseph","Thomas","Charles",
             "Mary","Patricia","Jennifer","Linda","Elizabeth","Barbara","Susan","Jessica","Sarah","Karen",
             "Brian","Kevin","Jason","Matthew","Gary","Timothy","Jose","Larry","Jeffrey","Frank",
             "Alex", "Chris", "Ryan", "Eric", "Justin", "Brandon", "Tyler", "Aaron", "Daniel", "Mark",
             "Emily", "Ashley", "Amanda", "Melissa", "Stephanie", "Nicole", "Rachel", "Lauren", "Megan", "BrittANY"]
_US_LAST  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
             "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
             "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]

def make_person(idx: int, prefix: str, is_ind: bool, headline: str, comp: str, mut_base: int) -> MockPerson:
    seed = f"{prefix}-{idx}-v2"
    fs = _IND_FIRST if is_ind else _US_FIRST
    ls = _IND_LAST if is_ind else _US_LAST
    f = fs[_hash(seed+"f", len(fs))]
    l = ls[_hash(seed+"l", len(ls))]
    slug = f"{f.lower()}-{l.lower()}-{idx}-{prefix}"
    return MockPerson(
        id=slug,
        name=f"{f} {l}",
        linkedin_url=f"https://www.linkedin.com/in/{slug}",
        headline=f"{headline} at {comp}" if comp not in headline else headline,
        company=comp,
        mutual_count=mut_base + _hash(seed+"m", 40)
    )

def gen_layer(count: int, prefix: str, is_ind: bool, titles: list[str], companies: list[str], mut_base: int) -> list[MockPerson]:
    res = []
    for i in range(count):
        tit = titles[_hash(f"t-{prefix}-{i}", len(titles))]
        comp = companies[_hash(f"c-{prefix}-{i}", len(companies))]
        res.append(make_person(i, prefix, is_ind, tit, comp, mut_base))
    return res

# ── Dynamic Layers 1 to 11 ───────────────────────────────────────────────────

# L1: 100 IITR Students
L1_STUDENTS = gen_layer(100, "l1", True, ["Student", "Computer Science Student", "B.Tech Undergrad", "M.Tech Student"], ["IIT Roorkee"], 5)

# L2: 120 IITR Recent Alumni in India / Bangalore
L2_ALUMNI = gen_layer(120, "l2", True, ["Software Engineer", "Data Scientist", "Product Manager", "Backend Engineer"], 
                   ["Flipkart", "Paytm", "Zomato", "Swiggy", "Ola", "Microsoft India", "Google India", "Amazon India"], 15)

# L3: 150 Senior Alumni / Tech Leads
L3_SENIOR_ALUMNI = gen_layer(150, "l3", True, ["Senior Software Engineer", "Tech Lead", "Staff Engineer", "Engineering Manager"],
                          ["Google", "Microsoft", "Amazon", "Uber", "Meta", "Netflix", "Apple", "Salesforce"], 30)

# L4: 150 US-based Engineers & Managers
L4_US_ENGS = gen_layer(150, "l4", False, ["Senior Software Engineer", "Engineering Manager", "Principal Engineer"],
                    ["Google", "Meta", "Stripe", "Airbnb", "Robinhood", "Coinbase", "Snap", "Pinterest"], 45)

# L5: 150 Directors
L5_DIRECTORS = gen_layer(150, "l5", False, ["Director of Engineering", "Senior Director", "Head of Product"],
                      ["Google", "Meta", "Amazon", "Tesla", "NVIDIA", "xAI", "OpenAI", "Stripe", "Airbnb"], 60)

# L6: 120 Senior Directors
L6_SR_DIRECTORS = gen_layer(120, "l6", False, ["Senior Director of Engineering", "VP Product"],
                         ["Google", "Microsoft", "Salesforce", "Oracle", "Uber", "Block", "Anthropic"], 70)

# L7: 100 VPs
L7_VPS = gen_layer(100, "l7", False, ["VP of Engineering", "Vice President", "SVP Product", "VP Data"],
                ["NVIDIA", "Meta", "OpenAI", "Apple", "Databricks", "Snowflake", "Palantir"], 80)

# L8: 80 SVPs
L8_SVPS = gen_layer(80, "l8", False, ["SVP of Engineering", "Senior Vice President", "EVP"],
                 ["NVIDIA", "Google", "Microsoft", "Amazon", "Oracle", "Salesforce"], 90)

# L9: 80 Executives
L9_EXECS = gen_layer(80, "l9", False, ["C-Level Executive", "Chief Technology Officer", "Chief Product Officer"],
                  ["Stripe", "Airbnb", "Tesla", "Uber", "Block", "Shopify", "Snap"], 100)

# L10: 60 VC Principles / Partners
L10_VC_PARTNERS = gen_layer(60, "l10", False, ["Partner", "General Partner", "Managing Director"],
                         ["Sequoia Capital", "a16z", "Founders Fund", "Greylock", "Khosla Ventures", "Lightspeed"], 120)

# L11: 40 Top VC Executives / Board Members
L11_BOARD = gen_layer(40, "l11", False, ["Managing Partner", "Board Member", "Senior General Partner"],
                   ["Sequoia Capital", "a16z", "Founders Fund", "Benchmark", "Y Combinator", "Index Ventures"], 150)


# ── The Tech Leaders (Split into L5, L8, L12 for Hop Variety) ────────────────

FOUNDERS_RAW = [
    MockPerson("jensen-huang",       "Jensen Huang",       "https://www.linkedin.com/in/jensen-huang",       "Co-Founder & CEO at NVIDIA",                    "NVIDIA",          82),
    MockPerson("williamhgates",      "Bill Gates",         "https://www.linkedin.com/in/williamhgates",      "Co-chair, Bill & Melinda Gates Foundation",      "Gates Foundation", 89),
    MockPerson("elonmusk",           "Elon Musk",          "https://www.linkedin.com/in/elonmusk",           "CEO at Tesla, SpaceX & xAI",                    "xAI",             120),
    MockPerson("zuck",               "Mark Zuckerberg",    "https://www.linkedin.com/in/zuck",               "Founder & CEO at Meta",                         "Meta",            95),
    MockPerson("jeffbezos",          "Jeff Bezos",         "https://www.linkedin.com/in/jeffbezos",          "Founder at Amazon & Blue Origin",                "Amazon",          78),
    MockPerson("sundarpichai",       "Sundar Pichai",      "https://www.linkedin.com/in/sundarpichai",       "CEO at Google & Alphabet",                      "Google",          86),
    MockPerson("satyanadella",       "Satya Nadella",      "https://www.linkedin.com/in/satyanadella",       "Chairman & CEO at Microsoft",                   "Microsoft",       85),
    MockPerson("timcook",            "Tim Cook",           "https://www.linkedin.com/in/timcook",            "CEO at Apple",                                  "Apple",           48),
    MockPerson("samaltman",          "Sam Altman",         "https://www.linkedin.com/in/samuel-altman",      "CEO at OpenAI",                                 "OpenAI",          93),
    MockPerson("andrewyng",          "Andrew Ng",          "https://www.linkedin.com/in/andrewyng",          "Founder at DeepLearning.AI & Coursera",          "DeepLearning.AI", 61),
    MockPerson("reidhoffman",        "Reid Hoffman",       "https://www.linkedin.com/in/reidhoffman",        "Co-Founder at LinkedIn & Partner at Greylock",  "Greylock",        88),
    MockPerson("peterthiel",         "Peter Thiel",        "https://www.linkedin.com/in/peterthiel",         "Co-Founder at PayPal & Palantir",               "Founders Fund",   70),
    MockPerson("marcandreessen",     "Marc Andreessen",    "https://www.linkedin.com/in/mandreessen",        "Co-Founder at a16z",                            "a16z",            65),
    MockPerson("benhoro",            "Ben Horowitz",       "https://www.linkedin.com/in/ben-horowitz",       "Co-Founder at a16z",                            "a16z",            54),
    MockPerson("brianachesky",       "Brian Chesky",       "https://www.linkedin.com/in/brianchesky",        "Co-Founder & CEO at Airbnb",                    "Airbnb",          49),
    MockPerson("travis-kalanick",    "Travis Kalanick",    "https://www.linkedin.com/in/travis-kalanick",    "Co-Founder at Uber & CloudKitchens",            "CloudKitchens",   38),
    MockPerson("dara-khosrowshahi",  "Dara Khosrowshahi",  "https://www.linkedin.com/in/dara-khosrowshahi",  "CEO at Uber",                                   "Uber",            44),
    MockPerson("stewartbutterfield", "Stewart Butterfield", "https://www.linkedin.com/in/stewart-butterfield","Co-Founder at Slack & Flickr",                 "Slack",           36),
    MockPerson("tobi",               "Tobi Lütke",         "https://www.linkedin.com/in/tobi",               "Co-Founder & CEO at Shopify",                   "Shopify",         57),
    MockPerson("patrickcollison",    "Patrick Collision",  "https://www.linkedin.com/in/patrickcollison",    "Co-Founder & CEO at Stripe",                    "Stripe",          62),
    MockPerson("johncollison",       "John Collision",     "https://www.linkedin.com/in/john-collison",      "President & Co-Founder at Stripe",              "Stripe",          58),
    MockPerson("drew-houston",       "Drew Houston",       "https://www.linkedin.com/in/drewhouston",        "Co-Founder & CEO at Dropbox",                   "Dropbox",         40),
    MockPerson("aaronlevie",         "Aaron Levie",        "https://www.linkedin.com/in/aaronlevie",         "Co-Founder & CEO at Box",                       "Box",             33),
    MockPerson("evan-spiegel",       "Evan Spiegel",       "https://www.linkedin.com/in/evanspiegel",        "Co-Founder & CEO at Snap",                      "Snap",            35),
    MockPerson("jack-dorsey",        "Jack Dorsey",        "https://www.linkedin.com/in/jack-dorsey",        "Co-Founder at Twitter & Block",                 "Block",           67),
    MockPerson("ericschmidt",        "Eric Schmidt",       "https://www.linkedin.com/in/ericschmidt",        "Former CEO at Google",                          "Schmidt Ventures", 72),
    MockPerson("larryellison",       "Larry Ellison",      "https://www.linkedin.com/in/larryellison",       "Co-Founder & CTO at Oracle",                    "Oracle",          60),
    MockPerson("marc-benioff",       "Marc Benioff",       "https://www.linkedin.com/in/marcbenioff",        "Founder & CEO at Salesforce",                   "Salesforce",      64),
    MockPerson("dharmesh",           "Dharmesh Shah",      "https://www.linkedin.com/in/dharmesh",           "Co-Founder & CTO at HubSpot",                   "HubSpot",         47),
    MockPerson("danielek",           "Daniel Ek",          "https://www.linkedin.com/in/daniel-ek",          "Co-Founder & CEO at Spotify",                   "Spotify",         53),
    MockPerson("reedHastings",       "Reed Hastings",      "https://www.linkedin.com/in/reed-hastings",      "Co-Founder & Executive Chairman at Netflix",    "Netflix",         59),
    MockPerson("niklas-zennstrom",   "Niklas Zennström",   "https://www.linkedin.com/in/niklas-zennstrom",   "Co-Founder at Skype & Atomico",                 "Atomico",         37),
    MockPerson("emmet-shear",        "Emmett Shear",       "https://www.linkedin.com/in/emmett-shear",       "Co-Founder at Twitch",                          "Twitch",          26),
    MockPerson("kevin-systrom",      "Kevin Systrom",      "https://www.linkedin.com/in/kevin-systrom",      "Co-Founder at Instagram & Artifact",            "Artifact",        45),
    MockPerson("max-levchin",        "Max Levchin",        "https://www.linkedin.com/in/mlevchin",           "Co-Founder at PayPal & CEO at Affirm",          "Affirm",          50),
    MockPerson("david-sacks",        "David Sacks",        "https://www.linkedin.com/in/davidsacks",         "Co-Founder at Yammer & Craft Ventures",         "Craft Ventures",  46),
    MockPerson("chamath",            "Chamath Palihapitiya","https://www.linkedin.com/in/chamath",           "Founder at Social Capital",                     "Social Capital",  55),
    MockPerson("sequoia-roelof",     "Roelof Botha",       "https://www.linkedin.com/in/roelof-botha",       "Managing Partner at Sequoia Capital",           "Sequoia Capital",  58),
    MockPerson("ariannahuff",        "Arianna Huffington", "https://www.linkedin.com/in/ariannahuffington",  "Founder at Thrive Global & HuffPost",           "Thrive Global",   52),
    MockPerson("paul-graham",        "Paul Graham",        "https://www.linkedin.com/in/paul-graham",        "Founder at Y Combinator",                       "Y Combinator",    80),
    MockPerson("gary-tan",           "Garry Tan",          "https://www.linkedin.com/in/garrytan",           "President & CEO at Y Combinator",               "Y Combinator",    65),
    MockPerson("jason-calacanis",    "Jason Calacanis",    "https://www.linkedin.com/in/jasoncalacanis",     "Angel Investor & Podcaster",                    "LAUNCH",          50),
    MockPerson("bill-gurley",        "Bill Gurley",        "https://www.linkedin.com/in/billgurley",         "General Partner at Benchmark",                  "Benchmark",       68),
]

# Stagger the founders across different layers to get between 5 and 12 hops!
L5_FOUNDERS = FOUNDERS_RAW[0:15]    # Accessible in 5 hops (L4 -> L5)
L8_FOUNDERS = FOUNDERS_RAW[15:30]   # Accessible in 8 hops (L7 -> L8)
L12_FOUNDERS = FOUNDERS_RAW[30:]    # Accessible in 12 hops (L11 -> L12)

ALL_PERSONS: list[MockPerson] = (
    [L0_CALLER] + 
    L1_STUDENTS + L2_ALUMNI + L3_SENIOR_ALUMNI + 
    L4_US_ENGS + L5_DIRECTORS + L6_SR_DIRECTORS + L7_VPS + 
    L8_SVPS + L9_EXECS + L10_VC_PARTNERS + L11_BOARD +
    L5_FOUNDERS + L8_FOUNDERS + L12_FOUNDERS
)
PERSON_INDEX: dict[str, MockPerson] = {p.id: p for p in ALL_PERSONS}

def _build_adjacency() -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {p.id: set() for p in ALL_PERSONS}
    
    def link(a: MockPerson, b: MockPerson) -> None:
        adj[a.id].add(b.id)
        adj[b.id].add(a.id)
        
    def link_layers(layer_a: list[MockPerson], layer_b: list[MockPerson], edges_per_node: int):
        for i, a in enumerate(layer_a):
            for k in range(edges_per_node):
                b = layer_b[_hash(f"{a.id}-{k}", len(layer_b))]
                link(a, b)

    def link_within(layer: list[MockPerson], edges_per_node: int):
        for i, a in enumerate(layer):
            for k in range(edges_per_node):
                b = layer[_hash(f"{a.id}-in-{k}", len(layer))]
                if a.id != b.id:
                    link(a, b)

    # Base IITR Hub
    link_layers([L0_CALLER], L1_STUDENTS, 25) # Aviral knows 25 students
    link_within(L1_STUDENTS, 5)
    
    # The Chain: L1 -> L2 -> L3 -> L4 ... -> L11
    link_layers(L1_STUDENTS, L2_ALUMNI, 4)
    link_layers(L2_ALUMNI, L3_SENIOR_ALUMNI, 4)
    link_layers(L3_SENIOR_ALUMNI, L4_US_ENGS, 4)
    link_layers(L4_US_ENGS, L5_DIRECTORS, 5)
    link_layers(L5_DIRECTORS, L6_SR_DIRECTORS, 5)
    link_layers(L6_SR_DIRECTORS, L7_VPS, 5)
    link_layers(L7_VPS, L8_SVPS, 6)
    link_layers(L8_SVPS, L9_EXECS, 6)
    link_layers(L9_EXECS, L10_VC_PARTNERS, 6)
    link_layers(L10_VC_PARTNERS, L11_BOARD, 7)
    
    link_within(L4_US_ENGS, 3)
    link_within(L8_SVPS, 3)
    link_within(L11_BOARD, 3)

    # Attach Founders to specific Layers
    link_layers(L4_US_ENGS, L5_FOUNDERS, 8)     # 5 Hops total: L0 -> L1 -> L2 -> L3 -> L4 -> L5_FOUNDERS
    link_layers(L7_VPS, L8_FOUNDERS, 8)         # 8 Hops total
    link_layers(L11_BOARD, L12_FOUNDERS, 8)     # 12 Hops total

    return adj

ADJACENCY: dict[str, set[str]] = _build_adjacency()
