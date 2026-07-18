# EO-DG API Method Enforcement

EO-DG audits `server.py` GET and POST route declarations.

GET and HEAD routes must be observational. POST, PUT, PATCH, and DELETE may represent commands when they use explicit command interfaces and preserve authority checks.

The static route audit separates GET surfaces from POST command routes and flags unregistered or command-looking GET routes.

