# Strategy Module Template

## Summary
Describe the strategy in plain language:
- what market condition it targets
- what signals it uses
- what risk controls are included

## Safety & responsibility
This module is provided for research/education only. You are solely responsible for backtesting, simulation testing, configuration, and any live use. See the root **DISCLAIMER.md**.

## Files in this module
- `src/` — source code
- `metadata.yaml` — machine-readable metadata used for cataloging
- `parameters.md` — parameter documentation (defaults + units)
- `notes.md` — research notes + failure modes
- `changelog.md` — module-specific changelog
- `screenshots/` — optional visuals
- `test-results/` — optional test artifacts / logs

## Implementation notes
- Keep logic deterministic where possible.
- Prefer explicit naming over clever shorthand.
- Avoid hard-coding instrument/session assumptions unless required; document them if you do.
