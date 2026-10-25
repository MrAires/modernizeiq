const product = document.body.dataset.product;
const modern = product === "ModernizeIQ";
const $ = (s, root = document) => root.querySelector(s);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const date = (value) =>
  new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
const time = (value) =>
  new Date(value).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
const num = (value) =>
  Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 });
const icons = {
  grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
  pulse: "M2 12h5l3-8 4 16 3-8h5",
  upload: "M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6",
  layers: "m12 3 10 5-10 5L2 8l10-5Zm-10 9 10 5 10-5M2 16l10 5 10-5",
  graph: "M5 4h5v5H5zM14 15h5v5h-5zM2 15h5v5H2zM7 9v3H4v3m3-3h9v3",
  alert: "m12 3 10 18H2L12 3Zm0 6v5m0 3v1",
  search: "M20 20l-5-5m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0",
  check: "M4 12l5 5L20 6",
  compare: "M7 3v18M3 7l4-4 4 4m6 14V3m-4 14 4 4 4-4",
  file: "M6 2h8l5 5v15H6V2Zm8 0v6h5M9 12h7m-7 4h7",
  clock: "M12 8v5l3 2m7-3a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  book: "M3 3h7l2 2 2-2h7v17h-7l-2 2-2-2H3V3Zm9 2v17",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  play: "m8 4 13 8-13 8V4Z",
  box: "m12 2 9 5v10l-9 5-9-5V7l9-5ZM3 7l9 5 9-5m-9 5v10",
  close: "m6 6 12 12M6 18 18 6",
  download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
  flag: "M5 22V3m0 0c5-5 9 5 15 0v10c-6 5-10-5-15 0",
  shield: "m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6l9-4Z",
};
const icon = (name, size = 18) =>
  `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${icons[name] || icons.box}"/></svg>`;
const navItems = modern
  ? [
      ["portfolio", "Portfolio", "grid"],
      ["assessment", "Workbench", "layers"],
      ["architecture", "Architecture", "graph"],
      ["dependencies", "Dependencies", "box"],
      ["findings", "Risk register", "alert"],
      ["roadmap", "Transformation plan", "flag"],
      ["review", "Decisions", "check"],
      ["compare", "Compare assessments", "compare"],
      ["reports", "Reports", "file"],
      ["audit", "Audit trail", "clock"],
      ["import", "New assessment", "upload"],
      ["guide", "Getting started", "book"],
    ]
  : [
      ["portfolio", "Mission control", "grid"],
      ["assessment", "Investigation", "pulse"],
      ["services", "Service health", "layers"],
      ["signals", "Observability", "graph"],
      ["findings", "Incidents", "alert"],
      ["evidence", "Evidence explorer", "search"],
      ["review", "Review queue", "check"],
      ["compare", "Experiments", "compare"],
      ["reports", "Reports & exports", "file"],
      ["audit", "Activity log", "clock"],
      ["import", "Data sources", "upload"],
      ["guide", "Getting started", "book"],
    ];
const page = location.pathname.slice(1) || "portfolio";
let runs = [],
  run = null,
  reviews = [],
  selected = new URLSearchParams(location.search).get("run");
let toastTimer;
const link = (target, id = selected) =>
  "/" + target + (id ? "?run=" + encodeURIComponent(id) : "");
const button = (label, target, kind = "secondary") =>
  `<a class="button ${kind}" href="${link(target)}">${label}</a>`;
const pill = (label, kind = "neutral") =>
  `<span class="pill ${kind}">${esc(label)}</span>`;
const empty = (title, detail, action = "") =>
  `<div class="empty">${icon("layers", 34)}<h3>${esc(title)}</h3><p>${esc(detail)}</p>${action}</div>`;
const table = (heads, rows) =>
  `<div class="table-scroll"><table><thead><tr>${heads.map((h) => "<th>" + esc(h) + "</th>").join("")}</tr></thead><tbody>${rows.map((row) => "<tr>" + row.map((cell) => "<td>" + cell + "</td>").join("") + "</tr>").join("")}</tbody></table></div>`;
function toast(message, bad = false) {
  const el = $("#toast");
  el.textContent = message;
  el.className = "visible" + (bad ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = ""), 6000);
}
async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = { detail: "Unable to reach the server" };
    }
    throw Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  }
  return response.json();
}
const data = () => run?.payload || {};
const latestReviews = () =>
  Object.fromEntries([...reviews].reverse().map((r) => [r.item, r]));
const statusOf = (f) => latestReviews()[f.id]?.decision || "open";
const totalFindings = () => runs.reduce((s, r) => s + r.findings, 0);
const title = (eyebrow, heading, sub, actions = "") =>
  `<div class="page-title"><div><p class="eyebrow">${eyebrow}</p><h1>${heading}</h1><p class="subtitle">${sub}</p></div><div class="actions">${actions}</div></div>`;
const panelHead = (label, title, action = "") =>
  `<div class="panel-head"><div><span class="eyebrow">${label}</span><h2>${title}</h2></div>${action}</div>`;
function metric(label, value, note, kind = "", symbol = "pulse") {
  return `<article class="metric ${kind}"><div class="metric-label">${label}${icon(symbol)}</div><strong>${value}</strong><span>${note}</span></article>`;
}
function chart(points, key, threshold = null, compact = false) {
  if (!points?.length)
    return empty("No samples", "Import metric observations to view a chart.");
  const reduced = points.filter(
    (_, i) =>
      i % Math.max(1, Math.floor(points.length / 240)) === 0 ||
      i === points.length - 1,
  );
  const factor = key === "error_rate" ? 100 : 1;
  const max =
    Math.max(
      ...points.map((p) => p[key] * factor),
      threshold === null ? 0 : threshold * factor,
      1,
    ) * 1.14;
  const width = 800,
    height = compact ? 90 : 220,
    pad = compact ? 6 : 28;
  const firstTime = Date.parse(points[0].timestamp),
    span = Math.max(1, Date.parse(points.at(-1).timestamp) - firstTime);
  const coords = reduced
    .map(
      (p) =>
        `${pad + ((Date.parse(p.timestamp) - firstTime) * (width - 2 * pad)) / span},${height - pad - ((p[key] * factor) / max) * (height - 2 * pad)}`,
    )
    .join(" ");
  const thresholdY =
    threshold === null
      ? null
      : height - pad - ((threshold * factor) / max) * (height - 2 * pad);
  return `<div class="chart ${compact ? "compact" : ""}"><svg role="img" aria-label="${esc(key)} over time" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">${compact ? "" : [0.25, 0.5, 0.75].map((y) => `<line class="gridline" x1="${pad}" y1="${y * height}" x2="${width - pad}" y2="${y * height}"/>`).join("")}<polygon class="chart-fill" points="${pad},${height - pad} ${coords} ${width - pad},${height - pad}"/><polyline class="chart-line" points="${coords}"/>${thresholdY === null ? "" : `<line class="threshold" x1="${pad}" x2="${width - pad}" y1="${thresholdY}" y2="${thresholdY}"/>`}</svg>${compact ? "" : `<div class="chart-labels"><span>${time(points[0].timestamp)}</span><span>0–${num(max)} ${key === "error_rate" ? "%" : "ms"}${threshold === null ? "" : ` · dashed threshold: ${num(threshold * factor)}`}</span><span>${time(points.at(-1).timestamp)}</span></div>`}</div>`;
}
function primaryService() {
  const d = data();
  return (
    d.evidence?.find((e) => e.service)?.service ||
    Object.keys(d.services || {})[0]
  );
}
function scoreBars(categories, brief = false) {
  return `<div class="score-bars">${categories.map((c) => `<button class="score-row" data-category="${esc(c.category)}"><span>${esc(c.category)}</span><b>${c.score}<small>/100</small></b><i><em style="width:${Math.max(0, Math.min(100, c.score))}%" class="${c.score < 40 ? "low" : c.score >= 80 ? "good" : ""}"></em></i>${brief ? "" : `<small>${c.earned} of ${c.possible} points · weight ${c.weight}</small>`}</button>`).join("")}</div>`;
}
function architectureMap(target = false) {
  const d = data();
  let nodes = d.architecture?.nodes || [];
  if (target) {
    const rules = new Set((d.findings || []).map((f) => f.rule_id));
    nodes = [
      {
        id: "application",
        kind: "proposal",
        label: "Validate modular boundaries",
      },
      ...(rules.has("LOCAL_STORAGE")
        ? [
            {
              id: "storage",
              kind: "proposal",
              label: "Review external persistence",
            },
          ]
        : []),
      ...(rules.has("SECRET_LITERAL")
        ? [
            {
              id: "secrets",
              kind: "proposal",
              label: "Managed secret references",
            },
          ]
        : []),
      ...(rules.has("MISSING_CI")
        ? [
            {
              id: "delivery",
              kind: "proposal",
              label: "Tested delivery pipeline",
            },
          ]
        : []),
    ];
  }
  return `<div class="architecture-map ${target ? "proposed" : ""}"><div class="map-label">${target ? "PROPOSED REVIEW AREAS" : "INFERRED FROM SOURCE"}</div>${nodes.map((n, i) => `<button class="architecture-node ${i === 0 ? "primary-node" : ""}" data-node="${esc(n.id)}" data-proposed="${target}"><span class="node-icon">${icon(n.kind === "database" ? "layers" : n.kind === "external" ? "graph" : n.id === "application" ? "box" : "shield", 22)}</span><span><small>${esc(n.kind)}</small><strong>${esc(n.label)}</strong></span><span class="node-arrow">${icon("arrow", 15)}</span></button>`).join("")}<p>${target ? "Proposals require validation of scale, ownership, durability and cost." : "Static relationships are hypotheses, not a runtime call graph."}</p></div>`;
}
function findingCards(limit = 4) {
  const d = data();
  return (
    (d.findings || [])
      .slice(0, limit)
      .map(
        (f) =>
          `<button class="finding-card" data-finding="${esc(f.id)}"><span class="severity-icon ${esc(f.severity)}">${icon("alert")}</span><span><small>${esc(f.category)} · ${esc(f.rule_id || "Sustained window")}</small><strong>${esc(f.title)}</strong><em>${esc(f.action)}</em></span>${pill(statusOf(f))}${icon("arrow", 16)}</button>`,
      )
      .join("") ||
    empty(
      "No matching findings",
      "The selected checks did not find an issue in this snapshot. This is not a guarantee of health or security.",
    )
  );
}
function frame() {
  const name = navItems.find((n) => n[0] === page)?.[1] || "Workspace";
  const options = runs
    .map(
      (r) =>
        `<option value="${esc(r.id)}" ${r.id === selected ? "selected" : ""}>${esc(r.name)}</option>`,
    )
    .join("");
  $("#app").innerHTML =
    `<aside class="sidebar"><a href="/portfolio" class="brand"><img src="/workspace-assets/logo.svg" alt="${product} logo"><span>${product}<small>${modern ? "MODERNIZATION INTELLIGENCE" : "INCIDENT INTELLIGENCE"}</small></span></a><div class="workspace-label">${modern ? "YOUR WORKSPACE" : "OPERATIONS WORKSPACE"}</div><nav class="side-nav" aria-label="Main navigation">${navItems.map(([p, label, i]) => `<a href="${link(p)}" aria-label="${esc(label)}" title="${esc(label)}" class="${page === p ? "active" : ""}">${icon(i)}<span>${label}</span>${p === "findings" && data().findings?.length ? "<b>" + data().findings.length + "</b>" : ""}</a>`).join("")}</nav><div class="sidebar-bottom"><span class="status-dot"></span><div>Local workspace<small>Data stays on this machine</small></div></div></aside><div class="app-body"><header class="topbar"><div class="breadcrumb">Workspace <span>/</span> <strong>${esc(name)}</strong></div><div class="topbar-actions"><button class="ghost demo-button" data-demo>${icon("play", 16)} Explore demo</button><a class="button primary small" href="/import">${icon("upload", 16)} ${modern ? "New assessment" : "Import telemetry"}</a></div></header><div class="contextbar"><div><span class="context-label">${modern ? "APPLICATION" : "INVESTIGATION"}</span><select id="run-select" aria-label="Active assessment">${options || "<option>No assessments</option>"}</select></div><div class="context-meta">${run ? pill(run.context.kind === "demo" ? "DEMO DATA" : "YOUR IMPORT", run.context.kind === "demo" ? "demo" : "success") : ""}<span>${run ? date(run.created) : "Ready to begin"}</span></div></div><main id="main" tabindex="-1"><div id="page"></div></main><footer>${product} Studio · Evidence first. Human decisions.<a href="/guide">How this works ${icon("arrow", 13)}</a></footer></div>`;
  $("#run-select").onchange = (e) => {
    localStorage.setItem(product + "-run", e.target.value);
    location.href = link(page, e.target.value);
  };
}
function portfolio() {
  const d = data(),
    current = data().findings?.length || 0;
  const intro = modern
    ? title(
        "APPLICATION PORTFOLIO",
        "Understand what comes next.",
        "Turn repository evidence into a modernization plan you can explain.",
        button(
          icon("upload", 16) + " Assess a repository",
          "import",
          "primary",
        ),
      )
    : title(
        "OPERATIONS / OVERVIEW",
        "Mission control",
        "Every signal, investigation and decision. One place to work.",
        button(icon("upload", 16) + " Connect your data", "import", "primary"),
      );
  let html =
    intro +
    `<section class="welcome-strip"><span class="welcome-icon">${icon(modern ? "layers" : "pulse", 24)}</span><div><strong>${run?.context.kind === "demo" ? "A working demo, ready to explore." : "Your data. A traceable investigation."}</strong><p>${modern ? "Explore the baseline and improved control, inspect evidence, then try your own repository." : "Follow the checkout incident, compare it with healthy traffic, then import your own telemetry."}</p></div>${button("Open " + (modern ? "workbench" : "investigation") + " " + icon("arrow", 16), "assessment")}</section>`;
  html += `<div class="metrics-grid">${metric(modern ? "Applications assessed" : "Saved investigations", runs.length, "Separate, persistent snapshots", "", "layers")}${metric(modern ? "Selected readiness" : "Signal breaches", modern ? (d.readiness?.overall ?? "—") + "/100" : current, modern ? "Transparent weighted heuristic" : "Sustained multi-signal windows", current ? "attention" : "", "pulse")}${metric(
    "High-priority findings",
    runs.reduce((s, r) => s + r.high, 0),
    "Across saved assessments",
    "attention",
    "alert",
  )}${metric("Review decisions", reviews.length, "For the selected snapshot", "", "check")}</div>`;
  if (modern) {
    html += `<div class="split modern-feature"><section class="panel">${panelHead("FEATURED ASSESSMENT", esc(run?.name || "Application"), button("Open workbench →", "assessment", "text"))}<div class="feature-profile">${pill(d.profile?.primary_language || "Unknown")}${(d.profile?.frameworks || []).map((x) => pill(x)).join("")}<span>${d.profile?.files_analyzed || 0} files inspected</span></div>${architectureMap()}</section><section class="panel">${panelHead("READINESS AT A GLANCE", "Where to focus", pill("Rule-based"))}${scoreBars((d.readiness?.categories || []).slice(0, 6), true)}${button("View all dimensions →", "assessment", "text")}</section></div>`;
  } else {
    const service = primaryService();
    html += `<div class="split"><section class="panel">${panelHead("PRIMARY SIGNAL", "Service latency", `<span class="legend"><i></i> ${esc(service || "Service")}</span>`)}<div class="chart-heading"><strong>${num(Math.max(...(d.services?.[service] || []).map((p) => p.latency_p95_ms), 0))}<small> ms peak P95</small></strong>${pill(current ? "BREACH DETECTED" : "NO MATCHING BREACH", current ? "danger" : "success")}</div>${chart(d.services?.[service], "latency_p95_ms", d.parameters?.latency_ms)}<div class="panel-bottom">Recorded observations for the selected snapshot ${button("Explore signals →", "signals", "text")}</div></section><section class="panel focus-panel">${panelHead("INVESTIGATION FOCUS", current ? "Signals need attention" : "No matching incidents")}${findingCards(2)}<div class="note">${icon("shield")}<span>Symptoms are detected from your settings. Causation requires additional evidence.</span></div>${button("Open investigation →", "assessment", "primary")}</section></div>`;
  }
  html += `<section class="panel portfolio-table">${panelHead(modern ? "APPLICATION INVENTORY" : "INVESTIGATION HISTORY", modern ? "Your assessments" : "Recent investigations", `<label class="search-input">${icon("search", 16)}<input id="portfolio-search" placeholder="Search projects…" aria-label="Search projects"></label>`)}<div id="portfolio-rows"></div></section>`;
  $("#page").innerHTML = html;
  const draw = () => {
    const q = $("#portfolio-search").value.toLowerCase();
    const filtered = runs.filter((r) => r.name.toLowerCase().includes(q));
    $("#portfolio-rows").innerHTML = table(
      [
        "Project",
        "Source",
        modern ? "Readiness" : "Services",
        "Findings",
        "Assessed",
        "",
      ],
      filtered.map((r) => [
        `<a class="project-name" href="${link("assessment", r.id)}"><span class="project-icon">${icon(modern ? "box" : "pulse")}</span><strong>${esc(r.name)}</strong></a>`,
        pill(
          r.context.kind === "demo" ? "Demo" : "Imported",
          r.context.kind === "demo" ? "demo" : "neutral",
        ),
        modern
          ? "<b>" + r.score + "/100</b>"
          : String(r.profile.services ?? "—"),
        pill(r.findings + " findings", r.findings ? "warning" : "success"),
        '<span class="muted">' + date(r.created) + "</span>",
        `<a aria-label="Open ${esc(r.name)}" href="${link("assessment", r.id)}">${icon("arrow")}</a>`,
      ]),
    );
  };
  $("#portfolio-search").oninput = draw;
  draw();
}
function assessment() {
  const d = data();
  let html = title(
    modern ? "APPLICATION / ASSESSMENT" : "INCIDENT / INVESTIGATION",
    modern ? "Modernization workbench" : "Follow the evidence.",
    esc(run.name),
    button("Export report " + icon("download", 16), "reports"),
  );
  if (modern) {
    html += `<div class="assessment-band"><div><small>READINESS HEURISTIC</small><strong>${d.readiness.overall}<em>/100</em></strong></div><dl><dt>Language</dt><dd>${esc(d.profile.primary_language)}</dd><dt>Framework</dt><dd>${esc(d.profile.frameworks.join(", ") || "Not detected")}</dd></dl><dl><dt>Files inspected</dt><dd>${d.profile.files_analyzed}</dd><dt>Dependencies</dt><dd>${d.dependencies.length}</dd></dl><dl><dt>Findings</dt><dd>${d.findings.length}</dd><dt>Scope</dt><dd>${esc(d.status)}</dd></dl></div><div class="split"><section class="panel">${panelHead("CURRENT ARCHITECTURE", esc(d.architecture.style), button("Expand map →", "architecture", "text"))}${architectureMap()}<div class="note">${icon("shield")}<span>${esc(d.architecture.strategy)}</span></div></section><section class="panel">${panelHead("TRANSPARENT SCORING", "Readiness dimensions", pill("Inspect any score"))}${scoreBars(d.readiness.categories)}</section></div><section class="panel">${panelHead("PRIORITY FINDINGS", "Start with the evidence", button("All risks →", "findings", "text"))}${findingCards(5)}</section>`;
  } else {
    const s = primaryService(),
      findings = d.findings || [];
    html += `<div class="investigation-banner ${findings.length ? "incident" : "healthy"}"><span class="banner-icon">${icon(findings.length ? "alert" : "check", 28)}</span><div><p class="eyebrow">${findings.length ? "SUSTAINED MULTI-SIGNAL BREACH" : "NO MATCHING MULTI-SIGNAL WINDOW"}</p><h2>${findings.length ? findings.length + " detected episode(s) across observed services" : "No incident detected with these settings"}</h2><p>${d.parameters.consecutive_samples} samples · P95 ≥ ${d.parameters.latency_ms} ms · error rate ≥ ${num(d.parameters.error_rate * 100)}%</p></div>${pill("HUMAN REVIEW")}</div><div class="split"><section class="panel">${panelHead("SIGNAL CORRELATION", esc(s))}${chart(d.services?.[s], "latency_p95_ms", d.parameters.latency_ms)}<p class="chart-caption">P95 latency · milliseconds</p>${chart(d.services?.[s], "error_rate", d.parameters.error_rate)}<p class="chart-caption">Error rate · percent</p></section><section class="panel">${panelHead("OBSERVED TIMELINE", "What happened")}<div class="timeline">${d.evidence.map((e, i) => `<button data-evidence="${esc(e.id)}"><span class="timeline-number">${i + 1}</span><div><small>${time(e.observations[0].timestamp)}</small><strong>${esc(e.service)}</strong><p>${e.observations.length} consecutive observations breached both thresholds.</p></div>${icon("arrow", 15)}</button>`).join("") || empty("No breach timeline", "Try the incident demo or review your imported signals.")}</div><div class="note">${icon("shield")}<span>No deployment or trace correlation was supplied by this metric-only import. A root cause is not established.</span></div></section></div><section class="panel">${panelHead("NEXT STEPS", "Investigation queue", button("Record decisions →", "review", "text"))}${findingCards(20)}</section>`;
  }
  $("#page").innerHTML = html;
}
function services() {
  const d = data();
  $("#page").innerHTML =
    title(
      "SERVICE INVENTORY",
      "Health, service by service.",
      "Inspect every imported service without relying on fixed service names.",
    ) +
    `<div class="service-grid">${Object.entries(d.services || {})
      .map(([name, points]) => {
        const affected = d.evidence.some((e) => e.service === name);
        return `<article class="panel service-card"><div class="service-card-title"><span class="service-symbol">${icon("layers", 24)}</span>${pill(affected ? "Breach observed" : "No matching breach", affected ? "danger" : "success")}</div><h2>${esc(name)}</h2><p>${points.length} observations · ${time(points[0].timestamp)}–${time(points.at(-1).timestamp)}</p>${chart(points, "latency_p95_ms", null, true)}<div class="service-numbers"><div><small>Latest P95</small><b>${num(points.at(-1).latency_p95_ms)} ms</b></div><div><small>Latest errors</small><b>${num(points.at(-1).error_rate * 100)}%</b></div></div><a class="text-link" href="${link("signals") + "&service=" + encodeURIComponent(name)}">Inspect signals ${icon("arrow", 15)}</a></article>`;
      })
      .join("")}</div>`;
}
function signals() {
  const d = data();
  const preferred =
    new URLSearchParams(location.search).get("service") || primaryService();
  $("#page").innerHTML =
    title(
      "OBSERVABILITY",
      "Signals over time.",
      "Examine recorded values against the exact detection thresholds.",
    ) +
    `<div class="filterbar"><label>Service<select id="signal-service">${Object.keys(
      d.services || {},
    )
      .map(
        (s) =>
          `<option ${s === preferred ? "selected" : ""}>${esc(s)}</option>`,
      )
      .join(
        "",
      )}</select></label><label>Metric<select id="signal-metric"><option value="latency_p95_ms">P95 latency (ms)</option><option value="error_rate">Error rate (%)</option></select></label></div><section class="panel" id="signal-chart"></section><section class="panel">${panelHead("OBSERVATION TABLE", "Recorded samples", pill("Latest 200 shown"))}<div id="signal-table"></div></section>`;
  const draw = () => {
    const service = $("#signal-service").value,
      key = $("#signal-metric").value,
      points = d.services[service] || [];
    $("#signal-chart").innerHTML =
      panelHead("TIME SERIES", esc(service)) +
      chart(
        points,
        key,
        key === "error_rate"
          ? d.parameters.error_rate
          : d.parameters.latency_ms,
      );
    $("#signal-table").innerHTML = table(
      ["Timestamp", "P95 latency", "Error rate", "Both thresholds breached"],
      points
        .slice(-200)
        .map((p) => [
          esc(p.timestamp),
          num(p.latency_p95_ms) + " ms",
          num(p.error_rate * 100) + "%",
          pill(
            p.latency_p95_ms >= d.parameters.latency_ms &&
              p.error_rate >= d.parameters.error_rate
              ? "Yes"
              : "No",
            p.latency_p95_ms >= d.parameters.latency_ms &&
              p.error_rate >= d.parameters.error_rate
              ? "danger"
              : "neutral",
          ),
        ]),
    );
  };
  $("#signal-service").onchange = draw;
  $("#signal-metric").onchange = draw;
  draw();
}
function findingPage() {
  const d = data();
  $("#page").innerHTML =
    title(
      modern ? "RISK / REGISTER" : "INCIDENT / REGISTER",
      modern ? "Make risk reviewable." : "An actionable incident register.",
      "Filter observations, inspect supporting evidence, and record a decision.",
      button("Review queue →", "review", "primary"),
    ) +
    `<div class="filterbar"><label class="search-input">${icon("search")}<input id="finding-search" placeholder="Search findings or rules…" aria-label="Search findings"></label><label>Severity<select id="severity"><option value="">All severities</option><option>high</option><option>medium</option><option>low</option></select></label><label>Status<select id="finding-status"><option value="">All statuses</option><option>open</option><option>accepted</option><option>rejected</option><option>deferred</option><option>investigate</option></select></label></div><section class="panel" id="finding-table"></section>`;
  const draw = () => {
    const q = $("#finding-search").value.toLowerCase(),
      severity = $("#severity").value,
      status = $("#finding-status").value;
    const rows = d.findings.filter(
      (f) =>
        (!severity || f.severity === severity) &&
        (!status || statusOf(f) === status) &&
        JSON.stringify(f).toLowerCase().includes(q),
    );
    $("#finding-table").innerHTML =
      panelHead("EVIDENCE-BASED REGISTER", rows.length + " findings") +
      table(
        ["Severity", "Finding", "Category", "Status", "Evidence", ""],
        rows.map((f) => [
          pill(f.severity, f.severity === "high" ? "danger" : "warning"),
          `<button class="table-title" data-finding="${esc(f.id)}">${esc(f.title)}<small>${esc(f.rule_id || f.id)}</small></button>`,
          esc(f.category),
          pill(statusOf(f)),
          f.evidence_ids.length + " references",
          `<button class="icon-button" aria-label="Inspect ${esc(f.title)}" data-finding="${esc(f.id)}">${icon("arrow")}</button>`,
        ]),
      );
    if (!rows.length)
      $("#finding-table").innerHTML += empty(
        "No findings match these filters",
        "Try another severity, status or search phrase.",
      );
  };
  ["finding-search", "severity", "finding-status"].forEach(
    (id) => ($("#" + id).oninput = draw),
  );
  draw();
}
function evidencePage() {
  const d = data();
  $("#page").innerHTML =
    title(
      "EVIDENCE / EXPLORER",
      "Every claim has a source.",
      "Search observations and inspect file locations or metric windows.",
    ) +
    `<label class="search-input wide">${icon("search")}<input id="evidence-search" placeholder="Search file, service, description or rule…" aria-label="Search evidence"></label><div class="evidence-grid" id="evidence-list"></div>`;
  const draw = () => {
    const q = $("#evidence-search").value.toLowerCase();
    $("#evidence-list").innerHTML =
      d.evidence
        .filter((e) => JSON.stringify(e).toLowerCase().includes(q))
        .map(
          (e) =>
            `<button class="panel evidence-card" data-evidence="${esc(e.id)}"><div>${icon(modern ? "file" : "pulse")}${pill(e.rule_id || "Metric window")}</div><h3>${esc(e.file || e.service)}</h3><p>${esc(e.description)}</p><small>${e.line ? "Line " + e.line + " · " : ""}${esc(e.id)}</small><span class="text-link">Inspect evidence ${icon("arrow", 14)}</span></button>`,
        )
        .join("") ||
      empty("No matching evidence", "Try another search phrase.");
  };
  $("#evidence-search").oninput = draw;
  draw();
}
function architecture() {
  const d = data();
  $("#page").innerHTML =
    title(
      "ARCHITECTURE / EXPLORER",
      "See the application clearly.",
      "Distinguish observed structure from proposals that need human validation.",
    ) +
    `<div class="segmented"><button class="active" data-map="current">Current state</button><button data-map="target">Proposed review areas</button><button data-map="both">Compare views</button></div><div id="map-view"></div><section class="panel">${panelHead("RELATIONSHIPS", "Inferred connections")}${table(
      ["From", "To", "Relationship", "Evidence"],
      d.architecture.edges.map((e) => [
        esc(e.from),
        esc(e.to),
        esc(e.relation),
        e.evidence_ids
          .map(
            (id) =>
              `<button class="text-button" data-evidence="${esc(id)}">${esc(id)}</button>`,
          )
          .join(" "),
      ]),
    )}<div class="note">${icon("shield")}<span>${esc(d.architecture.strategy)}</span></div></section>`;
  const draw = (mode) => {
    $("#map-view").className = mode === "both" ? "split" : "";
    $("#map-view").innerHTML =
      (mode !== "target"
        ? '<section class="panel">' +
          panelHead("OBSERVED", esc(d.architecture.style)) +
          architectureMap() +
          "</section>"
        : "") +
      (mode !== "current"
        ? '<section class="panel">' +
          panelHead("PROPOSED", "Validate before redesign") +
          architectureMap(true) +
          "</section>"
        : "");
    document
      .querySelectorAll("[data-map]")
      .forEach((b) => b.classList.toggle("active", b.dataset.map === mode));
  };
  document
    .querySelectorAll("[data-map]")
    .forEach((b) => (b.onclick = () => draw(b.dataset.map)));
  draw("current");
}
function dependencies() {
  const d = data();
  $("#page").innerHTML =
    title(
      "DEPENDENCY / INTELLIGENCE",
      "Know what you depend on.",
      "Declared packages, version constraints and evidence. No unsupported vulnerability claims.",
    ) +
    `<div class="metrics-grid three">${metric("Declared dependencies", d.dependencies.length, "Parsed from supported manifests", "", "box")}${metric("Exact versions", d.dependencies.filter((x) => x.pinned).length, "Declarations with exact release pins", "", "check")}${metric("Vulnerability assessment", "Not checked", "No advisory lookup has been run", "", "shield")}</div><div class="filterbar"><label class="search-input">${icon("search")}<input id="dep-search" placeholder="Find a package…" aria-label="Search dependencies"></label><label>Ecosystem<select id="ecosystem"><option value="">All ecosystems</option>${[...new Set(d.dependencies.map((x) => x.ecosystem))].map((x) => "<option>" + esc(x) + "</option>").join("")}</select></label></div><section class="panel" id="dep-table"></section>`;
  const draw = () => {
    const q = $("#dep-search").value.toLowerCase(),
      ecosystem = $("#ecosystem").value;
    $("#dep-table").innerHTML = table(
      [
        "Package",
        "Declared version",
        "Ecosystem",
        "Scope",
        "Source",
        "Evidence",
      ],
      d.dependencies
        .filter(
          (x) =>
            (!ecosystem || x.ecosystem === ecosystem) &&
            x.name.toLowerCase().includes(q),
        )
        .map((x) => [
          `<strong>${esc(x.name)}</strong>`,
          `<code>${esc(x.version)}</code><br>${pill(x.pinned ? "Exact pin" : "Review resolution", x.pinned ? "success" : "warning")}`,
          esc(x.ecosystem),
          esc(x.scope),
          `<code>${esc(x.file)}${x.line ? ":" + x.line : ""}</code>`,
          x.evidence_ids
            .map(
              (id) =>
                `<button class="icon-button" aria-label="Inspect dependency evidence" data-evidence="${esc(id)}">${icon("search")}</button>`,
            )
            .join(""),
        ]),
    );
  };
  $("#dep-search").oninput = draw;
  $("#ecosystem").onchange = draw;
  draw();
}
function roadmap() {
  const d = data();
  const phases = ["Stabilize", "Prepare", "Automate", "Modernize"];
  $("#page").innerHTML =
    title(
      "TRANSFORMATION / PLAN",
      "A sequence you can defend.",
      "Proposed actions linked to real findings. Effort and impact are qualitative estimates.",
      button("Review findings →", "review", "primary"),
    ) +
    `<div class="roadmap-board">${phases
      .map((phase, i) => {
        const items = (d.recommendations || []).filter(
          (r) => r.phase === phase,
        );
        return `<section class="roadmap-column"><div class="roadmap-heading"><span>0${i + 1}</span><h2>${phase}</h2><b>${items.length}</b></div>${items.map((r) => `<article class="roadmap-card">${pill(r.priority, r.priority === "P0" ? "danger" : "warning")}<h3>${esc(r.title)}</h3><div class="roadmap-tags"><span>${esc(r.effort)} effort</span><span>${esc(r.impact)} impact</span></div><p>${r.finding_ids.length} linked findings · ${r.evidence_ids.length} evidence references</p>${r.depends_on.length ? "<small>Prerequisites: " + esc(r.depends_on.join(", ")) + "</small>" : ""}<button class="text-button" data-finding="${esc(r.finding_ids[0])}">Inspect supporting finding ${icon("arrow", 14)}</button></article>`).join("") || '<div class="roadmap-empty">No action generated in this phase.</div>'}</section>`;
      })
      .join("")}</div>`;
}
function reviewPage() {
  const d = data();
  const latest = latestReviews();
  $("#page").innerHTML =
    title(
      "HUMAN / REVIEW",
      modern ? "Put judgment on record." : "Decide the next step.",
      "Accept, reject, defer, or request more investigation. Your rationale becomes part of the audit trail.",
    ) +
    `<div class="split review-layout"><section class="panel">${panelHead("REVIEW QUEUE", d.findings.length + " findings")}<div class="review-list">${d.findings.map((f) => `<button data-review-item="${esc(f.id)}"><span>${pill(f.severity, f.severity === "high" ? "danger" : "warning")}<strong>${esc(f.title)}</strong></span>${pill(latest[f.id]?.decision || "open")}</button>`).join("") || empty("Nothing to review", "No finding was generated for this snapshot.")}</div></section><section class="panel" id="review-form-wrap"></section></div>`;
  const choose = (id) => {
    const f = d.findings.find((x) => x.id === id);
    if (!f) return;
    document
      .querySelectorAll("[data-review-item]")
      .forEach((b) =>
        b.classList.toggle("selected", b.dataset.reviewItem === id),
      );
    $("#review-form-wrap").innerHTML =
      `<p class="eyebrow">SELECTED FINDING</p><h2>${esc(f.title)}</h2><p class="muted">${esc(f.action)}</p><button class="text-button" data-finding="${esc(f.id)}">Review the evidence ${icon("arrow", 15)}</button><form id="decision-form"><input type="hidden" name="item" value="${esc(f.id)}"><label>Decision<select name="decision"><option value="accepted">Accept finding</option><option value="investigate">Investigate further</option><option value="deferred">Defer for later</option><option value="rejected">Reject finding</option></select></label><label>Rationale<textarea name="note" required minlength="1" maxlength="2000" placeholder="What did you verify? What supports your decision?"></textarea></label><button class="button primary" type="submit">${icon("check", 16)} Record decision</button><p class="form-note">This records your review. It does not execute remediation or modify source code.</p></form>`;
    $("#decision-form").onsubmit = async (e) => {
      e.preventDefault();
      const submit = $("button[type=submit]", e.target);
      submit.disabled = true;
      try {
        await api("/api/runs/" + selected + "/reviews", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(Object.fromEntries(new FormData(e.target))),
        });
        reviews = await api("/api/runs/" + selected + "/reviews");
        reviewPage();
        toast("Decision saved. View its history in Audit trail.");
      } catch (err) {
        toast(err.message, true);
        submit.disabled = false;
      }
    };
  };
  document
    .querySelectorAll("[data-review-item]")
    .forEach((b) => (b.onclick = () => choose(b.dataset.reviewItem)));
  if (d.findings.length) choose(d.findings[0].id);
  else
    $("#review-form-wrap").innerHTML = empty(
      "Review queue is clear",
      "Import another snapshot or explore a demo.",
    );
}
async function comparePage() {
  const options = runs
    .map((r) => `<option value="${esc(r.id)}">${esc(r.name)}</option>`)
    .join("");
  $("#page").innerHTML =
    title(
      "RESEARCH / COMPARISON",
      "Make the change measurable.",
      "Compare two saved snapshots and their settings before drawing a conclusion.",
    ) +
    `<div class="compare-controls panel"><label>Baseline<select id="before">${options}</select></label><span class="compare-icon">${icon("compare", 24)}</span><label>Comparison<select id="after">${options}</select></label><button id="compare-button" class="button primary">Compare snapshots</button></div><div id="comparison"></div>`;
  if (runs.length > 1) $("#after").selectedIndex = 1;
  const draw = async () => {
    const a = $("#before").value,
      b = $("#after").value;
    if (!a || !b) return;
    if (a === b) {
      $("#comparison").innerHTML = empty(
        "Choose two different snapshots",
        "A baseline and a changed or control run make the comparison useful.",
      );
      return;
    }
    try {
      const [left, right] = await Promise.all([
        api("/api/runs/" + a),
        api("/api/runs/" + b),
      ]);
      const la = left.payload,
        ra = right.payload;
      const delta = ra.findings.length - la.findings.length;
      const configA = la.parameters || la.readiness.config_sha256,
        configB = ra.parameters || ra.readiness.config_sha256;
      const compatible = JSON.stringify(configA) === JSON.stringify(configB);
      let html = `<div class="comparison-summary"><div><span class="eyebrow">FINDING COUNT CHANGE</span><strong>${delta > 0 ? "+" : ""}${delta}</strong><p>${la.findings.length} → ${ra.findings.length} findings</p></div>${modern ? `<div><span class="eyebrow">READINESS CHANGE</span><strong>${num(ra.readiness.overall - la.readiness.overall)}</strong><p>${la.readiness.overall} → ${ra.readiness.overall} /100</p></div>` : ""}<div>${pill(compatible ? "Matching analysis settings" : "Analysis settings differ", compatible ? "success" : "warning")}<p>${compatible ? "Review input differences before attributing improvement." : "Changed settings can affect results. This is not an isolated input experiment."}</p></div></div>`;
      if (modern) {
        html +=
          '<section class="panel">' +
          panelHead("DIMENSION COMPARISON", "Where the scores changed") +
          table(
            ["Dimension", left.name, right.name, "Change"],
            la.readiness.categories.map((c) => {
              const other = ra.readiness.categories.find(
                (x) => x.category === c.category,
              );
              return [
                esc(c.category),
                String(c.score),
                String(other?.score ?? "—"),
                other ? num(other.score - c.score) : "—",
              ];
            }),
          ) +
          "</section>";
      }
      const counts = (d) => {
        const map = new Map();
        d.findings.forEach((f) => {
          const key = f.rule_id || f.title;
          map.set(key, (map.get(key) || 0) + 1);
        });
        return map;
      };
      const x = counts(la),
        y = counts(ra);
      html +=
        '<section class="panel">' +
        panelHead("FINDING DIFFERENCES", "Evidence categories") +
        table(
          ["Rule or symptom", "Baseline", "Comparison", "Change"],
          [...new Set([...x.keys(), ...y.keys()])].map((k) => [
            esc(k),
            String(x.get(k) || 0),
            String(y.get(k) || 0),
            String((y.get(k) || 0) - (x.get(k) || 0)),
          ]),
        ) +
        "</section>";
      $("#comparison").innerHTML = html;
    } catch (e) {
      toast(e.message, true);
    }
  };
  $("#compare-button").onclick = draw;
  if (runs.length > 1) await draw();
}
function reports() {
  const d = data();
  $("#page").innerHTML =
    title(
      "DELIVERABLES / EXPORT",
      "Ready for the next conversation.",
      "Share findings, decisions and reproducible evidence in the format your audience needs.",
    ) +
    `<div class="report-grid"><article class="panel report-card"><span class="report-art">${icon("file", 42)}</span><p class="eyebrow">HUMAN-READABLE</p><h2>Assessment report</h2><p>A clean, printable report with purpose, findings, priorities, review history and an evidence appendix.</p><a class="button primary" target="_blank" rel="noopener" href="/api/runs/${selected}/report">Open report ${icon("arrow", 16)}</a><small>Use Print → Save as PDF in the report.</small></article><article class="panel report-card"><span class="report-art">${icon("box", 42)}</span><p class="eyebrow">REPRODUCIBLE RESEARCH</p><h2>Full evidence package</h2><p>Structured assessment data, analysis parameters, context and all recorded reviews in a JSON file.</p><a class="button secondary" href="/api/runs/${selected}/export">Download JSON ${icon("download", 16)}</a></article><article class="panel report-card"><span class="report-art">${icon("grid", 42)}</span><p class="eyebrow">SPREADSHEET-READY</p><h2>Finding register</h2><p>Export finding IDs, severity, categories and recommended actions for your research or tracking sheet.</p><a class="button secondary" href="/api/runs/${selected}/findings.csv">Download CSV ${icon("download", 16)}</a></article></div><section class="panel">${panelHead("EXPORT SCOPE", esc(run.name))}<div class="report-summary">${pill(d.findings.length + " findings")}${pill(d.evidence.length + " evidence records")}${pill(reviews.length + " review decisions")}${pill(run.context.kind === "demo" ? "Educational demo" : "User import")}</div><p class="muted">${esc(run.context.objective || "No objective was supplied.")}</p></section>`;
}
function audit() {
  $("#page").innerHTML =
    title(
      "GOVERNANCE / HISTORY",
      "A record of human decisions.",
      "An append-only review history for this assessment. New decisions do not erase earlier ones.",
    ) +
    `<section class="panel">${panelHead("ASSESSMENT ACTIVITY", reviews.length + " review decisions")}${reviews.length ? '<div class="audit-list">' + reviews.map((r) => `<article><span class="audit-icon">${icon(r.decision === "accepted" ? "check" : r.decision === "investigate" ? "search" : "clock")}</span><div><div>${pill(r.decision)}<small>${date(r.created)}</small></div><h3>${esc(data().findings.find((f) => f.id === r.item)?.title || r.item)}</h3><p>${esc(r.note)}</p><code>${esc(r.item)}</code></div></article>`).join("") + "</div>" : empty("Your decision history starts here", "Review a finding and record your rationale. It will appear here with a timestamp.", button("Open review queue →", "review", "primary"))}</section>`;
}
function importPage() {
  $("#page").innerHTML =
    title(
      modern ? "SOURCE / INGESTION" : "TELEMETRY / INGESTION",
      modern ? "Bring your application." : "Bring your own signals.",
      modern
        ? "A safe static assessment starts with a source repository ZIP."
        : "Import time-series measurements and choose the detection settings.",
    ) +
    `<div class="split import-layout"><form class="panel import-form" id="upload-form">${panelHead("01 / SOURCE", modern ? "Repository upload" : "Telemetry upload")}<label class="dropzone" id="dropzone">${icon("upload", 36)}<strong id="file-label">Drop a ${modern ? "ZIP" : "CSV or JSON"} file here</strong><span>or click to browse · maximum 10 MiB</span><input type="file" name="file" required accept="${modern ? ".zip" : ".csv,.json"}"></label><div class="field-row"><label>Project name<input name="name" required maxlength="120" placeholder="e.g. Commerce production review"></label><label>Business criticality<select name="criticality"><option>medium</option><option>high</option><option>low</option></select></label></div><label>Objective / research question<textarea name="objective" maxlength="1000" placeholder="What decision should this assessment support?"></textarea></label>${modern ? "" : `<div class="form-divider"></div>${panelHead("02 / DETECTION", "Set your thresholds")}<div class="field-row"><label>P95 latency threshold (ms)<input type="number" name="latency" min="1" value="1000" required></label><label>Error-rate threshold (fraction)<input type="number" name="error" min="0.0001" max="1" step="0.0001" value="0.05" required></label></div><div class="field-row"><label>Consecutive samples<input type="number" name="samples" min="2" max="100" value="3" required></label><label>Maximum sample gap (seconds)<input type="number" name="gap" min="1" max="86400" value="120" required></label></div>`}<div class="form-actions"><button class="button primary" type="submit">${icon("pulse", 17)} Analyze and save</button><span id="upload-status" role="status">Your source is never executed.</span></div><div id="upload-error" class="form-error" role="alert"></div></form><div><section class="panel import-help"><span class="eyebrow">START WITH A WORKING EXAMPLE</span><h2>Explore before you upload.</h2><p>${modern ? "The demo includes a legacy commerce repository and an improved control. Both are analyzed by the real engine." : "The demo includes sustained degradation, healthy traffic and transient spikes across six services."}</p><button class="button secondary" data-demo>${icon("play", 16)} Load demo workspace</button><a class="text-link" href="/api/sample">Download sample ${modern ? "repository" : "telemetry"} ${icon("download", 15)}</a></section><section class="panel"><p class="eyebrow">INPUT CONTRACT</p><h2>${modern ? "What gets inspected" : "Required columns"}</h2>${modern ? '<ul class="plain-list"><li>Supported UTF-8 source and configuration</li><li>Dependency declarations and selected code patterns</li><li>Testing, container and delivery indicators</li><li>Unsafe ZIP paths and excessive sizes are rejected</li></ul>' : '<div class="schema-list"><code>timestamp</code><span>ISO 8601 with timezone or Z</span><code>service_id</code><span>Your service name</span><code>latency_p95_ms</code><span>Nonnegative milliseconds</span><code>error_rate</code><span>Fraction from 0 to 1</span></div>'}<div class="note">${icon("shield")}<span>Files stay on this machine. Business context is saved for review and does not silently alter technical evidence.</span></div></section></div></div>`;
  const form = $("#upload-form"),
    fileInput = form.elements.file,
    zone = $("#dropzone");
  const changed = () => {
    const file = fileInput.files[0];
    $("#file-label").textContent = file ? file.name : "Choose a source file";
    if (file && !form.elements.name.value)
      form.elements.name.value = file.name.replace(/\.[^.]+$/, "");
    zone.classList.toggle("has-file", !!file);
  };
  fileInput.onchange = changed;
  zone.ondragover = (e) => {
    e.preventDefault();
    zone.classList.add("dragging");
  };
  zone.ondragleave = () => zone.classList.remove("dragging");
  zone.ondrop = (e) => {
    e.preventDefault();
    zone.classList.remove("dragging");
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      changed();
    }
  };
  form.onsubmit = async (e) => {
    e.preventDefault();
    const file = fileInput.files[0],
      submit = $("button[type=submit]", form);
    $("#upload-error").textContent = "";
    try {
      if (!file) throw Error("Select a file first.");
      if (file.size > 10485760)
        throw Error("This file exceeds the 10 MiB upload limit.");
      if (!(modern ? /\.zip$/i : /\.(csv|json)$/i).test(file.name))
        throw Error("Choose a supported file type.");
      submit.disabled = true;
      $("#upload-status").textContent =
        "Inspecting source and calculating evidence…";
      const params = new URLSearchParams();
      for (const key of [
        "name",
        "criticality",
        "objective",
        "latency",
        "error",
        "samples",
        "gap",
      ])
        if (form.elements[key]) params.set(key, form.elements[key].value);
      const result = await api("/api/import?" + params, {
        method: "POST",
        headers: {
          "Content-Type": /\.csv$/i.test(file.name)
            ? "text/csv"
            : "application/octet-stream",
        },
        body: file,
      });
      localStorage.setItem(product + "-run", result.id);
      location.href = link("assessment", result.id);
    } catch (err) {
      $("#upload-error").textContent = err.message;
      $("#upload-status").textContent = "Correct the input and retry.";
      submit.disabled = false;
    }
  };
}
function guide() {
  $("#page").innerHTML =
    title(
      "PRODUCT / GUIDE",
      "A clear path from input to decision.",
      "Use the demo to learn the workflow, then bring your own evidence.",
    ) +
    `<div class="guide-grid">${[
      [
        "01",
        "Explore a real demo",
        "Load the built-in examples. They pass through the same analysis engine as user uploads.",
        "play",
      ],
      [
        "02",
        "Inspect the evidence",
        "Open a finding, inspect the source location or metric observations, and check the scoring or detection rule.",
        "search",
      ],
      [
        "03",
        "Record your judgment",
        "Accept, reject, defer or investigate with a written rationale. The audit keeps the history.",
        "check",
      ],
      [
        "04",
        "Compare and communicate",
        "Import changed data, compare snapshots, then export a readable report or reproducible JSON package.",
        "file",
      ],
    ]
      .map(
        ([n, t, p, i]) =>
          `<article class="panel guide-card"><div><b>${n}</b>${icon(i, 26)}</div><h2>${t}</h2><p>${p}</p></article>`,
      )
      .join(
        "",
      )}</div><section class="panel">${panelHead("HANDS-ON EXPERIMENT", "Make one change. Predict the outcome.")}<p>${modern ? "Download the sample repository. Change DEBUG=True to DEBUG=False, zip it again, and import a new assessment. Compare the security score and debug finding against the baseline. Explain why other findings remain." : "Download the telemetry sample and import it using a 2,000 ms latency threshold instead of 1,000 ms. Compare detected episodes against the demo. Explain why changing the threshold changes the result without changing the source data."}</p><div class="actions"><button class="button primary" data-demo>${icon("play", 16)} Open demo</button><a class="button secondary" href="/api/sample">Download sample</a></div></section><section class="panel">${panelHead("SCOPE AND LIMITS", "What these results mean")}<ul class="plain-list"><li>${modern ? "Scores are configurable static-analysis heuristics. Tests, CI and Docker presence do not prove runtime correctness." : "A sustained metric breach identifies a symptom. It does not prove a deployment or dependency caused it."}</li><li>Demo data is labelled. Your imports are retained as separate snapshots.</li><li>Review decisions do not execute infrastructure or source changes.</li><li>This is a local single-user workspace, not a public multi-tenant service.</li><li>Use independent labelled datasets to evaluate accuracy before making performance claims.</li></ul></section>`;
}
function openDrawer(title, body) {
  const dialog = $("#drawer");
  $("#drawer-content").innerHTML =
    `<div class="drawer-head"><div><p class="eyebrow">${modern ? "EVIDENCE / REVIEW" : "INVESTIGATION / DETAIL"}</p><h2>${esc(title)}</h2></div><button class="icon-button" id="close-drawer" aria-label="Close details">${icon("close", 22)}</button></div><div class="drawer-body">${body}</div>`;
  $("#close-drawer").onclick = () => dialog.close();
  if (!dialog.open) dialog.showModal();
}
function evidenceHTML(e) {
  return `<div class="evidence-detail"><div class="detail-meta">${pill(e.rule_id || "Metric observations")}<code>${esc(e.id)}</code></div><h3>${esc(e.file || e.service || "Inventory observation")}</h3>${e.line ? "<p>Source line <strong>" + e.line + "</strong></p>" : ""}<p>${esc(e.description)}</p>${
    e.observations
      ? table(
          ["Time", "P95", "Error rate"],
          e.observations.map((p) => [
            time(p.timestamp),
            num(p.latency_p95_ms) + " ms",
            num(p.error_rate * 100) + "%",
          ]),
        )
      : ""
  }${e.file_sha256 ? '<label>Source fingerprint<code class="hash">' + esc(e.file_sha256) + "</code></label>" : ""}</div>`;
}
document.addEventListener("click", async (event) => {
  const demo = event.target.closest("[data-demo]");
  if (demo) {
    demo.disabled = true;
    try {
      const result = await api("/api/demo", { method: "POST" });
      localStorage.setItem(product + "-run", result.primary);
      location.href = link("portfolio", result.primary);
    } catch (e) {
      toast(e.message, true);
      demo.disabled = false;
    }
    return;
  }
  const f = event.target.closest("[data-finding]");
  if (f) {
    const finding = data().findings.find((x) => x.id === f.dataset.finding);
    if (!finding) return;
    openDrawer(
      finding.title,
      `<div class="detail-meta">${pill(finding.severity, finding.severity === "high" ? "danger" : "warning")}${pill(statusOf(finding))}</div><h3>Observation</h3><p>${esc(finding.explanation || finding.title)}</p><h3>Recommended next step</h3><p>${esc(finding.action)}</p><h3>Supporting evidence</h3>${finding.evidence_ids
        .map((id) => data().evidence.find((e) => e.id === id))
        .filter(Boolean)
        .map(evidenceHTML)
        .join(
          "",
        )}<a class="button primary" href="${link("review")}">Record a decision ${icon("arrow", 15)}</a>`,
    );
    return;
  }
  const e = event.target.closest("[data-evidence]");
  if (e) {
    const evidence = data().evidence.find((x) => x.id === e.dataset.evidence);
    if (evidence) openDrawer("Evidence inspection", evidenceHTML(evidence));
    return;
  }
  const category = event.target.closest("[data-category]");
  if (category) {
    const c = data().readiness.categories.find(
      (x) => x.category === category.dataset.category,
    );
    openDrawer(
      c.category + " · " + c.score + "/100",
      `<div class="score-explanation"><strong>${c.earned} / ${c.possible}</strong><p>Earned points / possible points × 100. Overall weight: ${c.weight}.</p></div>${c.checks.map((check) => `<div class="check-row">${pill(check.status, check.status === "satisfied" ? "success" : check.status === "unknown" ? "warning" : "neutral")}<h3>${esc(check.label)}</h3><p>${check.points_earned} of ${check.points_possible} points</p>${check.evidence_ids.map((id) => `<button class="text-button" data-evidence="${esc(id)}">Inspect ${esc(id)}</button>`).join("")}</div>`).join("")}`,
    );
    return;
  }
  const node = event.target.closest("[data-node]");
  if (node) {
    if (node.dataset.proposed === "true") {
      openDrawer(
        "Proposed review area",
        "<p>This view suggests areas to validate using the detected findings. It is not an implemented or proven target architecture.</p>" +
          button("Inspect the risk register →", "findings", "primary"),
      );
      return;
    }
    const n = data().architecture.nodes.find((x) => x.id === node.dataset.node);
    openDrawer(
      n.label,
      `<p>${esc(data().architecture.caution)}</p>${
        n.evidence_ids
          .map((id) => data().evidence.find((e) => e.id === id))
          .filter(Boolean)
          .map(evidenceHTML)
          .join("") || "<p>Application-level structural hypothesis.</p>"
      }`,
    );
  }
});
$("#drawer").addEventListener("click", (e) => {
  if (e.target === $("#drawer")) $("#drawer").close();
});
async function start() {
  try {
    runs = await api("/api/runs");
    if (!runs.length) {
      await api("/api/demo", { method: "POST" });
      runs = await api("/api/runs");
    }
    selected = selected || localStorage.getItem(product + "-run");
    if (!runs.some((r) => r.id === selected)) selected = runs[0]?.id;
    if (selected) {
      [run, reviews] = await Promise.all([
        api("/api/runs/" + selected),
        api("/api/runs/" + selected + "/reviews"),
      ]);
      localStorage.setItem(product + "-run", selected);
    }
    frame();
    const handlers = {
      portfolio,
      assessment,
      services,
      signals,
      findings: findingPage,
      evidence: evidencePage,
      architecture,
      dependencies,
      roadmap,
      review: reviewPage,
      compare: comparePage,
      reports,
      audit,
      import: importPage,
      guide,
    };
    if (!run && !["portfolio", "import", "guide"].includes(page)) {
      $("#page").innerHTML = empty(
        "Choose an assessment",
        "Import your data or explore the demo first.",
        button("Import data", "import", "primary"),
      );
      return;
    }
    await (handlers[page] || portfolio)();
  } catch (e) {
    $("#app").innerHTML =
      `<main class="startup-error">${icon("alert", 40)}<h1>The workspace could not load.</h1><p>${esc(e.message)}</p><p>Keep START_WORKSPACE.bat running and refresh this page.</p><button class="button primary" onclick="location.reload()">Try again</button></main>`;
  }
}
start();
