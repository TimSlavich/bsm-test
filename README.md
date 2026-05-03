# Brand SERP Monitor

Monitors a branded Google SERP for an iGaming operator (e.g. `starcasino` in NL), classifies each top-N domain through a three-stage pipeline, persists every snapshot, and surfaces drift through an interactive React dashboard.

## TL;DR

```bash
cp .env.example .env          # paste your OpenRouter key into LITELLM_API_KEY
docker compose up --build     # backend (Playwright + Alembic + SQLite) + frontend
# → http://localhost:5173 — dashboard
# → http://localhost:8000/docs — OpenAPI / Swagger
```

In the dashboard click **Run live scan**. The fetcher cascade tries Google first (Playwright + stealth + NL consent cookies), falls back to DuckDuckGo HTML, and finally to a saved fixture. ~10–60 s end-to-end.

To populate the trend chart immediately on a fresh DB:

```bash
docker compose exec backend python -m brand_monitor.scripts.seed_history --brand starcasino --days 7
```

## What it solves

A branded SERP for an iGaming operator contains four kinds of result mixed together:

1. **Official** — the brand's own apex / localized / promo / owned-media domains.
2. **Affiliate-to-Brand** — partners that genuinely send traffic to the brand and earn commission.
3. **Competitor-Hijacking** — sites that *use the brand name* but redirect users to **other operators**.
4. **Informational / Neutral** — news, regulators, forums, gambling portals.

Hand-monitoring this past a few brands is intractable. The tool automates it: daily SERP capture, three-stage classification, historical snapshots, dashboard drift tracking.

## Architecture

```
            ┌─────────────────────────────────────────────────────────────┐
            │                    Brand SERP Monitor                       │
            └─────────────────────────────────────────────────────────────┘
                                       │
  ┌────────────────────────────────────┼─────────────────────────────────┐
  │              SERP fetcher (cascade)│                                 │
  │   ┌────────────────────────────────▼──────┐                          │
  │   │ 1. Google · Playwright + stealth +    │  ── on captcha ─┐        │
  │   │    NL consent cookies                 │                 │        │
  │   └───────────────────────────────────────┘                 ▼        │
  │   ┌───────────────────────────────────────┐  ┌────────────────────┐  │
  │   │ 3. Saved fixture (last-resort, demo)  │◄─│ 2. DuckDuckGo HTML │  │
  │   └───────────────────────────────────────┘  └────────────────────┘  │
  └────────────────────────────────────┬─────────────────────────────────┘
                                       │  N×SerpResult (pos, url, domain, title)
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │                     Classifier pipeline                              │
  │  ┌────────────┐ miss ┌──────────────┐ low conf ┌──────────────────┐  │
  │  │  Stage 1   │─────►│   Stage 2    │─────────►│   Stage 3 — LLM  │  │
  │  │ Whitelist  │      │  Algorithm   │          │  arbiter (model  │  │
  │  │ (no I/O)   │      │  + mimicry   │          │  chain rotation, │  │
  │  │ conf 0.95  │      │  rule        │          │  hostile-text    │  │
  │  │            │      │              │          │  guarded)        │  │
  │  └────────────┘      └──────────────┘          └──────────────────┘  │
  │                                                                      │
  │  Stage-2 page fetch goes through a pluggable PageFetcher with        │
  │  cascading httpx → Playwright fallback (bypasses Cloudflare /        │
  │  JS-only-rendered pages).                                            │
  └────────────────────────────────────┬─────────────────────────────────┘
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Persistence: SQLAlchemy 2 async + Alembic + SQLite (WAL)            │
  │  brands · brand_keywords · serp_snapshots ·                          │
  │  serp_results · domain_classifications                               │
  └────────────────────────────────────┬─────────────────────────────────┘
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  FastAPI: REST + SSE (live scan progress)                            │
  └────────────────────────────────────┬─────────────────────────────────┘
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Dashboard: React 19 + TanStack Query + Recharts (no CSS framework)  │
  │  Distribution · Position lineup · Stage breakdown · N-day trend ·    │
  │  Top-N table with drilldown · Snapshot diff · Scheduler CRUD         │
  └──────────────────────────────────────────────────────────────────────┘
```

## Why three stages

A naïve "one LLM call per domain on every scan" approach costs roughly `$0.05 × 10 results × 1000 brands × 30 days ≈ $15k/month` for work that is hash-lookup 70% of the time. The staged design pushes work to the cheapest tier that can produce a confident verdict: whitelist (free, ~70%), algorithm (~$0.001/URL, ~25%), LLM (only when confidence < 0.65, <5%).

The hardest engineering problem is **distinguishing partner from hijacker** — both look identical on the surface. Stage 2 resolves this by following each affiliate redirect chain (under SSRF guards) and computing the **destination ratio**: majority brand → partner; majority competitor → hijacker; mixed → text-bait + stage-3 escalation.

## Mimicry detection

A common NL hijacker pattern is the *fake-official* page — a domain like `starcasino.net.nl` that claims *"Officiële website"*, copies KSA legalese, has zero outbound affiliate links, and quietly funnels registrations. The redirect-ratio rule can't catch it (no outbound to measure); calling it "informational" distorts the dashboard.

Stage 2 includes a dedicated mimicry rule that fires on a non-whitelisted domain when (a) title or H1 contains an *official-claim* marker (*"Officiële website"*, `™`, login/registration claim) **and** brand mentions exceed a threshold **and** the page is isolated, or (b) brand mentions are very heavy (≥30) on a page with no schema.org and no resolvable outbound. Both flags route to `hijacker_blackhat_scam` with high confidence.

## Pluggable PageFetcher

Stage 2 needs the rendered HTML of each SERP-listed URL. The httpx fast path covers ~80% of pages, but JS-only-rendered hijacker funnels and Cloudflare-protected sites return either a hollow shell or 403 to a non-browser fetcher.

Rather than scattering `if playwright` branches through the pipeline, the project exposes a single `PageFetcher` Protocol with three implementations: `HttpxPageFetcher`, `PlaywrightPageFetcher`, and `CascadingPageFetcher` (tries fast first, falls back when blocked / empty / SPA-shell). Adding a new backend (Browserless, ScrapingBee, residential-proxy provider) is a single new class implementing the Protocol — no pipeline changes required.

The cascade triggers on: fast-fetch returned `None`; status ∈ `{401, 403, 405, 429, 503}`; body too small (<1.5 KB); low anchor count + SPA marker (`__NEXT_DATA__`, `data-reactroot`).

## LLM model chain

OpenRouter free-tier providers frequently 429 under upstream load. The arbiter accepts a comma-separated `ARBITER_MODELS` chain and rotates to the next model on rate-limit / transient error (within-model: one quick retry; cross-model: rotate). Different OpenRouter providers serve different models, so a 429 on Llama 3.3 doesn't imply a 429 on the next entry. Adding a provider is one env-var entry — no code change.

For paid deployment the chain collapses to a single high-quality model.

## Stack

| Layer       | Choice                                                        |
|-------------|---------------------------------------------------------------|
| Language    | Python 3.12 (backend), TypeScript strict (frontend)           |
| API         | FastAPI + Pydantic v2 + SSE                                   |
| ORM         | SQLAlchemy 2 (async) + Alembic                                |
| DB          | SQLite via aiosqlite (WAL). Postgres = `DATABASE_URL` swap.   |
| SERP fetch  | Playwright + playwright-stealth → DuckDuckGo HTML → fixture   |
| Page fetch  | Pluggable: httpx → Playwright cascade (Strategy pattern)      |
| LLM router  | LiteLLM → OpenRouter, comma-separated model fallback chain    |
| Tracing     | Langfuse (optional, hooks wired through LiteLLM callbacks)    |
| Frontend    | Vite + React 19 + TanStack Query + Recharts (no CSS framework) |
| i18n        | react-i18next, EN default + UK auto-detect                    |
| Tests       | pytest + Hypothesis (property-based) + httpx ASGI integration |
| Pkg mgr     | uv (Python), npm (Node)                                       |

## Running locally without Docker

Prereqs: [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
# Backend
cd backend
uv sync
uv run playwright install chromium      # one-time
uv run migrate                          # alembic upgrade head
uv run start                            # :8000 with --reload

# Frontend (separate terminal)
cd frontend
npm ci
npm run dev                             # :5173, proxies /api → :8000
```

`uv run start --prod --workers 4` for prod-style. `uv run seed-history --brand starcasino --days 7` for trend-chart demo data.

## Tests

```bash
cd backend
uv run pytest                           # 66 tests: unit + property + integration
uv run pytest -m property               # Hypothesis only
uv run pytest --cov=brand_monitor       # coverage
```

The LLM arbiter has dedicated tests with mocked LiteLLM (valid response, invalid subcategory, malformed JSON, network error, missing key, confidence clamping) — no real API calls in CI.

## Repository layout

```
.
├── README.md
├── docker-compose.yml              # backend + frontend with healthchecks
├── .env.example                    # every documented variable
├── backend/
│   ├── pyproject.toml              # deps + scripts + pytest + ruff config
│   ├── Dockerfile                  # multi-stage: builder → runtime + chromium
│   ├── alembic.ini, alembic/       # async-aware migrations
│   └── src/brand_monitor/
│       ├── main.py                 # FastAPI entry
│       ├── config.py               # pydantic-settings (.env auto-discovery)
│       ├── cli.py                  # uv run start / migrate
│       ├── api/                    # routes + Pydantic schemas + SSE
│       ├── classifier/
│       │   ├── pipeline.py         # 3-stage orchestrator (never raises)
│       │   ├── whitelist.py        # stage 1
│       │   ├── algorithm.py        # stage 2 (incl. mimicry rule)
│       │   ├── llm.py              # stage 3 + ARBITER_MODELS chain
│       │   ├── page_fetcher.py     # PageFetcher Protocol + cascade
│       │   ├── safety.py           # SSRF guard
│       │   ├── prompts.py          # arbiter prompt templates
│       │   ├── constants.py        # tunable knobs
│       │   ├── signals.py          # affiliate links, schema.org, mentions
│       │   └── taxonomy.py         # 4 categories × 16 subcategories + ReasonCode
│       ├── db/                     # models + async session (SQLite WAL)
│       ├── seeds/                  # brand config + tracker fingerprints
│       ├── serp/fetcher.py         # cascading SERP fetcher
│       ├── services/scan.py        # high-level scan orchestration
│       ├── scheduler.py            # APScheduler with multi-worker guard
│       └── scripts/seed_history.py # demo trend data
└── frontend/
    ├── Dockerfile                  # vite build → nginx with /api proxy
    ├── nginx.conf
    └── src/
        ├── lib/api.ts              # typed fetch wrappers + SSE EventSource
        ├── i18n/                   # EN + UK translations
        ├── components/             # ui primitives + charts
        ├── features/               # scan, snapshot, diff, scheduler, dashboard
        ├── pages/Dashboard.tsx
        └── styles/                 # tokens + dark mode (data-theme)
```

## Configuration

`.env.example` documents every variable. Critical ones:

| Variable             | Purpose                                            |
|----------------------|----------------------------------------------------|
| `DATABASE_URL`       | Defaults to SQLite WAL on a Docker volume          |
| `LITELLM_BASE_URL`   | `https://openrouter.ai/api/v1`                     |
| `LITELLM_API_KEY`    | OpenRouter key (stage-3 LLM arbiter)               |
| `ARBITER_MODEL`      | Primary model — used when `ARBITER_MODELS` empty   |
| `ARBITER_MODELS`     | Comma-separated fallback chain (rotates on 429)    |
| `AUTO_CREATE_TABLES` | `false` in prod, `true` in dev                     |
| `SCHEDULER_ENABLED`  | `true` enables APScheduler daily scans             |
| `CORS_ALLOW_ORIGINS` | Comma-separated allowed origins                    |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Optional LLM tracing keys |
| `LANGFUSE_HOST`      | Defaults to cloud; set to `http://host.docker.internal:3000` for self-hosted |

If `LITELLM_API_KEY` is unset, the pipeline silently skips stage-3 and returns the stage-2 verdict — the classifier never raises.

## Trade-offs intentionally taken

- **No paid SERP APIs.** Live Google needs residential proxies in production; without them the cascade falls through to DuckDuckGo HTML, which has slightly different ranking but unwraps correctly.
- **Whitelists as code seed**, not a UI. Brand ops grow the lists via the manual review queue. The data path (`POST /api/brands`, `PUT /whitelists`) is wired.
- **No Tailwind / no CSS framework.** A few hundred lines of CSS custom properties; dark mode via `data-theme="dark"`. Worth a Tailwind migration past ~50 components.
- **APScheduler in-process** (single replica). Production multi-replica goes to Temporal / Celery-beat; the scheduler module is small and entirely replaceable. Multi-worker guard refuses to start when `WEB_CONCURRENCY > 1`.
- **SQLite, not Postgres.** Schema and ORM code are dialect-agnostic; switching is a `DATABASE_URL` change. WAL + busy-timeout handle the staggered scheduler writes.
- **`Base.metadata.create_all` only in dev.** Prod path runs Alembic exclusively.
- **Free-tier LLMs are upstream-rate-limited** by OpenRouter providers. The model chain mitigates this; for a paid key the chain collapses to one entry.

## Production roadmap

| Item                                              | Reason                       |
|---------------------------------------------------|------------------------------|
| Postgres + connection pool                        | Concurrent writers           |
| Temporal cron workflow                            | Durability across restarts   |
| Residential proxy pool for Google fetcher         | Bypass Google bot detection  |
| Redis cache: SERP (24h TTL) + classification (7d) | Cost + latency               |
| Cold archival → S3 + Parquet                      | Long-tail history queries    |
| Langfuse self-hosted in compose                   | First-class observability    |
| GitHub Actions: lint → typecheck → tests → build  | CI/CD gate                   |
| Visual regression (Playwright screenshot diff)    | Dashboard QA                 |
| Brand-admin UI form                               | Reduce ops dependence on API |
| Persistent Playwright browser pool                | Reduce ~2s launch overhead   |
