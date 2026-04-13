---
description: Ship a new Spacetime Lab v1.x or v2.x patch end-to-end using the physics-builder methodology. Takes a target patch name and a plain-text task description.
---

# Ship a Spacetime Lab patch end-to-end

**Trigger this workflow when** the user says "ship v2.X ...", "release patch
v2.X", or provides a patch scope and expects a full release flow.

## Required inputs (ask the user if not provided)

1. **Target version** (e.g., `v2.2.0`).
2. **Scope statement**: 1-3 sentences describing the physics / capability.
3. **Deferrals**: anything the user explicitly wants out of this patch.

## Eight-step release flow

Execute these in order. Do **not** skip a step.

### 1. Concept session (in chat, no code)

Write a plain-text concept note covering:
- What physics / math you're building and why it's the next step
- Which closed-form invariants you'll gate on (pre-commit to a residual)
- API sketch (function signatures + module paths)
- What is **explicitly deferred** and why
- Verification sources you will pin against

Wait for an explicit "luz verde" or equivalent before writing code.

### 2. Verify-before-code

Fetch the canonical source for every closed-form formula you'll implement:
- For AdS/CFT: AEMM 2019 (arXiv:1905.08762), Penington 2019 (arXiv:1905.08255),
  AHMST 2020 (arXiv:2006.06872)
- For Kerr QNMs: Stein's qnm package docs + Berti-Cardoso-Starinets 2009
- For BTZ / rotating BTZ: BTZ 1992, Carlip 1995, Strominger 1998
- For evaporation: Page 1976

Prefer WebFetch on the `ar5iv.labs.arxiv.org/html/<id>` version; the PDF
abstract pages give only metadata. Record the exact equations and the paper
section in the module docstring header **before** writing any function body.

### 3. Module implementation

- File path: `spacetime_lab/<subpackage>/<new_module>.py`.
- Add the module's public API to `spacetime_lab/<subpackage>/__init__.py`
  (both the import list and `__all__`).
- Follow the existing style: NumPy docstrings, type hints on every function,
  `from __future__ import annotations`, `math.pi` not a hardcoded constant,
  `G_N = 1.0` default.
- Every function that takes a dimensionful parameter validates it
  (`if mass <= 0: raise ValueError(...)`).

### 4. Smoke test before formal tests

Run one `python -c "..."` script that exercises the happy path and prints
the key residuals. This catches the stupid sign/exponent bugs before you
write 30 tests around them.

### 5. Tests

- `tests/test_phase_<vX_Y>.py`.
- Pin to closed-form invariants from step 2.
- Default tolerance `abs_tol=1e-12`; relax only with a comment citing the
  published-reference precision.
- Group tests into classes by concept (e.g., `TestEvaporation`,
  `TestSaddleCrossing`).

### 6. Notebook

- `notebooks/<N>_<short_name>.ipynb`.
- Structure: concept headline → 1-2 derivation cells → 2-3 result cells with
  plots → closing gate cell that re-runs the invariants as hard asserts.
- The closing gate cell must end with `print("ALL V<X>.<Y> GATES PASS")` or
  equivalent.

### 7. Release docs

Update together in one commit:
- `CHANGELOG.md` — follow the v1.x-v2.x pattern (Added / Verified / Tests /
  Honest scope deferred / Bugs caught during verify-before-code / Methodology).
- `README.md` — version badge + test count badge + release link + notebook
  table row.
- `ROADMAP.md` — new `## vX.Y patch` section.
- `pyproject.toml` — `version = "X.Y.Z"`.

### 8. Commit + tag + push + GitHub release

- `git add` the specific files (no `-A`).
- Commit message per `rules/commit-and-release-style.md`.
- Annotated tag `vX.Y.Z` with multi-line message.
- `git push origin master` and `git push origin vX.Y.Z`.
- `gh release create vX.Y.Z --title "..." --notes "$(cat <<'EOF' ... EOF)"`.
- Update the project memory file `project_spacetime_lab_v<X>_<Y>.md`.

## Pause points (ask the user)

You must pause and get explicit approval at:
- End of **step 1** (concept session). Do not start coding without "luz verde".
- End of **step 5** if the full test suite introduces any regression
  (existing test breaks).
- End of **step 7** before `git push`, since a push is visible externally.

## Auto-execution mode

- Steps 1, 2, 8 are **manual**: need user approval.
- Steps 3, 4, 5, 6, 7 can run **auto** once step 2 is signed off.
- If Vercel or Render auto-deploy fails on push, stop and surface it — do
  not retry blindly.
