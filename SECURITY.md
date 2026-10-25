# Security boundary

ModernizeIQ is a local, single-user static-analysis prototype for small repositories. It never executes target scripts, binaries, tests or dependency installers, and it makes no outbound request during assessment. It never connects to discovered databases or endpoints.

ZIP members are read without extraction. Stored and deflated members only; reject traversal/absolute/drive/ADS names, duplicates, case collisions, links, special files, encrypted members and excessive compression ratios. Apply entry/depth/size limits before and during reads. Local inputs reject links and special files. Excluded and unsupported files are reported.

Potential secret values are not printed or serialized. Evidence uses fixed descriptions, file/line references and content hashes. Source text stays in memory only. Names, paths, dependency names and approved route shapes are metadata; users should still review reports before sharing. This is not a universal secret detector.

HTML escapes repository-derived values and denies network/script execution using a restrictive content policy. No target content is interpreted as instructions or executable HTML.

Limitations: application-level limits do not constitute a hardened multi-tenant sandbox. Use a fixed local copy and do not mutate files during inspection. Parent-directory races, parser resource consumption, OS permissions and unrecognized encodings/languages require care. A future public upload API must add isolated worker processes, CPU/memory/time quotas, authentication, authorization, rate limits and retention controls. The current milestone must not be exposed as a public upload service.

Security findings are review indicators, not confirmed vulnerabilities. No vulnerability, deprecation or current-version database is queried. Report a suspected analyzer bug with a minimal fictional fixture and expected behavior; never submit real credentials.
