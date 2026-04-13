---
description: Commit-message and release-docs conventions for Spacetime Lab. Mirrors the v1.x-v2.x sprint style bit-for-bit.
trigger: always_on
---

# Commit messages

- **First line**: `<type>(<scope>): <imperative summary under 70 chars>`
  where `<type>` is one of `release`, `feat`, `fix`, `refactor`, `test`, `docs`,
  `chore` and `<scope>` is the patch version or module (`v2.1`, `qes`, `vercel`).
  Examples from the repo:
  - `release(v2.1.0): dynamical QES Page curve + Schwarzschild-AdS RT`
  - `fix(vercel): pin framework to null to bypass 'Services' monorepo preset`

- **Body**: blank line, then paragraphs. Release commits must include:
  - "Added" section listing new public API entries.
  - "Verified bit-exact" table with residuals.
  - "Honest scope deferred to vX.Y" section.
  - "Bugs caught during verify-before-code" section (if applicable).

- **Footer**: always end with a Co-Authored-By line:
  ```
  Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
  ```

- Pass the body via HEREDOC (`git commit -m "$(cat <<'EOF' ... EOF)"`) so
  markdown bullets and tables render correctly.

# Tags

- Lightweight `vX.Y.Z` doesn't work for releases; use **annotated tags** with
  a multi-line message summarising the patch.

# GitHub releases

- Create via `gh release create vX.Y.Z --title "vX.Y.Z — <short headline>" --notes "$(cat <<'EOF' ... EOF)"`.
- Body structure mirrors the commit but lighter: short hook, bit-exact table,
  scope deferred, methodology note, and a closing `🤖 Generated with [Claude
  Code](https://claude.com/claude-code)` line.

# CHANGELOG

- Entries follow Keep-a-Changelog format: `## [X.Y.Z] — YYYY-MM-DD — <headline>`.
- Sections within a release: `Added`, `Verified`, `Tests`, `Honest scope
  deferred`, `Bugs caught during verify-before-code`, `Methodology`.

# Version bumps

- Minor version bump = new physics capability (v1.1, v1.2, v2.1).
- Major version bump = refactor of Phase-9-style hand-identified logic into a
  real formalism (v2.0).
- Patch version reserved for pure bug fixes with no new API.

# Do not

- Do not amend commits that have been pushed. Always create a new commit.
- Do not use `--no-verify` or skip hooks.
- Do not ship a release without the CHANGELOG, ROADMAP, README badge, and
  pyproject.toml version bump all updated together.
