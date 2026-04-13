---
description: Pin closed-form formulas against canonical sources before writing implementation. Produces a verified "what must be true at the end" table.
---

# Verify before code

**Trigger this workflow at the start of any new physics/math module**,
before writing any implementation beyond the module header.

## Inputs

- A **list of closed-form formulas** the new module will implement. The user
  typically lists 3-6 key expressions in the concept-session message.
- A **scope statement** (what physics regime, eternal/evaporating, static/
  dynamical, pure/matter, etc.).

## Procedure

### 1. Identify canonical sources

For each formula, pick ONE canonical source from this table (prefer the
most specific). If a formula does not fit these, ask the user.

| Topic | Source |
|---|---|
| JT gravity + bath, QES setup | AEMM 2019 (arXiv:1905.08762) |
| QES formulation | Penington 2019 (arXiv:1905.08255) |
| Review / Page curve canonical | AHMST 2020 (arXiv:2006.06872) |
| Replica wormholes | Penington-Shenker-Stanford-Yang 2019 (arXiv:1911.11977) |
| Strominger BTZ derivation | Strominger 1998 (arXiv:hep-th/9712251) |
| BTZ original | Bañados-Teitelboim-Zanelli 1992 (arXiv:hep-th/9204099) |
| BTZ review | Carlip 1995 (arXiv:hep-th/9506079) |
| Kerr QNM wrapper | Stein 2019 qnm package (arXiv:1908.10377) + PyPI docs |
| Kerr QNM tables | Berti-Cardoso-Starinets 2009 (arXiv:0905.2975) |
| Hartman-Maldacena saddle | HM 2013 (arXiv:1303.1080) |
| Schwarzschild evaporation | Page 1976, Phys. Rev. D 13, 198 |
| Ryu-Takayanagi | RT 2006 (arXiv:hep-th/0603001) + RT 2006b (arXiv:hep-th/0605073) |
| Calabrese-Cardy entanglement | CC 2004 (arXiv:hep-th/0405152) |

### 2. Fetch

WebFetch against the ar5iv HTML mirror (`https://ar5iv.labs.arxiv.org/html/<id>`)
— the plain arXiv abstract pages only return metadata.

Ask the fetched content for:
- The exact formula(s) with variable definitions
- The section/equation number for provenance
- Any factor-of-2 or sign convention the paper uses explicitly

### 3. Record

For each formula, append an entry to the module docstring header **before**
implementing anything:

```python
r"""<module one-liner>.

Formulas pinned in v<X.Y>:

| Quantity | Closed form | Source |
|---|---|---|
| $S_{BH}$ | $\pi r_+ / (2 G_N)$ | Bekenstein-Hawking |
| Page time | $t_P = (1 - \sqrt{2}/4) t_{evap}$ | derived from $M(t_P) = M_0/\sqrt{2}$ |
| ... | ... | ... |

References
==========
- AEMM 2019, arXiv:1905.08762, eq. 18 (dilaton), eq. 69 (S_gen).
- ...
"""
```

### 4. Build a "what must be true at the end" table

Separately from the docstring, write a short text block the user can review:

```
Verified invariants (to be tested bit-exactly):
- M(t=0) = M_0 exactly
- M(t_Page)^2 = M_0^2 / 2 (abs_tol=1e-12)
- S_rad(t_evap) = 0 exactly
- Replica connected saddle == Phase 9 island_saddle_entropy (residual 0.0)
```

Pre-commit to these gates. The test suite in step 5 of ship-patch just
mechanically translates them to pytest assertions.

## Pause points

- After the fetch and before the docstring: **surface a one-paragraph
  summary of what you pinned**, so the user can catch "you pinned the wrong
  paper section".
- If any fetched source disagrees with a formula the user dictated in the
  concept session, **stop and ask** — do not silently pick one.

## Honest outputs

- If a fetch fails (abstract-only, dead link), say so explicitly.
- If the canonical source's coefficients don't match the convention used by
  the existing codebase (e.g., BTZ mass convention `M = (r_+² + r_-²)/(8 G_N L²)`
  vs competing `= r_+²/L²`), pick the one already used in the repo and
  document the convention choice in the module docstring.
