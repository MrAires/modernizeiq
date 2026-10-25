"""Escape all repository-derived content; export a self-contained offline report."""

from html import escape
from pathlib import Path


def h(value: object) -> str:
    return escape(str(value), quote=True)


def evidence_links(ids: list[str]) -> str:
    return " ".join(f'<a href="#{h(identifier)}">{h(identifier)}</a>' for identifier in ids)


def table(headers: list[str], rows: list[list[str]]) -> str:
    return '<div class="table-scroll"><table><thead><tr>' + ''.join(f'<th>{h(t)}</th>' for t in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def render_html(data: dict) -> str:
    css = Path(__file__).with_name("report.css").read_text(encoding="utf-8")
    profile, score = data["profile"], data["readiness"]
    refs = {e["id"]: e for e in data["evidence"]}
    meta = [("Primary language", profile["primary_language"]), ("Framework", ", ".join(profile["frameworks"]) or "Not detected"),
            ("Database", ", ".join(profile["databases"]) or "Not detected"), ("Files inspected", profile["files_analyzed"]),
            ("Declared dependencies", profile["dependencies_declared"]), ("Test files", profile["test_files"])]
    identity = ''.join(f'<div><dt>{h(key)}</dt><dd>{h(value)}</dd></div>' for key, value in meta)
    nodes = ''.join(f'<div class="node"><span>{h(n["kind"])}</span><strong>{h(n["label"])}</strong><small>{len(n["evidence_ids"])} evidence references</small></div>' for n in data["architecture"]["nodes"])
    edges = ''.join(f'<li><strong>{h(e["from"])} → {h(e["to"])}</strong><span>{h(e["relation"])}</span></li>' for e in data["architecture"]["edges"])
    dimensions = ''.join(f'<div class="dimension"><label>{h(c["category"])}<strong>{c["score"]:.0f}<small> / 100</small></strong></label><meter min="0" max="100" value="{c["score"]}">{c["score"]}</meter></div>' for c in score["categories"])
    priority = ''.join(f'<li><b class="pill">{h(r["priority"])}</b><div><strong>{h(r["title"])}</strong><small>{h(r["phase"])} · {h(r["effort"])} effort · {len(r["finding_ids"])} finding(s)</small></div></li>' for r in sorted(data["recommendations"], key=lambda r: (r["priority"], r["id"]))[:4])
    risk_rows = []
    for finding in sorted(data["findings"], key=lambda f: ({"high": 0, "medium": 1, "low": 2}[f["severity"]], f["rule_id"], f["id"])):
        first = refs[finding["evidence_ids"][0]]
        location = first["file"] + (f':{first["line"]}' if first["line"] else "")
        detail = f'<details><summary>{h(finding["title"])}</summary><p>{h(finding["explanation"])}</p><p><b>Action:</b> {h(finding["action"])}</p><small>{h(finding["confidence"])} · {h(finding["rule_id"])}</small></details>'
        risk_rows.append([f'<span class="severity {h(finding["severity"])}">{h(finding["severity"])}</span>', detail, h(finding["category"]), f'<code>{h(location)}</code><br>{evidence_links(finding["evidence_ids"])}'])
    risks = table(["Severity", "Finding / expand for rationale", "Category", "Evidence"], risk_rows)
    dep_rows = [[h(d["name"]), f'<code>{h(d["version"])}</code>', h(d["ecosystem"]), h(d["scope"]), h(d["file"]), "Not checked"] for d in data["dependencies"]]
    dependencies = table(["Dependency", "Declared version", "Ecosystem", "Scope", "Manifest", "CVE / age / deprecation"], dep_rows)
    phases = []
    for phase in ("Stabilize", "Prepare", "Automate", "Modernize"):
        items = [r for r in data["recommendations"] if r["phase"] == phase]
        if not items:
            continue
        actions = ''.join(f'<article class="action"><span>{h(r["priority"])} · {h(r["effort"])} effort · {h(r["impact"])} impact</span><p>{h(r["title"])}</p><small>Evidence: {len(r["evidence_ids"])} · Proposed for review</small>' + (f'<small>Prerequisites: {h(", ".join(r["depends_on"]))}</small>' if r["depends_on"] else '') + '</article>' for r in items)
        phases.append(f'<div class="phase"><h3>{h(phase)}</h3>{actions}</div>')
    calculations = ''.join('<details class="calculation"><summary>' + h(c["category"]) + f' — {c["earned"]} / {c["possible"]} points; weight {c["weight"]}</summary>' + table(["Check", "Result", "Points", "Evidence"], [[h(check["label"]), h(check["status"]), f'{check["points_earned"]} / {check["points_possible"]}', evidence_links(check["evidence_ids"])] for check in c["checks"]]) + '</details>' for c in score["categories"])
    evidence = ''.join(f'<details id="{h(e["id"])}" class="evidence"><summary><code>{h(e["id"])}</code> · {h(e["file"])}{":" + str(e["line"]) if e["line"] else ""}</summary><p>{h(e["description"])}</p><small>Rule: {h(e["rule_id"])}</small><small>File SHA-256: {h(e["file_sha256"] or "Inventory-level observation")}</small></details>' for e in data["evidence"])
    warnings = ''.join(f'<li>{h(w["file"])}: {h(w["message"])}</li>' for w in data["warnings"])
    skipped = ''.join(f'<li><code>{h(s["path"])}</code>: {h(s["reason"])}</li>' for s in data["skipped"])
    limitations = ''.join(f'<li>{h(item)}</li>' for item in data["limitations"])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>ModernizeIQ — {h(data['name'])}</title><style>{css}</style></head>
<body><a class="skip" href="#workbench">Skip to assessment</a><aside><a class="brand" href="#workbench"><b>M<span>IQ</span></b><strong>ModernizeIQ<small>MODERNIZATION ASSESSMENT</small></strong></a><nav aria-label="Report sections"><a href="#workbench">01 &nbsp; Workbench</a><a href="#risks">02 &nbsp; Risk register</a><a href="#dependencies">03 &nbsp; Dependencies</a><a href="#roadmap">04 &nbsp; Modernization plan</a><a href="#scoring">05 &nbsp; Scoring method</a><a href="#evidence">06 &nbsp; Evidence inspector</a><a href="#scope">07 &nbsp; Scope & limitations</a></nav><div class="aside-foot">DETERMINISTIC BASELINE<br><span>No LLM · Local static analysis</span></div></aside>
<main><header><span>REPOSITORY ASSESSMENT</span><strong>{h(data['name'])}</strong><a href="assessment.json" download>Export JSON ↗</a></header><section id="workbench"><div class="intro"><div><p class="eyebrow">Understand the legacy. Plan the transformation.</p><h1>Modernization workbench</h1><p class="subtitle">Evidence first. Decisions remain yours.</p></div><span class="run-state">{h(data['status'])}<small>Analyzer {h(data['analyzer_version'])} · Rules {h(score['config_version'])}</small></span></div><dl class="identity">{identity}</dl>
<div class="workbench"><article class="panel architecture"><p class="eyebrow">Current state · inferred</p><h2>{h(data['architecture']['style'])}</h2><p>{h(data['architecture']['caution'])}</p><div class="node-map">{nodes}</div><ul class="edges">{edges or '<li>No supported relationship inferred.</li>'}</ul><div class="architect-note"><b>Architecture judgment</b><p>{h(data['architecture']['strategy'])}</p></div></article><article class="panel readiness"><div class="score-heading"><div><p class="eyebrow">Readiness assessment</p><h2>Signals to act on</h2></div><strong>{score['overall']:.1f}<small>/ 100</small></strong></div>{dimensions}<p class="disclaimer">Heuristic score. Test coverage and security effectiveness are not measured.</p></article></div><article class="panel priorities"><div><p class="eyebrow">Start here</p><h2>Priority actions</h2></div><ol>{priority or '<li>No recommendation generated within supported scope.</li>'}</ol></article></section>
<section id="risks"><p class="eyebrow">Review before remediation</p><h2>Risk register <span class="count">{len(data['findings'])} indicators</span></h2><p class="section-note">Expand a finding to inspect its rationale. Possible security issues require confirmation.</p>{risks}</section>
<section id="dependencies"><p class="eyebrow">Declared inventory</p><h2>Dependencies</h2><p class="section-note">No package installation, transitive resolution or vulnerability service was used.</p>{dependencies}</section>
<section id="roadmap"><p class="eyebrow">Evidence-backed sequence</p><h2>Transformation roadmap</h2><p class="section-note">Effort and impact are qualitative rule defaults, not cost or delivery estimates.</p><div class="roadmap">{''.join(phases)}</div></section>
<section id="scoring"><p class="eyebrow">Transparent by design</p><h2>Check every point</h2><p class="section-note">{h(score['formula'])}. Unknown checks receive zero credit. Expand a dimension for the full calculation.</p>{calculations}</section>
<section id="evidence"><p class="eyebrow">Traceable observations</p><h2>Evidence inspector</h2><p class="section-note">Locations and fixed descriptions only. Source excerpts and matched values are never copied.</p>{evidence}</section>
<section id="scope"><p class="eyebrow">Assessment boundary</p><h2>Scope and limitations</h2><ul class="limitations">{limitations}</ul><details><summary>{len(data['warnings'])} parser/analysis warnings</summary><ul>{warnings or '<li>None reported.</li>'}</ul></details><details><summary>{len(data['skipped'])} skipped entries</summary><ul>{skipped or '<li>None reported.</li>'}</ul></details><p class="hash">Snapshot SHA-256: {h(data['snapshot_sha256'])}<br>Scoring configuration SHA-256: {h(score['config_sha256'])}</p></section><footer>ModernizeIQ · Deterministic assessment report · Use your browser’s Print command for a light print layout.</footer></main></body></html>'''


def executive_text(data: dict) -> str:
    lines = [f"ModernizeIQ — {data['name']}", "Executive assessment", "",
             f"Readiness heuristic: {data['readiness']['overall']} / 100",
             f"Inspected: {data['profile']['files_analyzed']} supported files",
             f"Architecture hypothesis: {data['architecture']['style']}", "",
             "Recommended priorities (human confirmation required):"]
    for rec in sorted(data["recommendations"], key=lambda r: (r["priority"], r["id"]))[:5]:
        lines.append(f"- {rec['priority']} / {rec['phase']}: {rec['title']}")
    lines += ["", "Business implication: configuration, reliability and delivery risks should be understood before moving the application.",
              "No migration cost, timeline or savings are estimated from source code alone.",
              "Assessment limits: static indicators only; no code execution, vulnerability lookup, measured coverage or LLM."]
    return "\n".join(lines) + "\n"
