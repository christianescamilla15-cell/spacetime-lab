---
description: Four-habit methodology that shipped Spacetime Lab v0.1 to v2.1. Any agent editing this repo must follow all four; violations must be flagged before proceeding.
trigger: always_on
---

# The four habits

## 1. Verify before code

For any non-trivial closed-form formula (Christoffel symbols, QNM coefficients,
Cardy / Brown-Henneaux / Strominger constants, horizon formulas, RT strip area,
QES extremality, etc.), **pin the formula to an external source before writing
the implementation**.

- Fetch the canonical paper or textbook section (arXiv, review, package docs).
- Write the formula and its provenance into the module docstring *before* coding.
- Do **not** code from memory when precision matters — four out of nine Phase
  failures in the original roadmap came from coded-from-memory sign/coefficient
  bugs.

## 2. Bit-exact gate tests

Every new module ends with a notebook gate cell and a test class that asserts
**bit-exact** or **machine-precision** agreement with a closed-form invariant.

- Default tolerance: `abs_tol=1e-12` (math.isclose).
- Relax only when the published reference has lower precision (e.g., Berti et
  al 2009 QNM table is 5 decimals → use `rel_tol=1e-4`).
- A non-zero residual where you expected machine precision is a **bug**, not a
  rounding accident. Find the discrepancy.
- Prefer independent-path verification: compute the same number two different
  ways and check the residual (Phase 7 RT vs Calabrese-Cardy, Phase 9
  HM vs island-continuity, v2.0 replica vs Phase 9 — all produced residual 0.0
  for the right reasons).

## 3. Honest scope-keeping

When a piece of code resists clean implementation, **mark it deferred or
experimental rather than ship something half-working**.

- Deferred features get a CHANGELOG entry with the *reason* and the *trigger
  condition* for un-deferral.
- Stubs stay out of production exports; they can live in the module, but
  `__all__` does not advertise them.
- Never ship a broken-but-labeled-ok feature. The project shipped nine phases
  + six patches without a single broken-but-deferred production feature.

## 4. Concept session before code

For any new physics / math / scientific computing phase or patch, the
structure is:

1. **Concept session in chat**: what we're building, why, what's new.
2. **Verification step**: pin formulas against sources, build a table of
   "what should be true at the end".
3. **API design**: propose the function signatures and module layout.
4. **Implementation**.
5. **Smoke test** against the verification table.
6. **Formal test file** pinned to the same closed forms.
7. **Notebook** with a closing gate cell that hard-asserts every claim.
8. **Release docs** (CHANGELOG / README / ROADMAP) + commit + tag + GitHub
   release.

Skipping any step is a bug.

# Style preferences

- **English for code and commits**; Spanish OK in user-facing chat.
- **Never use emojis inside code or commit messages**.  The README and
  release notes may use emojis sparingly when they carry meaning (🎉 for a
  v2.0-style milestone).
- **Bit-exact residuals are celebrated** — a `residual = 0.0` literal is more
  informative than "close to zero". Don't hide LSB-level matches.

# How to apply when working autonomously

If you are running this workflow without the user present:

- If a concept-level question arises (new API shape, new physics choice),
  **stop and write a concept note**; do not guess.
- If a deferred feature becomes a blocker, surface it instead of faking.
- If a test is failing near machine precision, investigate — do not widen
  tolerance to make it pass.
