# Copilot Progress Tracker

## Current Status
Working on repository organisation and documentation structure.

## Completed
- [x] Created `build_docs/` folder
- [x] Moved all build-related `.md` files into `build_docs/`
- [x] Created this `copilot.md` progress tracker

## Build-Related Docs (now in `build_docs/`)
| File | Description |
|------|-------------|
| `build-guide.md` | Main build guide |
| `STEP_01.md` – `STEP_10.md` | Step-by-step build steps |
| `STEP_04.2.md`, `STEP_05-06.md`, `STEP_05.0.md`, `STEP_05.5.md`, `STEP_05_ENTERPRISE.md` | Extended build step variants |
| `IMPLEMENTATION.md` | Implementation notes |
| `VERIFICATION_MATRIX.md` | Verification checklist/matrix |
| `STATUS.md` | Build/project status |
| `compliance-module-guide.md` | Compliance module guide |
| `improvements.md` | Planned improvements |
| `I18N_DIGITALTWIN.md` | Internationalisation / digital twin notes |

## Next Steps
- [ ] Review and update `build_docs/STATUS.md` with latest project state
- [ ] Ensure all cross-references between docs still resolve after the move
- [ ] Continue feature development per `build_docs/STEP_10.md` and beyond

## Notes
- Run tests: `python -m pytest tests/ -q`
- Start API: `python -m civ_arcos.api` (serves on port 8080)
- Dashboard: http://localhost:8080/dashboard
