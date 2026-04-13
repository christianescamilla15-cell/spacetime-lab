# Spacetime Lab — Claude Code Project Context

## Session bootstrap (read first)

When you open a new session in this repo, **immediately read
`.agent/runs/LATEST.md` if it exists**.  That file is auto-generated
by every dispatched workflow (claude-dispatch, dispatch-with-ollama,
bootstrap-new-project) and summarises the most recent dispatch:
its inputs, outputs, repo URL, duration, token usage, and a tail of
the agent output.

Without reading it you arrive blind to whatever the user just
triggered from their phone or from `gh workflow run`.  With it, you
already know what was scaffolded / opened / changed and can pick up
the next step coherently.

If `.agent/runs/LATEST.md` does **not** exist, no dispatch has run
since the last full-clean checkout — proceed normally.

## What is this?
Interactive platform for exploring black hole physics. Python SDK + FastAPI backend + React frontend. Combines visualization, simulation, and analysis in one unified toolkit.

## Author
Christian Hernández Escamilla — AI engineer learning GR by building tools for it.

## Stack
- **Core package:** Python 3.12 + numpy/scipy/sympy + quimb (Phase 6+)
- **Backend:** FastAPI + asyncio + Redis + WebSocket
- **Frontend:** React 18 + Vite 8 + Three.js + Plotly + KaTeX
- **Deploy:** Vercel (frontend) + Render (backend) + PyPI (package)

## Structure (monorepo)
```
spacetime-lab/
├── spacetime_lab/    # Python package (pip installable)
├── backend/          # FastAPI
├── frontend/         # React
├── docs/             # MkDocs
├── notebooks/        # Jupyter tutorials
└── tests/            # pytest
```

## Module Map
| Module | Purpose | Phase |
|--------|---------|-------|
| metrics/ | Exact solutions (Schwarzschild, Kerr, AdS, BTZ) | 1 |
| diagrams/ | Penrose + embedding diagrams | 2 |
| geodesics/ | Symplectic integrators | 3 |
| horizons/ | Event/apparent, ISCO, photon sphere | 4 |
| waves/ | QNMs, ringdown, Bilby/PyCBC integration | 5 |
| entropy/ | Holographic entanglement entropy (RT/HRT) | 7 |
| edu/ | Tutorials | continuous |

## Critical Rules
- NEVER hardcode constants — use `spacetime_lab.utils.constants`
- NEVER break symbolic computations with premature numerical substitution
- ALWAYS use geometric units (G=c=1) unless explicitly noted
- ALWAYS provide LaTeX representation alongside numerical output
- ALWAYS cite sources in docstrings (Wald, MTW, Carroll, etc.)
- Frontend .jsx for files with JSX (Vite 8 strict)
- Test every metric against known invariants (horizons, curvature scalars)

## Deploy
- Frontend: spacetime-lab.vercel.app (auto-deploy from master)
- Backend: spacetime-lab-api.onrender.com (auto-deploy from master)
- Package: pip install spacetime-lab
- Docs: docs.spacetimelab.dev (future)

## Conventions
- English for code, English for user-facing strings (international audience)
- Pydantic v2 for API models
- Type hints on all functions
- Docstrings in NumPy format
- Black formatting, ruff linting

## Physics-specific conventions
- Signature (-,+,+,+) for Lorentzian metrics (Wald convention)
- Boyer-Lindquist coordinates for Kerr by default
- Units: G = c = 1 (geometric), unless `physical_units=True`
- Angular momentum a ∈ [0, M] for physical Kerr
