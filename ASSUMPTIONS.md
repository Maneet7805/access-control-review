# Assumptions

This file records the defaults the agent chose when Maneet had no answer, one line each.
- 13 Nov 2026: Ran the M1.1 spike without a G0 tick or D1 pick because Maneet said "You decide". D1 itself is not decided.
- 13 Nov 2026: Built M1.6 with D2 = A (probes run through `docker exec`) because Maneet said "proceed" and A is the roadmap default. D2 itself is not ticked.
- 13 Nov 2026: Added task M1.8 (demo_sandbox) so owner gate G1 can be run; no task built it. Options: add M1.8, or edit G1. Picked M1.8: smallest change. Prints counts for table `profiles` by default.
- 13 Nov 2026: M2.2 needs a JSON schema validator. Options: hand-written checks, or `jsonschema`. Picked `jsonschema` as a dev-only dependency (tests); the code itself validates in plain Python.
