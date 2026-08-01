# ECS-004 Installation Runbook

1. Extract `ENTERPRISE_LEARNING_ECS004_REPOSITORY.zip` into an empty directory.
2. Open a terminal in the extracted repository root.
3. Verify Python: `python --version` must report Python 3.11 or newer.
4. Optional environment creation: `python -m venv .venv`.
5. Optional activation on Windows: `.venv\Scripts\Activate.ps1`.
6. Install package metadata if desired: `python -m pip install -e .`.
7. Verify repository scripts compile: `python -m py_compile Scripts\enterprise_learning_rm002_behavioral_implementation.py Scripts\enterprise_learning_ecs004_readiness_package.py src\argos\control_panel\enterprise_learning_runtime.py`.
8. Expected exit code for every command is `0`. Any nonzero exit code is an installation failure.
