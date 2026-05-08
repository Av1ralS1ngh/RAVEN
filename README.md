# RAVEN — Hypothesis Validation Copilot

RAVEN is a LangGraph-powered copilot that helps equity analysts validate investment hypotheses fast. Paste a thesis and the agent assembles an end-to-end diligence loop: structured planning, data collection through Yahoo Finance (yfinance), hybrid LLM analytics, narrative synthesis, and a polished report published for instant download. The goal is to collapse a multi-hour research sprint into a guided interactive session.

## Why It Matters
- **Actionable research in minutes**: Automates diligence steps that usually span analysts, data engineers, and PMs.
- **Audit-ready output**: Every chart, metric, and insight is backed by stored evidence and downloadable PDFs.
- **Human-in-the-loop**: Optional review gates let analysts approve or redirect the workflow before decisions are recorded.

## System Highlights
- 🔁 **LangGraph Orchestration** – deterministic workflow stages with retry-aware LLM REPL execution.
- 🧠 **LLM Hybrid Analytics** – prompt-safe Python execution, RESULT-validated outputs, and chart generation.
- 📊 **Yahoo Finance Integration** – direct data retrieval using the `yfinance` library (company info, historical prices, financials, etc.)
- 🖥️ **FastAPI + Sleek UI** – submit hypotheses, watch milestones progress, and download final reports in one screen.

## Architecture Overview
```
[FastAPI / UI]
	│
	▼
[Hypothesis Service] ─────→ [In-Memory Storage]
	│
	▼
[LangGraphValidationOrchestrator]
  ├─ Planning Stage - Plan Generation (LLM) 
  ├─ Data Collection Stage - YFinance Data Fetching
  ├─ Analysis Stage - Hybrid Analysis (LLM REPL)
  ├─ Analysis Stage - Detailed Narrative (LLM)
  ├─ Report Rendering (ReportLab)
  └─ Delivery (Portal publish)
```

## Getting Started

### Requirements
- Python 3.12+
- OpenAI API key (or compatible Azure endpoint)

### Install & Configure
```bash
git clone https://github.com/ayushsi42/raven.git
cd raven
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Required environment variables
set -a
source .env
set +a
```

## Run It Locally

### Installation
```bash
git clone https://github.com/Av1ralS1ngh/RAVEN.git
cd raven
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### Environment Variables
Create a `.env` file in the project root (or export variables manually). At minimum:

```bash
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"             # optional, default is gpt-4o-mini
```

### Start the API & UI
```bash
PYTHONPATH=src uvicorn hypothesis_agent.main:app --reload
```

Visit `http://localhost:8000/` for the landing page. The REST API is exposed beneath `/v1`.

### Run Tests
```bash
PYTHONPATH=src pytest
```

## Data Sources (YFinance)

RAVEN uses the `yfinance` library for financial data collection. The following tools are available:

- **Company Info** – fundamental data, ratios, descriptions
- **Historical Prices** – OHLCV market data
- **Financials** – income statements
- **Balance Sheet** – asset and liability data
- **Cash Flow** – cash flow statements
- **Earnings** – performance reports
- **Recommendations** – analyst ratings
- **News** – ticker-related news
- **Holders** – institutional and major owners
- **Dividends & Splits** – historical corporate actions

## License & Attribution
This project was produced during Hacktualization 2025 by Team RAVEN. Usage is internal-only unless granted explicit permission.
