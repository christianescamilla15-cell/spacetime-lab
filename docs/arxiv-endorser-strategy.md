# arXiv gr-qc submission — endorser strategy

**Status:** preparation phase.  Cannot submit until you find an endorser.

The arXiv `gr-qc` archive requires endorsement from an established
researcher for first-time submitters in that category.  This is a
60-second action for the endorser (one click in the arXiv portal),
but they must trust you enough to click it.

This document is the strategy for finding one.

---

## How endorsement works

1. You start the submission process at https://arxiv.org/submit
2. arXiv detects you have no prior gr-qc papers
3. arXiv shows you an "endorsement code" + URL to share
4. You email a potential endorser asking them to visit the URL and
   click "Endorse"
5. Once endorsed (it's a one-time per-archive thing, not per-paper),
   you can submit any number of gr-qc papers from then on

**The endorser DOES NOT review your paper.**  They are just
vouching that you're a real researcher who isn't going to spam the
archive with crank physics.  That's why most reasonable scientists
will endorse if asked politely with a credible track record (working
code + tests is a legitimate one).

---

## Strategy: pick endorsers who care about open science / pedagogy

Endorsers have to log in to arXiv to click; you want people who
already do that frequently.  Within gr-qc, this means active
researchers, ideally ones who have specifically advocated for or
contributed to open-source GR tools.

### Tier 1 — High likelihood of saying yes

These researchers have published widely in gr-qc AND have visible
public-facing pedagogy work (textbook chapters, blog posts, public
GitHub presence).  Endorsement is in their stated value system.

| Name | Affiliation | Why a good fit | Contact path |
|---|---|---|---|
| **Sean Carroll** | Johns Hopkins / Santa Fe | Author of *Spacetime and Geometry*; runs Mindscape podcast; vocal about open science | `sean@preposterousuniverse.com` (his blog email) |
| **Leo C. Stein** | U of Mississippi | Author of `qnm` Python package (which Spacetime Lab v1.2 wraps); has thanked similar projects publicly | `lcstein@olemiss.edu` (university page) |
| **Vitor Cardoso** | IST Lisbon / NBI Copenhagen | Co-author of canonical QNM review (Berti-Cardoso-Starinets 2009) — directly cited by your tests | `vitor.cardoso@tecnico.ulisboa.pt` |
| **Emanuele Berti** | Johns Hopkins | Same paper; supervisor of multiple grad students using public code | `berti@jhu.edu` |
| **Niayesh Afshordi** | Perimeter Institute | Active in GR pedagogy + public outreach; works on BH ringdown | (Perimeter directory) |

### Tier 2 — Decent shot, more "professional cold ask"

| Name | Affiliation | Notes |
|---|---|---|
| Will Farr | Stony Brook + Flatiron | Bilby co-author; ringdown analysis |
| Maximiliano Isi | IAS Princeton | Ringdown spectroscopy; no-hair tests |
| Geoffrey Compère | ULB Brussels | Holography / asymptotic symmetries |
| Daniel Harlow | MIT | Holographic entanglement entropy |
| Mark Van Raamsdonk | UBC | Holographic entanglement |

### Tier 3 — Network ask (don't cold-email)

If you have ANY connection — your university, an old professor, a
LinkedIn connection — to a gr-qc author, ask them first.  A warm
intro converts at >70%; a cold email at maybe 20%.

---

## Email template (Tier 1 / Tier 2 cold ask)

**Subject:** arXiv gr-qc endorsement request — open-source interactive GR toolkit

Keep it short.  Endorsers get a lot of these; the ones that work
respect the reader's time.

```
Dear Prof. <Name>,

I'm writing to ask if you would be willing to endorse me for the
arXiv gr-qc archive.  I've built an open-source educational toolkit
called Spacetime Lab that I'd like to publish a short preprint
about; the project is the only gr-qc-adjacent work I have so this
is a first submission.

The project (MIT license) is a Python package + REST API + interactive
web app spanning the arc from Schwarzschild to the Page curve, with
a 690+ pytest suite that pins every closed-form result to its
canonical reference value (including Berti-Cardoso-Starinets 2009
for the QNM tables and Brown-Henneaux 1986 for the BTZ Cardy match).

  Live demo:   https://spacetime-lab.vercel.app
  Code:        https://github.com/christianescamilla15-cell/spacetime-lab
  Draft:       https://github.com/christianescamilla15-cell/spacetime-lab/blob/master/docs/arxiv-draft.md

If you're willing, the endorsement link will look like
  https://arxiv.org/auth/endorse?x=<CODE>
once I start the submission process.  No paper review is needed
on your part — endorsement just vouches that I'm a real researcher.

Thanks for considering this regardless of the answer.

Best,
Christian Hernández Escamilla
christianescamilla15@gmail.com
```

---

## arXiv submission technical checklist (for when you have an endorser)

Once endorsed, the submission itself is mechanical:

- [ ] Convert `docs/arxiv-draft.md` to LaTeX (arXiv accepts PDF or
      LaTeX source; LaTeX preferred for indexing).  pandoc handles
      most of this:
      ```
      pandoc docs/arxiv-draft.md -o arxiv-submission.tex \
        --template=acmart --bibliography=refs.bib
      ```
- [ ] Pick primary archive: **gr-qc**
- [ ] Pick cross-list: **physics.ed-ph** (physics education)
- [ ] Title (exact): "Spacetime Lab: An Open Educational Toolkit for
      Black-Hole Physics from Schwarzschild to the Page Curve"
- [ ] Author: Christian Hernández Escamilla
- [ ] Email: christianescamilla15@gmail.com
- [ ] Comments field: "11 pages, 6 figures, code at
      https://github.com/christianescamilla15-cell/spacetime-lab"
- [ ] License: arXiv non-exclusive (default; lets you also publish in
      a journal later)
- [ ] Submit during arXiv business hours (US Eastern; submissions
      late in week sit unprocessed until Monday)

Best release window for visibility: Sunday 23:00 UTC submission →
appears on Monday's mailing.  Mondays get the most reads.

---

## What NOT to do

- ❌ Don't cold-email 10 people simultaneously — endorsers compare
  notes; getting 3 "I already endorsed someone" replies looks bad
- ❌ Don't claim affiliations you don't have — fact-checkable in
  60 seconds
- ❌ Don't submit before HN/r/Physics launch.  An endorser checking
  the GitHub URL sees zero stars vs 100+ stars makes a difference
- ❌ Don't pad the paper.  6-12 pages with real content beats
  20 pages with filler

---

## Realistic timeline

| Day | Action |
|---|---|
| 0 | HN + r/Physics launch (today/tomorrow) |
| +3-5 | Wait for organic GitHub stars to build (target: 50+) |
| +5 | Email Tier 1 endorser candidates (3-5 in parallel is OK) |
| +7-14 | Endorsement received |
| +1 day | Submit |
| +2-3 days | arXiv mailing list announces it |

Total: 2-3 weeks from today to public preprint, IF launch traction
is decent.  If launch flops, may need to skip arXiv and just keep
GitHub as the canonical reference.
