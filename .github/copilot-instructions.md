# Copilot / AI Agent Instructions

These instructions define how automated agents should work in this repository.

## Branching and Releases (post v1)

- Do **not** commit directly to `main` or `dev`.
- All work must be done on a short-lived branch created from `dev`:
  - `feature/<short-description>` for new features
  - `bugfix/<short-description>` for bug fixes
- Open pull requests **into `dev`**.
- Only merge `dev` into `main` as part of a release.
  - Release PRs should be `dev` → `main`.
  - Tags/releases should point at `main`.

## Quality gates

- Prefer the existing VS Code tasks (or equivalent commands):
  - Tests: `python -m pytest tests/ -v`
  - Lint: `python -m pylint src/bbl_shutter_cam/`
  - Types: `python -m mypy src/bbl_shutter_cam/`
  - Format: `python -m black src/ tests/ scripts/`
- Keep changes minimal and focused; avoid drive-by refactors.

## Repo conventions

- Preserve public CLI behavior unless the change explicitly requires otherwise.
- Documentation must stay in sync with behavior changes.
- If a change affects features/functionality/user workflows/configuration/CLI output, update the relevant docs *in the same PR* before merging into `dev`:
  - `CHANGELOG.md`
  - `ROADMAP.md` (if it impacts planned work or milestones)
  - `README.md`
  - anything under `docs/`
- Do not merge changes into `dev` without the documentation updates for that change.
- If a change modifies what is stored in the config file (new keys, changed defaults, renamed/removed settings, profile structure), update the examples in the same PR:
  - `examples/config.example`
  - `examples/config.minimal.toml`
- Prefer editing existing files over adding new ones unless required.
