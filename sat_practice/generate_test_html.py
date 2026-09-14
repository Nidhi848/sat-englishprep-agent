#!/usr/bin/env python3
"""
Turn a /sat_practice/tests/*_test.json file into a standalone HTML page
Nirvaan can open directly (no email, no server, no internet needed) and
grade himself the moment he submits.

Usage:
    python3 sat_practice/generate_test_html.py sat_practice/tests/2026-09-14_test.json

Writes a sibling file, e.g. sat_practice/tests/2026-09-14_test.html.
This is the fallback path for when the Gmail connector isn't sending:
the routine still writes the JSON test file as usual (Step 5), then this
script turns it into something Nirvaan can open after a `git pull`
(or from a fresh `git clone`) with zero setup. The correct answers and
explanations ARE embedded in the page's data (needed for instant
self-grading after submit), but stay out of the DOM/UI until he clicks
"Submit Test" — same reveal-after-answering flow as the reveal toggle
in the parent's format-review artifact, just self-serve for the student.

This does NOT write back to score_log.json — that still only happens via
the routine's own grading step (reading a Gmail reply). Use the "Copy
results for your records" button after submitting to get a summary you
can paste into score_log.json by hand while the connector is down.
"""

import json
import sys
from html import escape
from pathlib import Path

DOMAIN_LABEL = {
    "information_and_ideas": "Info & Ideas",
    "craft_and_structure": "Craft & Structure",
}
DOMAIN_CLASS = {
    "information_and_ideas": "domain-info",
    "craft_and_structure": "domain-craft",
}
SUBTYPE_LABEL = {
    "words_in_context": "Words in Context",
    "text_structure_and_purpose": "Text Structure & Purpose",
    "cross_text_connections": "Cross-Text Connections",
    "central_ideas_and_details": "Central Ideas & Details",
    "inferences": "Inferences",
    "command_of_evidence": "Command of Evidence",
}
TOPIC_LABEL = {
    "natural_science": "Natural science",
    "literature": "Literature",
    "social_science": "Social science",
    "historical": "Historical / founding docs",
}


def render_question(q):
    domain = DOMAIN_LABEL.get(q["domain"], q["domain"])
    domain_cls = DOMAIN_CLASS.get(q["domain"], "domain-info")
    subtype = SUBTYPE_LABEL.get(q["subtype"], q["subtype"])
    topic = TOPIC_LABEL.get(q["topic_category"], q["topic_category"])

    if "passage" in q:
        passages_html = f'<div class="passage">{escape(q["passage"])}</div>'
    else:
        passages_html = "".join(
            f'<div class="passage"><span class="plabel">Text {i}</span>{escape(q[key])}</div>'
            for i, key in enumerate(("passage_1", "passage_2"), start=1)
        )

    choices_html = "".join(
        f'''
        <label class="choice" data-letter="{letter}">
          <input type="radio" name="q{q["id"]}" value="{letter}">
          <span class="letter">{letter}</span>
          <span>{escape(q["choices"][letter])}</span>
        </label>'''
        for letter in ("A", "B", "C", "D")
    )

    return f'''
    <div class="qcard" data-qid="{q["id"]}">
      <div class="qmeta">
        <span class="qnum">{q["id"]:02d}</span>
        <span class="tag {domain_cls}">{escape(domain)}</span>
        <span class="tag topic">{escape(subtype)}</span>
        <span class="tag topic">{escape(topic)}</span>
        <span class="result-badge"></span>
      </div>
      {passages_html}
      <p class="qtext">{escape(q["question"])}</p>
      <div class="choices">{choices_html}</div>
      <div class="explain"></div>
    </div>'''


def build_meta(questions):
    meta = {}
    for q in questions:
        meta[str(q["id"])] = {
            "domain": q["domain"],
            "correct": q["correct_answer"],
            "explanation": q["explanation"],
        }
    return meta


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAT Practice — {date} — Tier {info_tier}/{craft_tier}</title>
<style>
  :root{{
    --paper:#EDEFEC; --surface:#FFFFFF; --surface-2:#F6F7F4;
    --ink:#1C2321; --muted:#5B6660; --hairline:#D8DBD5;
    --info:#2F6F4F; --info-bg:#E7F1EA;
    --craft:#6B4A9E; --craft-bg:#EFE9F6;
    --accent:#2F6F4F;
    --good:#2F6F4F; --good-bg:#E7F1EA;
    --bad:#B23A2E; --bad-bg:#FBEAE7;
  }}
  @media (prefers-color-scheme: dark){{
    :root{{
      --paper:#171A17; --surface:#20241F; --surface-2:#262B24;
      --ink:#EAEDE8; --muted:#9AA69E; --hairline:#343A32;
      --info:#6FBE94; --info-bg:#1E332A;
      --craft:#B79BE0; --craft-bg:#2E2739;
      --accent:#6FBE94;
      --good:#6FBE94; --good-bg:#1E332A;
      --bad:#E8897C; --bad-bg:#3A2422;
    }}
  }}
  *{{box-sizing:border-box;}}
  body{{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:system-ui,-apple-system,Segoe UI,sans-serif;
    padding:28px 16px 100px;
  }}
  .wrap{{max-width:700px;margin:0 auto;}}
  h1{{font-family:Georgia,"Times New Roman",serif; font-size:21px; font-weight:700; margin:0 0 4px; text-wrap:balance;}}
  .sub{{font-size:13px; color:var(--muted); margin:0 0 18px;}}

  .fallback-note{{
    font-size:12.5px; color:var(--muted); background:var(--surface-2);
    border:1px solid var(--hairline); border-radius:8px;
    padding:10px 14px; margin-bottom:20px; line-height:1.5;
  }}

  .progress{{
    position:sticky; top:0; z-index:5; background:var(--paper);
    padding:10px 0 14px; margin-bottom:6px;
    font-size:12.5px; color:var(--muted); display:flex; align-items:center; gap:10px;
  }}
  .progress .bar{{flex:1; height:6px; background:var(--surface-2); border-radius:99px; overflow:hidden; border:1px solid var(--hairline);}}
  .progress .fill{{height:100%; background:var(--accent); width:0%; transition:width .2s ease;}}

  .results{{
    background:var(--surface); border:1px solid var(--hairline); border-radius:12px;
    padding:20px 22px; margin-bottom:20px;
  }}
  .results[hidden]{{display:none;}}
  .results .headline{{font-family:Georgia,"Times New Roman",serif; font-size:19px; font-weight:700; margin:0 0 12px;}}
  .results .breakdown{{display:flex; gap:10px; flex-wrap:wrap;}}
  .scorechip{{
    flex:1; min-width:150px; border-radius:9px; padding:10px 14px;
  }}
  .scorechip .lbl{{font-size:11px; letter-spacing:.03em; text-transform:uppercase; opacity:.8;}}
  .scorechip .val{{font-size:20px; font-weight:700; font-variant-numeric:tabular-nums;}}
  .scorechip.info{{background:var(--info-bg); color:var(--info);}}
  .scorechip.craft{{background:var(--craft-bg); color:var(--craft);}}
  .scorechip.overall{{background:var(--surface-2); color:var(--ink); border:1px solid var(--hairline);}}
  .results .msg{{font-size:13.5px; color:var(--muted); margin-top:12px; line-height:1.5;}}

  .qcard{{
    background:var(--surface); border:1px solid var(--hairline); border-left:3px solid var(--hairline);
    border-radius:10px; padding:18px 20px 20px; margin-bottom:14px;
  }}
  .qcard.answered{{border-left-color:var(--accent);}}
  .qcard.graded-correct{{border-left-color:var(--good);}}
  .qcard.graded-incorrect{{border-left-color:var(--bad);}}
  .qmeta{{display:flex; align-items:center; gap:8px; margin-bottom:12px; flex-wrap:wrap;}}
  .qnum{{font-family:"Courier New",monospace; font-weight:700; font-size:13px; color:var(--muted); width:24px; flex:none;}}
  .tag{{font-size:10.5px; letter-spacing:.03em; text-transform:uppercase; padding:3px 8px; border-radius:5px;}}
  .tag.domain-info{{background:var(--info-bg); color:var(--info);}}
  .tag.domain-craft{{background:var(--craft-bg); color:var(--craft);}}
  .tag.topic{{background:var(--surface-2); color:var(--muted); border:1px solid var(--hairline);}}
  .result-badge{{margin-left:auto; font-size:11px; font-weight:700; letter-spacing:.02em;}}
  .result-badge.correct{{color:var(--good);}}
  .result-badge.incorrect{{color:var(--bad);}}

  .passage{{
    font-family:Georgia,"Times New Roman",serif; font-size:15.5px; line-height:1.6;
    background:var(--surface-2); border-left:3px solid var(--hairline);
    padding:12px 15px; border-radius:0 6px 6px 0; margin-bottom:12px;
  }}
  .plabel{{display:block; font-size:10.5px; letter-spacing:.05em; text-transform:uppercase; color:var(--muted); margin-bottom:5px;}}
  .qtext{{font-size:14.5px; font-weight:600; margin:0 0 12px; line-height:1.5;}}

  .choices{{display:grid; gap:8px;}}
  .choice{{
    display:flex; gap:10px; align-items:flex-start; cursor:pointer;
    padding:9px 12px; border-radius:7px; border:1px solid var(--hairline); font-size:14px; line-height:1.45;
  }}
  .choice:hover{{background:var(--surface-2);}}
  .choice input{{margin:3px 0 0; accent-color:var(--accent); flex:none;}}
  .choice .letter{{font-family:"Courier New",monospace; font-weight:700; color:var(--muted); flex:none;}}
  .choice.correct-answer{{border-color:var(--good); background:var(--good-bg);}}
  .choice.wrong-pick{{border-color:var(--bad); background:var(--bad-bg);}}

  .explain{{
    display:none; margin-top:12px; padding-top:12px; border-top:1px dashed var(--hairline);
    font-size:13.5px; color:var(--ink); line-height:1.55;
  }}
  .explain b{{font-family:"Courier New",monospace; font-size:10.5px; letter-spacing:.05em; text-transform:uppercase; display:block; margin-bottom:4px; color:var(--muted);}}
  .qcard.graded .explain{{display:block;}}

  .submitbar{{
    position:fixed; bottom:0; left:0; right:0; background:var(--surface);
    border-top:1px solid var(--hairline); padding:14px 16px;
    display:flex; gap:10px; justify-content:center; flex-wrap:wrap;
  }}
  .submitbar button{{
    font-size:13.5px; border-radius:999px; padding:10px 18px; cursor:pointer;
    border:1px solid var(--accent); background:var(--accent); color:var(--surface);
  }}
  .submitbar button.secondary{{background:var(--surface); color:var(--accent);}}
  .submitbar button:disabled{{opacity:.45; cursor:not-allowed;}}
  .submitbar .hint{{font-size:12px; color:var(--muted); align-self:center;}}

  #copyOut{{max-width:700px; margin:14px auto 0; display:none;}}
  #copyOut.show{{display:block;}}
  #copyOut textarea{{
    width:100%; min-height:100px; font-family:"Courier New",monospace; font-size:12.5px;
    padding:10px; border-radius:8px; border:1px solid var(--hairline); background:var(--surface-2); color:var(--ink);
  }}
  #copyOut .label{{font-size:12px; color:var(--muted); margin-bottom:6px;}}

  @media (max-width:480px){{
    .qcard{{padding:15px 14px 16px;}}
    .results{{padding:16px 16px;}}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>SAT Practice — {date} — Tier {info_tier}/{craft_tier}</h1>
  <p class="sub">{count} questions &middot; ~{minutes} min at practice pace &middot; Info &amp; Ideas Tier {info_tier} / Craft &amp; Structure Tier {craft_tier}</p>

  <div class="fallback-note">Opened locally because email isn't set up yet. Answer everything below, then tap <b>Submit Test</b> to see your score and explanations right away — no need to wait on anyone.</div>

  <div id="resultsPanel" class="results" hidden>
    <div class="headline" id="resultsHeadline"></div>
    <div class="breakdown">
      <div class="scorechip info">
        <div class="lbl">Info &amp; Ideas</div>
        <div class="val" id="scoreInfo">—</div>
      </div>
      <div class="scorechip craft">
        <div class="lbl">Craft &amp; Structure</div>
        <div class="val" id="scoreCraft">—</div>
      </div>
      <div class="scorechip overall">
        <div class="lbl">Overall</div>
        <div class="val" id="scoreOverall">—</div>
      </div>
    </div>
    <div class="msg" id="resultsMsg"></div>
  </div>

  <div class="progress" id="progressBar">
    <span id="progressLabel">0 of {count} answered</span>
    <span class="bar"><span class="fill" id="progressFill"></span></span>
  </div>

  <div id="questions">{questions_html}</div>
</div>

<div class="submitbar">
  <button id="submitBtn" type="button">Submit Test</button>
  <button id="copyBtn" type="button" class="secondary" disabled>Copy results for your records</button>
  <span class="hint" id="submitHint">Answers save in this browser as you go.</span>
</div>
<div id="copyOut" class="wrap">
  <div class="label">Results summary (paste into score_log.json, or text/email it to whoever's tracking):</div>
  <textarea id="copyText" readonly></textarea>
</div>

<script>
const STORAGE_KEY = "sat_practice_{date}";
const total = {count};
const QMETA = {qmeta_json};

function loadState() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}"); }}
  catch (e) {{ return {{}}; }}
}}
function saveState(state) {{
  try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }} catch (e) {{}}
}}

function updateProgress() {{
  const answered = document.querySelectorAll('#questions input[type="radio"]:checked').length;
  document.getElementById("progressLabel").textContent = answered + " of " + total + " answered";
  document.getElementById("progressFill").style.width = (answered / total * 100) + "%";
}}

function gradeCard(card, answers) {{
  const qid = card.dataset.qid;
  const meta = QMETA[qid];
  const picked = answers[qid];
  const isCorrect = picked === meta.correct;

  card.classList.add("graded", isCorrect ? "graded-correct" : "graded-incorrect");
  card.querySelectorAll('input[type="radio"]').forEach(input => input.disabled = true);

  const badge = card.querySelector(".result-badge");
  badge.textContent = isCorrect ? "✓ Correct" : "✗ Incorrect";
  badge.classList.add(isCorrect ? "correct" : "incorrect");

  card.querySelectorAll(".choice").forEach(label => {{
    const letter = label.dataset.letter;
    if (letter === meta.correct) label.classList.add("correct-answer");
    else if (letter === picked) label.classList.add("wrong-pick");
  }});

  const explain = card.querySelector(".explain");
  explain.innerHTML = "<b>Why " + meta.correct + " is correct</b>" + meta.explanation;

  return isCorrect;
}}

function scoreLabel(pct) {{
  if (pct >= 85) return "Great work — that's tier-up territory.";
  if (pct <= 60) return "Rough one — this domain may need a tier down or a strategy chat.";
  return "Solid — right in the zone for this tier.";
}}

function gradeAll() {{
  const state = loadState();
  const answers = state.answers || {{}};
  const cards = Array.from(document.querySelectorAll(".qcard"));

  const totals = {{ information_and_ideas: {{c:0,n:0}}, craft_and_structure: {{c:0,n:0}} }};
  cards.forEach(card => {{
    const qid = card.dataset.qid;
    const meta = QMETA[qid];
    const correct = gradeCard(card, answers);
    totals[meta.domain].n++;
    if (correct) totals[meta.domain].c++;
  }});

  const infoP = Math.round(100 * totals.information_and_ideas.c / totals.information_and_ideas.n);
  const craftP = Math.round(100 * totals.craft_and_structure.c / totals.craft_and_structure.n);
  const overallN = totals.information_and_ideas.n + totals.craft_and_structure.n;
  const overallC = totals.information_and_ideas.c + totals.craft_and_structure.c;
  const overallP = Math.round(100 * overallC / overallN);

  document.getElementById("scoreInfo").textContent = totals.information_and_ideas.c + "/" + totals.information_and_ideas.n + " (" + infoP + "%)";
  document.getElementById("scoreCraft").textContent = totals.craft_and_structure.c + "/" + totals.craft_and_structure.n + " (" + craftP + "%)";
  document.getElementById("scoreOverall").textContent = overallC + "/" + overallN + " (" + overallP + "%)";
  document.getElementById("resultsHeadline").textContent = "Test graded — " + overallP + "% overall";
  document.getElementById("resultsMsg").textContent =
    "Info & Ideas: " + scoreLabel(infoP) + " Craft & Structure: " + scoreLabel(craftP);
  document.getElementById("resultsPanel").hidden = false;
  document.getElementById("resultsPanel").scrollIntoView({{ behavior: "smooth", block: "start" }});

  document.getElementById("submitBtn").disabled = true;
  document.getElementById("submitBtn").textContent = "Submitted";
  document.getElementById("copyBtn").disabled = false;
  document.getElementById("submitHint").textContent = "Graded locally — nothing sent anywhere automatically.";

  state.submitted = true;
  state.scores = {{ information_and_ideas: {{ c: totals.information_and_ideas.c, n: totals.information_and_ideas.n }},
                    craft_and_structure: {{ c: totals.craft_and_structure.c, n: totals.craft_and_structure.n }} }};
  saveState(state);
}}

(function init() {{
  const state = loadState();
  const answers = state.answers || {{}};

  document.querySelectorAll('.qcard').forEach(card => {{
    const qid = card.dataset.qid;
    const val = answers[qid];
    if (val) {{
      const input = card.querySelector('input[value="' + val + '"]');
      if (input) input.checked = true;
      card.classList.add("answered");
    }}
  }});
  updateProgress();

  if (state.submitted) {{
    gradeAll();
  }}

  document.getElementById("questions").addEventListener("change", (e) => {{
    if (e.target.type !== "radio") return;
    const card = e.target.closest(".qcard");
    card.classList.add("answered");
    const s = loadState();
    s.answers = s.answers || {{}};
    s.answers[card.dataset.qid] = e.target.value;
    saveState(s);
    updateProgress();
  }});

  document.getElementById("submitBtn").addEventListener("click", () => {{
    const answered = document.querySelectorAll('#questions input[type="radio"]:checked').length;
    if (answered < total && !confirm(answered + " of " + total + " answered. Submit anyway?")) return;
    gradeAll();
  }});

  document.getElementById("copyBtn").addEventListener("click", () => {{
    const s = loadState();
    if (!s.scores) return;
    const i = s.scores.information_and_ideas, c = s.scores.craft_and_structure;
    const cards = Array.from(document.querySelectorAll(".qcard"))
      .sort((a, b) => Number(a.dataset.qid) - Number(b.dataset.qid));
    const answerLines = cards.map(card => card.dataset.qid + ". " + (s.answers[card.dataset.qid] || "—"));
    const text = "SAT Practice — {date} — Tier {info_tier}/{craft_tier}\\n" +
      "Info & Ideas: " + i.c + "/" + i.n + " (" + Math.round(100*i.c/i.n) + "%)\\n" +
      "Craft & Structure: " + c.c + "/" + c.n + " (" + Math.round(100*c.c/c.n) + "%)\\n\\n" +
      "Answers:\\n" + answerLines.join("\\n");
    const box = document.getElementById("copyText");
    box.value = text;
    document.getElementById("copyOut").classList.add("show");
    box.focus();
    box.select();
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).catch(() => {{}});
    }}
  }});
}})();
</script>
</body>
</html>
"""


def generate(json_path: Path) -> Path:
    data = json.loads(json_path.read_text())
    questions_html = "".join(render_question(q) for q in data["questions"])
    count = len(data["questions"])
    minutes = round(count * 90 / 60)
    qmeta_json = json.dumps(build_meta(data["questions"]), ensure_ascii=False)

    html = PAGE_TEMPLATE.format(
        date=data.get("date", "sample"),
        info_tier=data["difficulty_tier"]["information_and_ideas"],
        craft_tier=data["difficulty_tier"]["craft_and_structure"],
        count=count,
        minutes=minutes,
        questions_html=questions_html,
        qmeta_json=qmeta_json,
    )

    out_path = json_path.with_suffix(".html")
    out_path.write_text(html)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 generate_test_html.py <path/to/test.json>")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)

    out = generate(src)
    print(f"Wrote {out}")
