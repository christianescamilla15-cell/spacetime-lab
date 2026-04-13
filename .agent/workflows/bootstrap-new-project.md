---
description: Scaffold a brand-new repo from scratch. The surrounding runner handles gh repo create, clone, commit, push; aider's job here is ONLY to author the scaffold files inside the empty repo.
---

You are an autonomous scaffolder.  You are sitting inside a newly-cloned
empty repository whose only file is `README.md` (auto-created by `gh repo
create --add-readme`).  Your job is to produce a working initial scaffold
for the project described below.

# Project

- **Name**: `{{PROJECT_NAME}}`
- **Stack**: `{{STACK}}`  (one of `python-fastapi`, `react-vite`,
  `python-cli`, `streamlit`)
- **Description**: {{PROJECT_DESCRIPTION}}

# Your deliverable by stack

Given the stack above, produce exactly these files and nothing more.
Do not add anything extra.  Do not invent unrelated configuration.

## Stack = `python-fastapi`

Create:
- `app/__init__.py` — empty file.
- `app/main.py` — minimal FastAPI app with a single `GET /` that returns
  `{"status": "ok", "project": <{{PROJECT_NAME}}>}` and a `GET /health` that
  returns `{"status": "healthy"}`.  No DB, no middleware, no auth.
- `requirements.txt` — exactly `fastapi` and `uvicorn[standard]`, each on
  its own line.
- `Dockerfile` — `python:3.12-slim` base, copies requirements.txt, pip
  installs, copies app/, exposes 8000, runs
  `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `.gitignore` — standard Python gitignore (`__pycache__/`, `*.pyc`,
  `.venv/`, `.env`, `.pytest_cache/`).
- Overwrite `README.md` with a short description, a `## Run locally`
  section showing `pip install -r requirements.txt` + `uvicorn app.main:app
  --reload`, and a `## Docker` section showing `docker build -t <name> .`
  and `docker run -p 8000:8000 <name>`.

## Stack = `react-vite`

Create:
- `package.json` — React 18 + Vite 5, scripts `dev`, `build`, `preview`.
- `vite.config.js` — minimal `import { defineConfig } from 'vite'; import
  react from '@vitejs/plugin-react'; export default defineConfig({ plugins:
  [react()] })`.
- `index.html` — standard Vite React template index.html.
- `src/main.jsx` — ReactDOM.createRoot mounting `App`.
- `src/App.jsx` — a single functional component showing the project name
  and description in an h1 + paragraph, minimal inline styles.
- `.gitignore` — `node_modules/`, `dist/`, `.env.local`, `.DS_Store`.
- `vercel.json` — `{ "framework": "vite" }` so Vercel auto-detects.
- Overwrite `README.md` with a short description and a `## Run locally`
  section showing `npm install` + `npm run dev`.

## Stack = `python-cli`

Create:
- `pyproject.toml` — PEP 621 style, project name from `{{PROJECT_NAME}}`,
  Python >=3.10, declare a single console-script entry point
  `<{{PROJECT_NAME}}> = <{{PROJECT_NAME}}>.__main__:main`.
- `src/<{{PROJECT_NAME}}>/__init__.py` — empty.
- `src/<{{PROJECT_NAME}}>/__main__.py` — a `main()` function parsing argv,
  printing `<{{PROJECT_NAME}}>: hello, {arg}` where `arg` is the first CLI
  argument or `world` if none.  `if __name__ == "__main__": main()` at
  bottom.
- `.gitignore` — standard Python gitignore.
- Overwrite `README.md` with a short description and a `## Install
  locally` section showing `pip install -e .` + `<{{PROJECT_NAME}}> hello`.

## Stack = `streamlit`

Create:
- `app.py` — a Streamlit app showing the project name as a title, the
  description as caption, and a single `st.text_input` + `st.button`
  that on click says "you typed: {value}".
- `requirements.txt` — exactly `streamlit`.
- `.gitignore` — standard Python gitignore.
- Overwrite `README.md` with a short description and a `## Run locally`
  section showing `pip install -r requirements.txt` + `streamlit run
  app.py`.

# Rules

- **Do not** modify `.git/`, `.github/`, or any file outside the above.
- **Do not** run shell commands; the surrounding runner handles git and
  deploy.
- **Do not** add tests, CI, linting, docker-compose, or any extra
  dependency beyond what this document lists.  If you think something
  extra is needed, leave it for a follow-up patch — honest scope-keeping
  applies here too.
- Produce concrete file contents, not placeholders.  Every file should be
  runnable / installable as-is.
- Keep all strings and identifiers lowercase + hyphenated for project
  names (`my-thing-optimizer` not `My_Thing_Optimizer`), except Python
  package names which use underscores (`my_thing_optimizer`).

# Output

Emit only the file edits.  The runner will commit and push afterward.
