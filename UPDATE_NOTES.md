# 25 October 2026 update

Added a database-backed health check, request timing and logging, dedicated Studio CI definition, Docker build recipe and explicit sample inputs. Tests: 66 passed. Docker and remote CI execution are not claimed.

Fixed an archive rejection caused by an excluded compiled source map exceeding the per-file limit. Whole-archive expansion, path, encryption and compression checks remain. Expected archive errors now show their specific reason. Bundled demo-apps/examples/samples are excluded from application assessment so a Flask fixture cannot label its host as Flask. Old saved assessments are unchanged; re-import to use the new scope. Scores can fall when irrelevant evidence is removed.

A high static score is not a security certification. Testing 100 means selected testing indicators exist, not 100 percent test coverage. Use real fixes and explicit limitations; do not tune weights to inflate a score.
