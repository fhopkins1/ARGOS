# AUDIT Repository Manifest

- Repository name: ARGOS
- Branch: `main`
- Commit hash at preparation start: `212fbea3c912eec83aa3c90287bbed974f19f873`
- Planned audit tag: `argos-audit-candidate-20260712-231120Z`
- UTC timestamp: `2026-07-12T23:11:25.114225+00:00`
- Git remote:
```text
origin	https://github.com/fhopkins1/ARGOS.git (fetch)
origin	https://github.com/fhopkins1/ARGOS.git (push)
```
- Git status at preparation start:
```text
## main...origin/main
 M .gitignore
?? AUDIT_DEPENDENCY_REPORT.md
?? AUDIT_FILE_TREE.txt
?? AUDIT_GIT_BRANCHES.txt
?? AUDIT_GIT_LOG.txt
?? AUDIT_GIT_REMOTES.txt
?? AUDIT_GIT_STATUS.txt
?? AUDIT_GIT_TAGS.txt
?? AUDIT_IMPLEMENTATION_PRESENCE_MATRIX.md
?? AUDIT_LAST_COMMIT_DETAILS.txt
?? AUDIT_SECRET_AND_PRIVACY_REVIEW.md
?? AUDIT_SNAPSHOT_PREPARATION_LOG.md
?? AUDIT_TAG_NAME.txt
?? AUDIT_WORKING_TREE_INVENTORY.md
```
- Total tracked files: 534
- Source-file count: 313
- Test-file count: 100
- Documentation-file count: 216
- Migration-file count: 1
- Configuration-template count: 3
- Total tracked repository size: 6443282 bytes
- Primary languages: Python, JavaScript, HTML, CSS, Markdown
- Package managers: Python/pyproject; no Node package manifest detected
- Runtime entry points: `src/argos/control_panel/runtime.py`, `src/argos/control_panel/server.py`, `src/argos/control_panel/canonical_enterprise_runtime.py`
- Test entry points: `python -m unittest`, `python -m compileall`, `node --check ui/argos_control_panel/app.js`
- UI entry points: `ui/argos_control_panel/index.html`, `ui/argos_control_panel/app.js`, `ui/argos_control_panel/styles.css`
- Persistence entry points: `src/argos/foundation/persistence/*`, `src/argos/control_panel/enterprise_persistence.py`
- Broker adapters: `src/argos/trader/paper_brokerage.py`
- Live-trading status: disabled / not certified
- Truth domains: proof, simulation, paper, live-disabled, position truth, performance truth
- Known unsupported capabilities: live trading, certified continuous paper trading, completed long-duration campaign
- Known failing/incomplete tests: full unittest discovery did not complete in audit window
