# RAVEN

RAVEN is an advanced recruitment intelligence and network mapping tool developed to help job seekers intelligently discover connections and analyze recruiter expectations. Operating at the intersection of professional networking and repository analysis, it empowers developers to uncover the most direct paths to hiring managers while auditing how well their public code portfolios align with a recruiter's desired tech stack constraints.

The platform is split into two primary modules backed by a sophisticated graph database architecture. **Module 1 (Path Finder)** performs multi-hop shortest-path traversals across a simulated or live LinkedIn graph utilizing TigerGraph's GSQL to identify hidden connection chains (bridge nodes). **Module 2 (Tech Stack Analyzer)** leverages Google's Gemini LLM to interpret a recruiter's job bio, extracts the demanded technologies, and simultaneously clones a candidate's GitHub repositories to compute a "blast radius"—mapping precisely which files depend on those specific technologies.

## Architecture

```text
    [ Frontend - React/Vite ]
          |        |
    (REST API)  (REST API)
          |        |
    [ Backend - FastAPI ] -------------+
      /        |       \               |
     /         |        \              v
[Playwright] [GitHub]  [Gemini 3.1] [TigerGraph]
 (Scraper)   (Clone)    (LLM)       (Cloud DB)
```

## Prerequisites

- **Node.js** (v20+)
- **Python** (v3.11+)
- **Google Cloud CLI** (`gcloud` configured with Vertex AI access)
- **TigerGraph Cloud Account** (Free tier supported)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/recruitgraph.git
   cd recruitgraph
   ```

2. **Environment Variables:**
   Copy the example environment file and fill in your credentials:
   ```bash
   cp backend/.env.example .env
   ```
   *(See the Environment Variables table below for details).*

3. **TigerGraph Cloud Setup:**
   - Create a free cluster on TigerGraph Cloud (version 3.9+).
   - Retrieve your host URL, username, password, and generate a Secret (or let the app auto-generate it if left blank).
   - Add these to your `.env` file.

4. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm ci
   cd ..
   ```

5. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

6. **Install Browser Binaries (for Scraping):**
   ```bash
   playwright install --with-deps chromium
   ```

7. **Start the Development Servers:**
   - **Terminal 1 (Backend):** `cd backend && uvicorn app.main:app --reload --port 8000`
   - **Terminal 2 (Frontend):** `cd frontend && npm run dev`

## TigerGraph Auto-Schema Installation

To streamline deployments, RecruitGraph is designed with a schema auto-installer. Upon the first backend launch (or when specifically invoking the graph clients), the backend utilizes `pyTigerGraph` to detect if the require schemas (`PersonGraph` and `DepGraph`) exist. If they do not, it automatically builds the schemas from the `.gsql` artifacts provided in the repository, provisions the vertices and edges, and publishes them. You do not need to manually configure the GSQL topologies.

## Environment Variables

| Name | Description | Example | Required |
|------|-------------|---------|----------|
| `DEMO_MODE` | Uses local mock graph instead of scraping LinkedIn if `true` | `true` | Yes |
| `TG_HOST` | TigerGraph Cloud address | `https://your-cluster.i.tgcloud.io` | Yes |
| `TG_USERNAME` | TigerGraph username | `tigergraph` | Yes |
| `TG_PASSWORD` | TigerGraph password | `MySuperSecret123!` | Yes |
| `TG_SECRET` | TigerGraph RESTPP Secret (auto-created if empty) | `abc123secret...` | No |
| `github_pat` | GitHub Personal Access Token for cloning | `ghp_xxxx` | Yes |
| `PROJECT_ID` | GCP Project ID for Gemini Vertex AI | `my-gcp-project` | Yes |
| `LOCATION` | GCP Project Region | `us-central1` | Yes |
| `VITE_API_BASE_URL`| Base URL for the frontend to hit the backend | `http://localhost:8000` | Yes |

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/path/health` | Healthcheck endpoint. Validates DB & LLM connection. | None |
| `POST` | `/api/path/find` | Computes shortest connection path from user to recruiter. | None |
| `POST` | `/api/blast/analyze` | Extracts stack from URL, clones GitHub, maps dependencies.| None |
| `GET` | `/api/blast/detail` | Returns specific file-level impact for a given library. | None |

## Development Workflow

For concurrent development, it is recommended to run the services bare-metal in two separate terminal sessions as shown in the **Setup Instructions**.

If you prefer to use Docker compose locally:
```bash
docker-compose up --build
```
This will spin up both the React frontend and FastAPI backend, linking them through a shared network. The frontend is served via an optimized Nginx container, proxying `/api` traffic internally to the Python container.

## Known Limitations

- **LinkedIn Scraping Restrictions:** The Playwright scraper running against live LinkedIn targets is highly susceptible to automated rate-limits, captchas, and IP bans. Using `DEMO_MODE=true` is strongly recommended for local testing and presentation.
- **GitHub API Rate Limits:** Cloning and analyzing repositories via the GitHub parser heavily utilizes GitHub's API. Unauthenticated requests are severely throttled; ensure you have a `github_pat` set to access the standard 5,000 requests/hour limit.

## License

MIT License. See `LICENSE` for details.
