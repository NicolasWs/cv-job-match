# cv-job-match

Nicolas's job-search pipeline + local control panel.

- **webapp/** — the control panel UI (filters → weekly jobs → scoring → application packages). Start here: [webapp/README.md](webapp/README.md).
- **config/search-profile.yaml** — single source of truth for search, filters, sectors and scoring weights.
- **pipeline/** — filter/dedupe engine and n8n config sync.
- **n8n/** — weekly LinkedIn scrape workflow (Apify → Drive). Setup: [docs/n8n-setup.md](docs/n8n-setup.md).
- **context/** — master CVs (EN/FR) that feed every generated package.
- **prompts/build-package.md** — spec for generated application packages.
- **applications/** — one folder per built package.
- **app/** — earlier v1 chat-style tool (still runnable, see app/README.md).
