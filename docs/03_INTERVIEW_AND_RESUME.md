# Your project story, interview preparation and referral résumé

Use the statements below only after you have run the project, made the hands-on changes and can explain the result. This is AI-assisted development. You do not need to hide that, and you should not claim to have independently written supplied code or performed work you have not done.

## Why choose these ideas?

A motivation you can adapt **if it matches your own thinking**:

“I wanted to learn how software engineering supports enterprise operations and modernization. Before changing a system, teams need evidence about its current behavior and risks. I chose two related problems: OpsPilot investigates a simulated incident after a failure; ModernizeIQ inspects source indicators before a modernization decision. I focused on evidence, reproducible rules and explaining limitations because an attractive dashboard alone would not help someone make a trustworthy decision.”

Do not invent employment, client projects, financial savings or a production incident as the origin of the idea.

## What problem each project solves

| Project | Problem | What the current artifact demonstrates |
|---|---|---|
| OpsPilot | Incident clues are spread across metrics, logs and deployment context | A local synthetic incident workflow, deterministic investigation, FastAPI/SQLite integration and a React/TypeScript console; the current change improves the palette and legibility |
| ModernizeIQ | Legacy assessment requires repeated source/configuration review | A local static-inspection pipeline, selected evidence-backed findings, configurable readiness points and proposed modernization actions |

OpsPilot does not run a real operations center or perform real remediation. ModernizeIQ does not migrate applications, run a full vulnerability scan or include the planned LLM/full-stack platform in this milestone.

## How this can help an Accenture referral application

Accenture's public application-modernization service description covers assessing application portfolios, defining architecture and building roadmaps. That makes ModernizeIQ's problem framing relevant to the company's work. This is a connection between your learning project and a business domain, not evidence of selection preference or an entry-level job requirement.

Source checked 24 October 2026: [Accenture — Application modernization](https://www.accenture.com/en/services/cloud/application-transformation/application-modernization).

| Evidence you can demonstrate | Skill it supports | What you should be able to explain |
|---|---|---|
| One source change, traced to a finding and weighted score | Python, debugging and analytical thinking | Why the result changed and why other findings remain |
| Rejected traversal ZIP and never-execute test | Defensive engineering | Input boundaries, size limits and remaining sandbox limitations |
| Manifest parser tests and structured output | Data handling and modular code | Declared vs installed/transitive dependencies |
| Evidence-linked priorities and executive summary | Consulting communication | Technical risk → operational consequence → proposed action |
| OpsPilot CSS-token edit and rebuild | React/TypeScript build workflow and UI judgment | Source vs compiled assets; semantic status colors and readability |
| Your own regression test and experiment log | Quality and ownership | A hypothesis, failure case, result and corrected understanding |

Match your résumé to the specific referral role's job description. Do not copy every technology keyword from the master prompt. Without a role ID, this is general preparation rather than a tailored résumé. A referral can help your application reach consideration; it does not guarantee shortlisting or an offer.

## Résumé wording for the current ModernizeIQ milestone

**ModernizeIQ — Repository Readiness Analyzer | Python, AST, JSON, pytest | AI-assisted portfolio project**

Choose two or three bullets after reproducing them yourself:

- Built and validated a Python static-analysis prototype that inventories local/ZIP repositories, parses declared dependencies and links selected modernization indicators to file-level evidence.
- Configured and verified readiness scoring across 10 dimensions with 34 transparent checks; generated technical and executive reports with evidence-linked modernization priorities.
- Evaluated two controlled fixtures, matching 11 labelled findings in the legacy sample and zero positives in the improved control; verified the packaged 51-test suite and documented its limited evaluation scope.
- Extended the starter with **[your actual change]** and **[your actual regression test]**, documenting predicted and observed behavior.

Replace placeholders with work you actually completed. The 51-test count belongs to the delivered suite; it will change if you add tests. Do not call the fixture result “100% accurate,” and do not say you authored all 51 tests independently.

## Résumé wording for your OpsPilot contribution

If you only performed the colour update and learned the existing app:

“Customized and tested a React/TypeScript incident-investigation console using shared colour tokens, responsive layouts and accessible status indicators, working with an existing FastAPI demonstration backend.”

If you also understand and have genuinely worked on the wider implementation, describe the relevant deterministic simulator, evidence reasoning or SQLite/API changes specifically. Keep “synthetic telemetry” and “simulated remediation” explicit. Do not describe hardcoded rules as an autonomous LLM agent.

## What you must understand before listing ModernizeIQ

You can run it from a clean extracted folder; identify the ingestion boundary; explain a Python AST assignment detector; show a finding's source line and hash; calculate a score; explain one false positive/missed-case limitation; run a negative test; explain why the analyzer never reads benchmark answers; distinguish implemented modules from planned FastAPI/SQLite/React/AI; and state what you personally changed.

If you cannot explain a bullet in ordinary language, simplify the bullet and keep learning that part.

## 30-second explanation — implemented milestone

“ModernizeIQ is a Python prototype for evidence-based legacy assessment. It safely reads a repository without running its code, inspects supported dependency and configuration patterns, and produces traceable findings. A configurable rule system calculates ten readiness dimensions and proposes a phased modernization plan. I validated it on controlled fixtures and used before/after changes to check the scoring. The current version is deterministic; AI explanation and the full web platform are future stages.”

## Two-minute explanation — implemented milestone

“The problem I chose is understanding an older application before proposing cloud modernization. Source review can be repetitive, and recommendations are weak if they cannot be traced to evidence. My prototype accepts a local folder or ZIP. It limits input size, rejects unsafe paths and links, skips vendored/build content and never executes target code.

“The analyzer creates a file snapshot, parses supported dependency manifests and uses Python AST inspection plus limited configuration-text rules. It records fixed explanations with file, line, rule and hash references; it omits detected secret values. It distinguishes observations from hypotheses: for example, a local file write suggests instance-bound state, but does not tell us the application's real durability needs.

“The score is a documented heuristic. Each dimension earns points for selected checks and the overall score is a weighted mean. Every number can be recalculated from exported JSON. Recommendations group related findings and propose stabilization, preparation and automation before larger architecture work. It does not automatically prescribe microservices.

“I tested positive cases, negative controls, malformed manifests, unsafe ZIPs and evidence integrity. The two demo fixtures are intentionally small; their results are not a general accuracy claim. My hands-on contribution was [describe your own experiment or code change and its test]. The next engineering gate is persistence and an API, followed by the React workbench; the current artifact is a local analyzer and report.”

## Three core interview questions and strong answers

**Why deterministic analysis before an LLM?** The evidence should be reproducible and testable. The baseline parses and records observations with fixed rule IDs. A future LLM can explain supplied evidence, but it should not invent findings. No LLM has been integrated in this milestone.

**How does the score work?** Each check earns a configured number of points if its condition is satisfied. A category is earned/possible × 100, and the overall number is a weighted mean. Parser warnings withhold absence-based credit. The weights encode judgment; the score is not universal or a probability. I can demonstrate disabling debug and the resulting 3.2-point overall change with the default configuration.

**What are the main limitations?** Static analysis cannot prove runtime architecture, security or deployment behavior. Language support is partial; declaration age, CVEs and actual test coverage are not measured. Presence of a test or CI file is weaker than executing it. Recommendations need a human with business context.

## Additional concepts to practice

| Concept | Clear explanation |
|---|---|
| Legacy modernization | Improving an existing system's maintainability, reliability or delivery without assuming every component needs replacement |
| Cloud readiness | Whether application and operating practices suit the intended cloud environment; more than merely running on a virtual machine |
| Monolith | One main deployment unit; it can still have good internal modules |
| Modular monolith | Cohesive module boundaries within a shared deployment, avoiding distributed-service overhead when unnecessary |
| Microservices | Independently deployable services; they add networking, consistency, deployment and observability work |
| Coupling | How strongly a component depends on another component's details |
| Stateless instance | Durable/shared state lives outside an individual application instance so replacement or scaling is manageable |
| External configuration | Environment-specific settings are supplied at runtime instead of being embedded in source |
| Secret handling | Values should be protected, scoped and rotated; an environment variable is a delivery mechanism, not a complete secret-management system |
| Container | A packaged application/runtime process environment; a Dockerfile does not automatically make the code scalable or secure |
| CI/CD | Automated integration checks and a controlled delivery/release workflow; this milestone detects indicators rather than proving a pipeline ran |
| Logs / metrics / traces | Event records / numerical time series / request journeys across components |
| Health checks | Signals used to judge whether a process is alive or ready; a constant success endpoint alone may miss dependencies |
| Technical debt | Design or implementation choices that create future maintenance work; repayment should be prioritized by risk and value |

## Prepare a referral-ready project package

1. Complete the experiments and add your real learning notes.
2. Capture your own two screenshots: risk/evidence view and a before/after score comparison.
3. Review the source and reports for private data before making anything public.
4. Keep a clear README with the setup commands, actual feature boundary, test result and limitations.
5. Put the project on a repository you control when ready; add the repository link to your résumé. No GitHub repository has been created or published by this delivery.
6. Prepare a three-minute live demo: problem, scan, one finding, one calculation, one limitation, one contribution.
7. Tailor two concise bullets to the actual job description; include only skills you can discuss.

A useful evidence order in an interview is: problem → design choice → working result → test → limitation → your contribution.
