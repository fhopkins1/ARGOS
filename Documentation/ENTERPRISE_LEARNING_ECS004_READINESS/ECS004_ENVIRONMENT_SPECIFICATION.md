# ECS-004 Environment Specification

Supported OS: Windows 10/11 or clean Python-capable Linux environment.
Observed OS: Windows-11-10.0.26200-SP0
Architecture: AMD64
Python: 3.14.5
Package manager: pip with repository-local `pyproject.toml`.
Database/services: none required for Enterprise Learning ECS-004 reproduction.
Environment variables: none required beyond standard Python execution.
Filesystem: writable repository directory; evidence output under `Documentation/ENTERPRISE_LEARNING_RM002_BEHAVIORAL_IMPLEMENTATION`.
Locale/encoding: UTF-8.
Timezone: deterministic timestamps are fixed constants in the generator; host timezone is not used for evidence identity.
Network: prohibited for execution. No external services or datasets are required.
Minimum resources: 1 CPU, 512 MB RAM, 100 MB free disk.
