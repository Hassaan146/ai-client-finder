"use strict";
const $ = id => document.getElementById(id);
let runId = null, poll = null;
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };

// ── option lists ────────────────────────────────────────────────────────────
const LEAD_TYPES = [
  ["companies_web", "Company websites", true],
  ["local_business", "Local businesses (needs location)", true],
  ["job_posts", "Job posts / hiring", false],
  ["community_intent", "Community intent (Reddit/forums)", false],
  ["news_signals", "News / funding signals", false],
];
const SERVICES = ["AI automations & chatbots", "WhatsApp automation", "Voice AI / cold-calling agents",
  "Workflow automation (Zapier/Make/n8n)", "Web design & development", "Shopify store setup", "SEO",
  "Google & Meta paid ads", "Email marketing", "Social media management", "Content writing / copywriting",
  "Video editing", "Graphic design", "UI/UX design", "Branding & identity", "Lead generation",
  "CRM setup & automation", "Mobile app development", "E-commerce management", "Virtual assistant / admin",
  "Bookkeeping & accounting", "Data scraping & enrichment", "Business consulting", "Photography / videography"];
const NICHES = ["Restaurants", "Cafes & coffee shops", "Dental clinics", "Medical clinics", "Law firms",
  "Real estate agencies", "Gyms & fitness studios", "Salons & spas", "E-commerce / Shopify stores",
  "SaaS startups", "Digital marketing agencies", "Construction companies", "Auto dealerships & repair",
  "Hotels & hospitality", "Travel agencies", "Coaching & online courses", "Accounting firms",
  "Insurance agencies", "Interior designers", "Event planners", "Home services (plumbers/electricians)",
  "Cleaning services", "Manufacturers", "Retail shops", "Fashion brands", "Photographers", "Nonprofits", "Consultants"];
const LOCATIONS = ["Remote / Global", "Lahore", "Karachi", "Islamabad", "Dubai", "Abu Dhabi", "Riyadh",
  "Doha", "London", "Manchester", "New York", "Los Angeles", "Chicago", "Toronto", "Sydney", "Melbourne",
  "Singapore", "Mumbai", "Delhi", "Bangalore", "Berlin", "Amsterdam", "Paris", "Madrid", "San Francisco",
  "Austin", "Kuala Lumpur", "Cairo"];

const checkedVals = menuEl => [...menuEl.querySelectorAll("input.opt:checked")].map(c => c.value);

// generic multi-select dropdown: options + optional "Select all" + optional custom-add
function buildMenu(menuEl, items, opts, onChange) {
  opts = opts || {};
  menuEl.textContent = "";
  if (opts.selectAll) {
    const l = el("label", "selall");
    const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "selall-cb";
    cb.addEventListener("change", () => {
      menuEl.querySelectorAll("input.opt").forEach(o => { o.checked = cb.checked; });
      onChange();
    });
    l.appendChild(cb); l.appendChild(document.createTextNode("Select all"));
    menuEl.appendChild(l);
  }
  const addOpt = (val, label, checked) => {
    const l = el("label");
    const cb = document.createElement("input");
    cb.type = "checkbox"; cb.className = "opt"; cb.value = val; cb.checked = !!checked;
    cb.addEventListener("change", onChange);
    l.appendChild(cb); l.appendChild(document.createTextNode(label));
    menuEl.appendChild(l);
    return l;
  };
  items.forEach(it => Array.isArray(it) ? addOpt(it[0], it[1], it[2]) : addOpt(it, it, false));
  menuEl._addOpt = addOpt;
  if (opts.custom) {
    const row = el("div", "dd-custom");
    const inp = document.createElement("input"); inp.placeholder = "add your own…";
    const btn = el("button", "ghost", "Add");
    const add = () => {
      const v = inp.value.trim(); if (!v) return;
      const node = addOpt(v, v, true);
      menuEl.insertBefore(node, row);           // keep custom row at bottom
      inp.value = ""; onChange();
    };
    btn.onclick = add;
    inp.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); add(); } });
    row.appendChild(inp); row.appendChild(btn); menuEl.appendChild(row);
  }
}

function wireDropdown(ddId, headId, menuId, summaryFn) {
  const dd = $(ddId), head = $(headId), menu = $(menuId);
  head.addEventListener("click", e => { e.stopPropagation(); dd.classList.toggle("open"); });
  menu.addEventListener("click", e => e.stopPropagation());
  return () => head.textContent = summaryFn();
}
document.addEventListener("click", () => document.querySelectorAll(".dd.open").forEach(d => d.classList.remove("open")));

const countSummary = (menuId, empty) => () => {
  const sel = checkedVals($(menuId));
  return sel.length ? (sel.length <= 2 ? sel.join(", ") : `${sel.length} selected`) : empty;
};
const typesSummary = () => {
  const sel = checkedVals($("menu-types"));
  const names = LEAD_TYPES.filter(t => sel.includes(t[0])).map(t => t[1].split(" (")[0]);
  return names.length ? (names.length <= 2 ? names.join(", ") : `${names.length} selected`) : "Pick at least one";
};
let refreshers = {};

async function initDropdowns() {
  const mk = (id, head, menu, items, opts, summary) => {
    buildMenu($(menu), items, opts, () => refreshers[menu]());
    refreshers[menu] = wireDropdown(id, head, menu, summary);
    refreshers[menu]();
  };
  mk("dd-service", "head-service", "menu-service", SERVICES, { selectAll: true, custom: true }, countSummary("menu-service", "Pick services…"));
  mk("dd-niche", "head-niche", "menu-niche", NICHES, { selectAll: true, custom: true }, countSummary("menu-niche", "Pick niches…"));
  mk("dd-location", "head-location", "menu-location", LOCATIONS, { selectAll: true, custom: true }, countSummary("menu-location", "Any / Remote…"));
  mk("dd-types", "head-types", "menu-types", LEAD_TYPES, { selectAll: true }, typesSummary);
  let srcItems = [];
  try {
    const r = await fetch("/api/sources"); const d = await r.json();
    srcItems = (d.sources || []).filter(s => s.active).map(s => [s.name, `${s.name} · tier ${s.tier}`, false]);
  } catch (e) { /* auto */ }
  mk("dd-sources", "head-sources", "menu-sources", srcItems, { selectAll: true }, countSummary("menu-sources", "Auto (all active sources)"));
}
initDropdowns();

// ── flow ────────────────────────────────────────────────────────────────────
$("btn-start").onclick = async () => {
  const lead_types = checkedVals($("menu-types"));
  if (!lead_types.length) { alert("Pick at least one 'What to find' option"); return; }
  const body = {
    service: checkedVals($("menu-service")), niche: checkedVals($("menu-niche")),
    location: checkedVals($("menu-location")), notes: $("notes").value.trim(),
    max_leads: parseInt($("max_leads").value) || 8,
    lead_types, sources: checkedVals($("menu-sources")),
  };
  if (!body.service.length || !body.niche.length) { alert("Pick (or add) at least one Service and one Niche"); return; }
  $("btn-start").disabled = true;
  try {
    const r = await fetch("/api/runs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error((await r.json()).detail || r.status);
    runId = (await r.json()).id;
    $("p-plan").classList.remove("hide"); $("plan-status").textContent = "(planning…)";
    $("p-plan").scrollIntoView({ behavior: "smooth" });
    poll = setInterval(tick, 2000);
  } catch (e) { alert("Error: " + e.message); $("btn-start").disabled = false; }
};

$("btn-approve").onclick = async () => {
  $("btn-approve").disabled = true;
  const r = await fetch(`/api/runs/${runId}/approve`, { method: "POST" });
  if (!r.ok) { alert("approve failed"); $("btn-approve").disabled = false; return; }
  $("p-progress").classList.remove("hide"); $("p-progress").scrollIntoView({ behavior: "smooth" });
};

$("btn-reject").onclick = () => {
  clearInterval(poll); runId = null;
  $("p-plan").classList.add("hide"); $("btn-start").disabled = false; window.scrollTo(0, 0);
};

async function tick() {
  if (!runId) return;
  const r = await fetch(`/api/runs/${runId}`); if (!r.ok) return;
  const d = await r.json();
  $("run-status").textContent = d.status;
  $("log").textContent = (d.log || []).join("\n"); $("log").scrollTop = 1e9;
  if (d.plan && $("plan-body").childElementCount === 0) renderPlan(d.plan);
  $("plan-status").textContent = d.status === "plan_ready" ? "(awaiting your approval)" : `(${d.status})`;
  $("btn-approve").disabled = d.status !== "plan_ready";
  if (d.status === "done" || d.status === "failed") {
    clearInterval(poll);
    if (d.status === "failed") { $("log").textContent += "\nERROR: " + d.error; $("run-status").classList.add("err"); }
    renderCards(d.cards || []);
  } else if (["sourcing", "ranking", "diagnosing"].includes(d.status)) {
    $("p-progress").classList.remove("hide"); renderCards(d.cards || []);
  }
}

function renderPlan(p) {
  const b = $("plan-body"); b.textContent = "";
  b.appendChild(el("div", "kv", "ICP: " + (p.icp || "—")));
  (p.tiers || []).forEach(t => {
    const s = el("div", "sec"); s.appendChild(el("b", "", "Tier " + (t.tier || "?") + " — " + (t.goal || "")));
    const ul = el("ul"); (t.queries || []).forEach(q => ul.appendChild(el("li", "", q))); s.appendChild(ul);
    b.appendChild(s);
  });
  if (p.ranking_criteria && p.ranking_criteria.length) {
    const s = el("div", "sec"); s.appendChild(el("b", "", "Ranking criteria"));
    const ul = el("ul"); p.ranking_criteria.forEach(c => ul.appendChild(el("li", "", c))); s.appendChild(ul); b.appendChild(s);
  }
}

function renderCards(cards) {
  const box = $("cards"); box.textContent = "";
  if (!cards.length) return;
  box.appendChild(el("p", "cardT", `Ranked leads (${cards.length})`));
  cards.forEach(c => {
    const p = el("div", "panel");
    if (c.priority) p.classList.add("priority");
    const h = el("p", "cardT");
    h.appendChild(el("span", "badge rank", "#" + c.rank));
    if (c.priority) h.appendChild(el("span", "badge first", "★ CONTACT FIRST"));
    h.appendChild(document.createTextNode(" " + c.title + " "));
    h.appendChild(el("span", "badge score", (c.fit_score || 0).toFixed(0) + "/10"));
    h.appendChild(el("span", "badge tier", c.source + "·" + c.tier));
    p.appendChild(h);
    if (c.fit_reason) p.appendChild(el("div", "kv", "why ranked here: " + c.fit_reason));
    if (c.url) { const a = el("a", "", c.url); a.href = c.url; a.target = "_blank"; a.rel = "noopener noreferrer"; p.appendChild(a); }

    // ── prominent CONTACT block ──
    const cs = el("div", "sec contact");
    cs.appendChild(el("b", "", "Contact"));
    if (c.person || c.role) cs.appendChild(el("div", "kv", "👤 " + [c.person, c.role].filter(Boolean).join(" — ")));
    if (c.email) {
      const row = el("div", "contact-email");
      const dot = el("span", "estat estat-" + (c.email_status || "unverified"));
      row.appendChild(dot);
      const a = el("a", "", c.email); a.href = "mailto:" + c.email; row.appendChild(a);
      row.appendChild(el("span", "kv", " (" + (c.email_status || "unverified") + ")"));
      const cp = el("button", "ghost mini", "copy"); cp.onclick = () => navigator.clipboard.writeText(c.email);
      row.appendChild(cp);
      cs.appendChild(row);
    } else { cs.appendChild(el("div", "kv", "no email found — try the website / socials below")); }
    if (c.phone) cs.appendChild(el("div", "kv", "📞 " + c.phone));
    (c.socials || []).forEach(s => { const a = el("a", "kv-a", s); a.href = s; a.target = "_blank"; a.rel = "noopener noreferrer"; cs.appendChild(a); });
    p.appendChild(cs);
    const an = c.analysis || {};
    if (an.requirement) { const s = el("div", "sec"); s.appendChild(el("b", "", "Requirement")); s.appendChild(el("div", "", an.requirement)); p.appendChild(s); }
    if (an.analyzer) { const s = el("div", "sec"); s.appendChild(el("b", "", "Analyzer — what they want")); s.appendChild(el("div", "", an.analyzer)); p.appendChild(s); }
    if (an.problems && an.problems.length) {
      const s = el("div", "sec"); s.appendChild(el("b", "", "Problems"));
      const ul = el("ul"); an.problems.forEach(x => ul.appendChild(el("li", "", (x.problem || "") + (x.evidence ? " (evidence: " + x.evidence + ")" : "")))); s.appendChild(ul); p.appendChild(s);
    }
    if (an.solutions && an.solutions.length) {
      const s = el("div", "sec"); s.appendChild(el("b", "", "Solutions & impact"));
      const ul = el("ul"); an.solutions.forEach(x => ul.appendChild(el("li", "", (x.solution || "") + " → " + (x.impact || "") + " — " + (x.why_it_matters || "")))); s.appendChild(ul); p.appendChild(s);
    }
    if (an.disclaimer) p.appendChild(el("div", "kv", an.disclaimer));
    const o = c.outreach || {};
    if (o.message) {
      const s = el("div", "sec");
      s.appendChild(el("b", "", "Outreach (" + (o.genre || "") + " · " + (o.channel || "") + ")"));
      if (o.why_this_genre) s.appendChild(el("div", "kv", o.why_this_genre));
      if (o.subject) s.appendChild(el("div", "kv", "subject: " + o.subject));
      s.appendChild(el("div", "msg", o.message));
      const btn = el("button", "ghost", "Copy message");
      btn.onclick = () => navigator.clipboard.writeText((o.subject ? o.subject + "\n\n" : "") + o.message);
      s.appendChild(btn); p.appendChild(s);
    }
    if (c.validator_notes && c.validator_notes.length) p.appendChild(el("div", "kv", "validators: " + c.validator_notes.join(" | ")));
    box.appendChild(p);
  });
}
