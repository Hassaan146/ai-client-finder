"use strict";
const CONFIG = { POLL_MS: 2000, COPY_FEEDBACK_MS: 1400, MAX_POLL_FAILURES: 5 };
const $ = (id) => document.getElementById(id);
let runId = null,
  poll = null,
  approved = false,
  pollFailures = 0;
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
};

// ── option lists ────────────────────────────────────────────────────────────
const LEAD_TYPES = [
  ["companies_web", "Company websites", true],
  ["local_business", "Local businesses (needs location)", true],
  ["job_posts", "Job posts / hiring", false],
  ["community_intent", "Community intent (Reddit/forums)", false],
  ["news_signals", "News / funding signals", false],
];
const SERVICES = [
  "AI automations & chatbots",
  "WhatsApp automation",
  "Voice AI / cold-calling agents",
  "Workflow automation (Zapier/Make/n8n)",
  "Web design & development",
  "Shopify store setup",
  "SEO",
  "Google & Meta paid ads",
  "Email marketing",
  "Social media management",
  "Content writing / copywriting",
  "Video editing",
  "Graphic design",
  "UI/UX design",
  "Branding & identity",
  "Lead generation",
  "CRM setup & automation",
  "Mobile app development",
  "E-commerce management",
  "Virtual assistant / admin",
  "Bookkeeping & accounting",
  "Data scraping & enrichment",
  "Business consulting",
  "Photography / videography",
];
const NICHES = [
  "Restaurants",
  "Cafes & coffee shops",
  "Dental clinics",
  "Medical clinics",
  "Law firms",
  "Real estate agencies",
  "Gyms & fitness studios",
  "Salons & spas",
  "E-commerce / Shopify stores",
  "SaaS startups",
  "Digital marketing agencies",
  "Construction companies",
  "Auto dealerships & repair",
  "Hotels & hospitality",
  "Travel agencies",
  "Coaching & online courses",
  "Accounting firms",
  "Insurance agencies",
  "Interior designers",
  "Event planners",
  "Home services (plumbers/electricians)",
  "Cleaning services",
  "Manufacturers",
  "Retail shops",
  "Fashion brands",
  "Photographers",
  "Nonprofits",
  "Consultants",
];
const LOCATIONS = [
  "Remote / Global",
  "Lahore",
  "Karachi",
  "Islamabad",
  "Dubai",
  "Abu Dhabi",
  "Riyadh",
  "Doha",
  "London",
  "Manchester",
  "New York",
  "Los Angeles",
  "Chicago",
  "Toronto",
  "Sydney",
  "Melbourne",
  "Singapore",
  "Mumbai",
  "Delhi",
  "Bangalore",
  "Berlin",
  "Amsterdam",
  "Paris",
  "Madrid",
  "San Francisco",
  "Austin",
  "Kuala Lumpur",
  "Cairo",
];

const checkedVals = (menuEl) => [...menuEl.querySelectorAll("input.opt:checked")].map((c) => c.value);

// generic multi-select dropdown: options + optional "Select all" + optional custom-add
function buildMenu(menuEl, items, opts, onChange) {
  opts = opts || {};
  menuEl.textContent = "";
  if (opts.selectAll) {
    const l = el("label", "selall");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.className = "selall-cb";
    cb.addEventListener("change", () => {
      menuEl.querySelectorAll("input.opt").forEach((o) => {
        o.checked = cb.checked;
      });
      onChange();
    });
    l.appendChild(cb);
    l.appendChild(document.createTextNode("Select all"));
    menuEl.appendChild(l);
  }
  const addOpt = (val, label, checked) => {
    const l = el("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.className = "opt";
    cb.value = val;
    cb.checked = !!checked;
    cb.addEventListener("change", onChange);
    l.appendChild(cb);
    l.appendChild(document.createTextNode(label));
    menuEl.appendChild(l);
    return l;
  };
  items.forEach((it) => (Array.isArray(it) ? addOpt(it[0], it[1], it[2]) : addOpt(it, it, false)));
  menuEl._addOpt = addOpt;
  if (opts.custom) {
    const row = el("div", "dd-custom");
    const inp = document.createElement("input");
    inp.placeholder = "add your own…";
    const btn = el("button", "ghost", "Add");
    const add = () => {
      const v = inp.value.trim();
      if (!v) return;
      const node = addOpt(v, v, true);
      menuEl.insertBefore(node, row); // keep custom row at bottom
      inp.value = "";
      onChange();
    };
    btn.onclick = add;
    inp.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        add();
      }
    });
    row.appendChild(inp);
    row.appendChild(btn);
    menuEl.appendChild(row);
  }
}

function wireDropdown(ddId, headId, menuId, summaryFn) {
  const dd = $(ddId),
    head = $(headId),
    menu = $(menuId);
  head.setAttribute("aria-expanded", "false");
  head.addEventListener("click", (e) => {
    e.stopPropagation();
    dd.classList.toggle("open");
    head.setAttribute("aria-expanded", dd.classList.contains("open") ? "true" : "false");
  });
  menu.addEventListener("click", (e) => e.stopPropagation());
  return () => (head.textContent = summaryFn());
}
function closeDropdowns() {
  document.querySelectorAll(".dd.open").forEach((d) => {
    d.classList.remove("open");
    const head = d.querySelector(".dd-head");
    if (head) head.setAttribute("aria-expanded", "false");
  });
}
document.addEventListener("click", closeDropdowns);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeDropdowns();
});

const countSummary = (menuId, empty) => () => {
  const sel = checkedVals($(menuId));
  return sel.length ? (sel.length <= 2 ? sel.join(", ") : `${sel.length} selected`) : empty;
};
const typesSummary = () => {
  const sel = checkedVals($("menu-types"));
  const names = LEAD_TYPES.filter((t) => sel.includes(t[0])).map((t) => t[1].split(" (")[0]);
  return names.length
    ? names.length <= 2
      ? names.join(", ")
      : `${names.length} selected`
    : "Pick at least one";
};
const refreshers = {};

async function initDropdowns() {
  const mk = (id, head, menu, items, opts, summary) => {
    buildMenu($(menu), items, opts, () => refreshers[menu]());
    refreshers[menu] = wireDropdown(id, head, menu, summary);
    refreshers[menu]();
  };
  mk(
    "dd-service",
    "head-service",
    "menu-service",
    SERVICES,
    { selectAll: true, custom: true },
    countSummary("menu-service", "Pick services…"),
  );
  mk(
    "dd-niche",
    "head-niche",
    "menu-niche",
    NICHES,
    { selectAll: true, custom: true },
    countSummary("menu-niche", "Pick niches…"),
  );
  mk(
    "dd-location",
    "head-location",
    "menu-location",
    LOCATIONS,
    { selectAll: true, custom: true },
    countSummary("menu-location", "Any / Remote…"),
  );
  mk("dd-types", "head-types", "menu-types", LEAD_TYPES, { selectAll: true }, typesSummary);
  let srcItems = [];
  try {
    const r = await fetch("/api/sources");
    const d = await r.json();
    srcItems = (d.sources || [])
      .filter((s) => s.active)
      .map((s) => [s.name, `${s.name} · tier ${s.tier}`, false]);
  } catch (e) {
    /* auto */
  }
  mk(
    "dd-sources",
    "head-sources",
    "menu-sources",
    srcItems,
    { selectAll: true },
    countSummary("menu-sources", "Auto (all active sources)"),
  );
}
initDropdowns();

// ── UI feedback helpers ─────────────────────────────────────────────────────
function setStep(n) {
  // 1..4 — mark earlier steps done, current active
  [...$("steps").children].forEach((li, i) => {
    li.classList.toggle("done", i < n - 1);
    li.classList.toggle("active", i === n - 1);
  });
}
function formError(msg) {
  $("form-error").textContent = msg || "";
}
function copyToClipboard(text) {
  // navigator.clipboard needs https/localhost — textarea fallback otherwise
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(ta);
  }
  return Promise.resolve();
}
function copyBtn(cls, label, getText) {
  // copy with visible confirmation (closure/feedback)
  const b = el("button", cls, label);
  b.onclick = async () => {
    try {
      await copyToClipboard(getText());
    } catch (e) {
      /* best-effort */
    }
    const old = b.textContent;
    b.textContent = "Copied ✓";
    b.disabled = true;
    setTimeout(() => {
      b.textContent = old;
      b.disabled = false;
    }, CONFIG.COPY_FEEDBACK_MS);
  };
  return b;
}
const fitBand = (s) => (s >= 7 ? "fit-hi" : s >= 4 ? "fit-mid" : "fit-lo");

// ── flow ────────────────────────────────────────────────────────────────────
$("btn-start").onclick = async () => {
  formError("");
  const lead_types = checkedVals($("menu-types"));
  if (!lead_types.length) {
    formError("Pick at least one “What to find” option.");
    return;
  }
  const body = {
    service: checkedVals($("menu-service")),
    niche: checkedVals($("menu-niche")),
    location: checkedVals($("menu-location")),
    notes: $("notes").value.trim(),
    max_leads: parseInt($("max_leads").value, 10) || 8,
    lead_types,
    sources: checkedVals($("menu-sources")),
  };
  if (!body.service.length || !body.niche.length) {
    formError("Pick (or add) at least one Service and one Niche.");
    return;
  }
  $("btn-start").disabled = true;
  try {
    const r = await fetch("/api/runs", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json()).detail || r.status);
    runId = (await r.json()).id;
    // fresh-run state reset (supports "Start a new search" after done/failed)
    approved = false;
    pollFailures = 0;
    lastCardCount = -1;
    clearInterval(poll);
    $("plan-body").textContent = "";
    $("cards").textContent = "";
    $("run-status").textContent = "…";
    $("run-status").classList.remove("err", "ok");
    $("spinner").classList.remove("hide");
    $("p-progress").classList.add("hide");
    setStep(2);
    $("p-plan").classList.remove("hide");
    $("plan-status").textContent = "(planning…)";
    $("p-plan").scrollIntoView({ behavior: "smooth" });
    poll = setInterval(tick, CONFIG.POLL_MS);
  } catch (e) {
    formError("Error: " + e.message);
    $("btn-start").disabled = false;
  }
};

$("btn-approve").onclick = async () => {
  $("btn-approve").disabled = true;
  try {
    const r = await fetch(`/api/runs/${runId}/approve`, { method: "POST" });
    if (!r.ok) {
      formError("Approve failed — try again.");
      $("btn-approve").disabled = false;
      return;
    }
  } catch (e) {
    formError("Approve failed (network) — try again.");
    $("btn-approve").disabled = false;
    return;
  }
  approved = true; // tick() must never re-enable the button after this
  setStep(3);
  $("p-progress").classList.remove("hide");
  $("p-progress").scrollIntoView({ behavior: "smooth" });
};

$("btn-reject").onclick = () => {
  clearInterval(poll);
  runId = null;
  approved = false;
  pollFailures = 0;
  setStep(1);
  $("p-plan").classList.add("hide");
  $("p-progress").classList.add("hide");
  $("plan-body").textContent = "";
  $("cards").textContent = "";
  $("btn-start").disabled = false;
  $("btn-start").textContent = "Build my plan";
  window.scrollTo({ top: 0, behavior: "smooth" });
};

let lastCardCount = -1;

function pollingFailed() {
  clearInterval(poll);
  $("spinner").classList.add("hide");
  const st = $("run-status");
  st.textContent = "connection lost — refresh to resume";
  st.classList.add("err");
  $("p-progress").classList.remove("hide");
}

async function tick() {
  if (!runId) return;
  try {
    const r = await fetch(`/api/runs/${runId}`);
    if (!r.ok) throw new Error("HTTP " + r.status);
    pollFailures = 0;
    const d = await r.json();
    $("run-status").textContent = d.status.replace(/_/g, " ");
    $("log").textContent = (d.log || []).join("\n");
    $("log").scrollTop = 1e9;
    if (d.plan && $("plan-body").childElementCount === 0) renderPlan(d.plan);
    $("plan-status").textContent =
      d.status === "plan_ready" ? "(awaiting your approval)" : `(${d.status.replace(/_/g, " ")})`;
    if (!approved) $("btn-approve").disabled = d.status !== "plan_ready";
    if (d.status === "done" || d.status === "failed") {
      clearInterval(poll);
      $("spinner").classList.add("hide");
      const st = $("run-status");
      st.classList.toggle("err", d.status === "failed");
      st.classList.toggle("ok", d.status === "done");
      if (d.status === "failed") $("log").textContent += "\nERROR: " + d.error;
      if (d.status === "done") setStep(4);
      lastCardCount = -1;
      renderCards(d.cards || [], d.status);
      $("btn-start").disabled = false; // subtle "run it again" affordance
      $("btn-start").textContent = "Start a new search";
    } else if (["sourcing", "ranking", "diagnosing"].includes(d.status)) {
      $("p-progress").classList.remove("hide");
      renderCards(d.cards || [], d.status); // stream cards in as they finish
    }
  } catch (e) {
    pollFailures += 1;
    if (pollFailures >= CONFIG.MAX_POLL_FAILURES) pollingFailed();
  }
}

function renderPlan(p) {
  const b = $("plan-body");
  b.textContent = "";
  b.appendChild(el("div", "kv", "ICP: " + (p.icp || "—")));
  (p.tiers || []).forEach((t) => {
    const s = el("div", "sec");
    s.appendChild(el("b", "", "Tier " + (t.tier || "?") + " — " + (t.goal || "")));
    const ul = el("ul");
    (t.queries || []).forEach((q) => ul.appendChild(el("li", "", q)));
    s.appendChild(ul);
    b.appendChild(s);
  });
  if (p.ranking_criteria && p.ranking_criteria.length) {
    const s = el("div", "sec");
    s.appendChild(el("b", "", "Ranking criteria"));
    const ul = el("ul");
    p.ranking_criteria.forEach((c) => ul.appendChild(el("li", "", c)));
    s.appendChild(ul);
    b.appendChild(s);
  }
}

function renderCards(cards, status) {
  // don't rebuild (and wipe open <details>) unless something actually changed
  if (cards.length === lastCardCount) return;
  lastCardCount = cards.length;
  const box = $("cards");
  box.textContent = "";
  if (!cards.length) {
    if (status === "done") {
      box.appendChild(
        el("p", "empty", "Run finished but produced no cards — try a broader niche or more locations."),
      );
    }
    return;
  }
  const head = el("p", "cardT", `Ranked leads (${cards.length})`);
  box.appendChild(head);
  cards.forEach((c) => {
    const p = el("div", "panel lead");
    if (c.priority) p.classList.add("priority");

    // ── header: rank · title · fit meter · source ──
    const h = el("div", "lead-head");
    h.appendChild(el("span", "badge rank", "#" + c.rank));
    h.appendChild(el("span", "lead-title", c.title));
    if (c.priority) h.appendChild(el("span", "badge first", "★ CONTACT FIRST"));
    const score = c.fit_score || 0;
    const fit = el("span", "badge fit " + fitBand(score), "fit " + score.toFixed(0) + "/10");
    const meter = el("span", "meter");
    const bar = el("i");
    bar.style.width = Math.min(score * 10, 100) + "%";
    meter.appendChild(bar);
    fit.appendChild(meter);
    h.appendChild(fit);
    h.appendChild(el("span", "badge src", c.source + " · " + c.tier));
    p.appendChild(h);

    if (c.fit_reason) p.appendChild(el("div", "kv", "Why ranked here: " + c.fit_reason));
    if (c.url) {
      const a = el("a", "", c.url);
      a.href = c.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      p.appendChild(a);
    }

    // ── contact block: the action zone, always visible ──
    const cs = el("div", "contact");
    cs.appendChild(el("b", "", "Contact"));
    if (c.person || c.role) {
      cs.appendChild(el("div", "kv", "👤 " + [c.person, c.role].filter(Boolean).join(" — ")));
    }
    if (c.email) {
      const row = el("div", "contact-email");
      row.appendChild(el("span", "estat estat-" + (c.email_status || "unverified")));
      const a = el("a", "", c.email);
      a.href = "mailto:" + c.email;
      row.appendChild(a);
      row.appendChild(el("span", "kv", "(" + (c.email_status || "unverified") + ")"));
      row.appendChild(copyBtn("ghost mini", "Copy", () => c.email));
      cs.appendChild(row);
    } else {
      cs.appendChild(el("div", "kv", "No email found — try the website / socials below."));
    }
    if (c.phone) {
      const t = el("div", "kv");
      const a = el("a", "", c.phone);
      a.href = "tel:" + c.phone.replace(/[^\d+]/g, "");
      t.append("📞 ", a);
      cs.appendChild(t);
    }
    (c.socials || []).forEach((s) => {
      const a = el("a", "kv-a", s);
      a.href = s;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      cs.appendChild(a);
    });
    p.appendChild(cs);

    // ── outreach: the deliverable, visible with one-click copy ──
    const o = c.outreach || {};
    if (o.message) {
      const s = el("div", "sec");
      s.appendChild(el("b", "", "Outreach (" + [o.genre, o.channel].filter(Boolean).join(" · ") + ")"));
      if (o.why_this_genre) s.appendChild(el("div", "kv", o.why_this_genre));
      if (o.subject) s.appendChild(el("div", "subject", "Subject: " + o.subject));
      s.appendChild(el("div", "msg", o.message));
      s.appendChild(
        copyBtn("ghost", "Copy message", () => (o.subject ? o.subject + "\n\n" : "") + o.message),
      );
      p.appendChild(s);
    }

    // ── analysis: supporting detail, collapsed by default (progressive disclosure) ──
    const an = c.analysis || {};
    if (an.requirement || an.analyzer || (an.problems || []).length || (an.solutions || []).length) {
      const det = document.createElement("details");
      const sum = document.createElement("summary");
      sum.textContent =
        "Why this lead — analysis" + (an.confidence ? " (confidence: " + an.confidence + ")" : "");
      det.appendChild(sum);
      if (an.requirement) {
        const s = el("div", "sec");
        s.appendChild(el("b", "", "Requirement"));
        s.appendChild(el("div", "", an.requirement));
        det.appendChild(s);
      }
      if (an.analyzer) {
        const s = el("div", "sec");
        s.appendChild(el("b", "", "What they want"));
        s.appendChild(el("div", "", an.analyzer));
        det.appendChild(s);
      }
      if (an.problems && an.problems.length) {
        const s = el("div", "sec");
        s.appendChild(el("b", "", "Problems"));
        const ul = el("ul");
        an.problems.forEach((x) =>
          ul.appendChild(
            el("li", "", (x.problem || "") + (x.evidence ? " (evidence: " + x.evidence + ")" : "")),
          ),
        );
        s.appendChild(ul);
        det.appendChild(s);
      }
      if (an.solutions && an.solutions.length) {
        const s = el("div", "sec");
        s.appendChild(el("b", "", "Solutions & impact"));
        const ul = el("ul");
        an.solutions.forEach((x) =>
          ul.appendChild(
            el("li", "", (x.solution || "") + " → " + (x.impact || "") + " — " + (x.why_it_matters || "")),
          ),
        );
        s.appendChild(ul);
        det.appendChild(s);
      }
      if (an.disclaimer) det.appendChild(el("div", "kv", an.disclaimer));
      p.appendChild(det);
    }

    if (c.validator_notes && c.validator_notes.length) {
      const det = document.createElement("details");
      const sum = document.createElement("summary");
      sum.textContent = "Validator notes (" + c.validator_notes.length + ")";
      det.appendChild(sum);
      const ul = el("ul");
      c.validator_notes.forEach((n) => ul.appendChild(el("li", "", n)));
      det.appendChild(ul);
      p.appendChild(det);
    }
    box.appendChild(p);
  });
}
