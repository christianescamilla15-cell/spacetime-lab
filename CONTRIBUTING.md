# Contributing to Spacetime Lab

Thank you for your interest in contributing! This project welcomes contributions from physicists, mathematicians, and developers of all levels.

## Ways to Contribute

- **New exact metric solutions** — add a class to `spacetime_lab/metrics/`
- **Tutorial notebooks** — Jupyter notebooks in `notebooks/`
- **Bug fixes** — check the issues tab
- **Documentation** — improve docstrings, add examples
- **Performance optimization** — faster geodesic integration, caching
- **Visualization** — better 3D rendering, plots

## Development Setup

### Clone and install
```bash
git clone https://github.com/christianescamilla15-cell/spacetime-lab.git
cd spacetime-lab
```

### Python package
```bash
cd spacetime-lab
pip install -e ".[dev]"
pytest
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Code Style

- **Python:** Black + Ruff. Run `black . && ruff check .` before committing.
- **JavaScript:** Prettier + ESLint.
- **Physics:** Always use geometric units (G=c=1) unless noted. Cite sources.

## Commit Messages

Follow conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` adding tests
- `refactor:` code refactoring
- `perf:` performance improvement

Example:
```
feat(metrics): add Reissner-Nordstrom exact solution
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes with tests
4. Run the test suite: `pytest`
5. Push and open a PR
6. Respond to review comments

## Physics Rigor

When adding new physics:
- **Cite the source** in the docstring (book, paper, or standard reference)
- **Test against known invariants** (e.g., Kretschmann scalar for a vacuum solution)
- **Document conventions** (signature, coordinate system, units)
- **Compare to existing tools** (EinsteinPy, Mathematica, etc.) where possible

## Questions?

Open a discussion on GitHub or contact the maintainer.
