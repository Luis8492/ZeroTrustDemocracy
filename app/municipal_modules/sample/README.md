# sample

Reference plugin demonstrating the municipality plugin contract. Everything in
this directory is **synthetic** — the assembly, the members, the topics, and
the minute texts are all fabricated for documentation and CI purposes.

A real plugin lives at the same shape: `__init__.py` exports `PARSERS` /
`FETCHERS`, `config/<name>.yaml` defines paths + fetch URLs, and each session
sub-package (`regular/`, `committee/`, ...) holds its `fetchers/` and
`parsers/`. The only thing different here is that `SampleFetcher` skips
Playwright and copies bundled fixtures from `regular/samples/` instead of
scraping a live site.

## Smoke test

```bash
# from the framework repo root
python scripts/init_db.py sample
python app/fetch.py --municipality sample          # copies fixtures → raw_minutes/sample/
python app/minute_analyzer.py --municipality sample
python scripts/export_static_data.py --municipality sample
```

After the last command, `frontend/public/data/index.json` and
`frontend/public/data/meetings/*.json` are populated and `npm run dev` in
`frontend/` will render the synthetic QAs.

## Format

See `regular/parsers/sample_parser.py` — the parser is intentionally short and
documents the file format inline.
