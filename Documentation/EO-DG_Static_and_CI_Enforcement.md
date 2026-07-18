# EO-DG Static and CI Enforcement

EO-DG static tests verify:
- route audit separates GET reads from POST commands
- mutating command surfaces cannot be guarded as reads
- registered surfaces declare consistency and prohibited effects
- static source does not create financial authorities
- certified surfaces are not command surfaces

The route audit flags command-like GET routes and unregistered production GET routes.

