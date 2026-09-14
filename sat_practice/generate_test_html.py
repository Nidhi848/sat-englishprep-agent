#!/usr/bin/env python3
"""
Turn a /sat_practice/tests/*_test.json file into a standalone HTML page
Nirvaan can open directly (no email, no server, no internet needed).

Usage:
    python3 sat_practice/generate_test_html.py sat_practice/tests/2026-09-14_test.json

Writes a sibling file, e.g. sat_practice/tests/2026-09-14_test.html.
This is the fallback path for when the Gmail connector isn't sending:
the routine still writes the JSON test file as usual (Step 5), then this
script turns it into something Nirvaan can open after a `git pull`
(or from a fresh `git clone`) with zero setup. It never embeds the
correct answers or explanations in the page — only the questions and
choices, same as the real email would show him.
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
        <label class="choice">
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
      </div>
      {passages_html}
      <p class="qtext">{escape(q["question"])}</p>
      <div class="choices">{choices_html}</div>
    </div>'''


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
  }}
  @media (prefers-color-scheme: dark){{
    :root{{
      --paper:#171A17; --surface:#20241F; --surface-2:#262B24;
      --ink:#EAEDE8; --muted:#9AA69E; --hairline:#343A32;
      --info:#6FBE94; --info-bg:#1E332A;
      --craft:#B79BE0; --craft-bg:#2E2739;
      --accent:#6FBE94;
    }}
  }}
  *{{box-sizing:border-box;}}
  body{{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:system-ui,-apple-system,Segoe UI,sans-serif;
    padding:28px 16px 90px;
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

  .qcard{{
    background:var(--surface); border:1px solid var(--hairline); border-left:3px solid var(--hairline);
    border-radius:10px; padding:18px 20px 20px; margin-bottom:14px;
  }}
  .qcard.answered{{border-left-color:var(--accent);}}
  .qmeta{{display:flex; align-items:center; gap:8px; margin-bottom:12px; flex-wrap:wrap;}}
  .qnum{{font-family:"Courier New",monospace; font-weight:700; font-size:13px; color:var(--muted); width:24px; flex:none;}}
  .tag{{font-size:10.5px; letter-spacing:.03em; text-transform:uppercase; padding:3px 8px; border-radius:5px;}}
  .tag.domain-info{{background:var(--info-bg); color:var(--info);}}
  .tag.domain-craft{{background:var(--craft-bg); color:var(--craft);}}
  .tag.topic{{background:var(--surface-2); color:var(--muted); border:1px solid var(--hairline);}}

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

  .submitbar{{
    position:fixed; bottom:0; left:0; right:0; background:var(--surface);
    border-top:1px solid var(--hairline); padding:14px 16px;
    display:flex; gap:10px; justify-content:center; flex-wrap:wrap;
  }}
  .submitbar button{{
    font-size:13.5px; border-radius:999px; padding:10px 18px; cursor:pointer;
    border:1px solid var(--accent); background:var(--accent); color:var(--surface);
  }}
  .submitbar .hint{{font-size:12px; color:var(--muted); align-self:center;}}

  #answerOut{{
    max-width:700px; margin:14px auto 0; display:none;
  }}
  #answerOut.show{{display:block;}}
  #answerOut textarea{{
    width:100%; min-height:90px; font-family:"Courier New",monospace; font-size:13px;
    padding:10px; border-radius:8px; border:1px solid var(--hairline); background:var(--surface-2); color:var(--ink);
  }}
  #answerOut .label{{font-size:12px; color:var(--muted); margin-bottom:6px;}}

  @media (max-width:480px){{
    .qcard{{padding:15px 14px 16px;}}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>SAT Practice — {date} — Tier {info_tier}/{craft_tier}</h1>
  <p class="sub">{count} questions &middot; ~{minutes} min at practice pace &middot; Info &amp; Ideas Tier {info_tier} / Craft &amp; Structure Tier {craft_tier}</p>

  <div class="fallback-note">Opened locally because email isn't set up yet. Answer everything below, then tap <b>Copy my answers</b> and send that numbered list to your parent (text, email — whatever works) so it can be graded.</div>

  <div class="progress">
    <span id="progressLabel">0 of {count} answered</span>
    <span class="bar"><span class="fill" id="progressFill"></span></span>
  </div>

  <div id="questions">{questions_html}</div>
</div>

<div class="submitbar">
  <button id="copyBtn" type="button">Copy my answers</button>
  <span class="hint">Answers save in this browser as you go.</span>
</div>
<div id="answerOut" class="wrap">
  <div class="label">Your answers (paste this into a text/email to your parent):</div>
  <textarea id="answerText" readonly></textarea>
</div>

<script>
const STORAGE_KEY = "sat_practice_answers_{date}";
const total = {count};

function loadSaved() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}"); }}
  catch (e) {{ return {{}}; }}
}}
function save(answers) {{
  try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(answers)); }} catch (e) {{}}
}}

function updateProgress() {{
  const answered = document.querySelectorAll('#questions input[type="radio"]:checked').length;
  document.getElementById("progressLabel").textContent = answered + " of " + total + " answered";
  document.getElementById("progressFill").style.width = (answered / total * 100) + "%";
}}

(function init() {{
  const saved = loadSaved();
  document.querySelectorAll('.qcard').forEach(card => {{
    const qid = card.dataset.qid;
    const val = saved[qid];
    if (val) {{
      const input = card.querySelector('input[value="' + val + '"]');
      if (input) input.checked = true;
      card.classList.add("answered");
    }}
  }});
  updateProgress();

  document.getElementById("questions").addEventListener("change", (e) => {{
    if (e.target.type !== "radio") return;
    const card = e.target.closest(".qcard");
    card.classList.add("answered");
    const answers = loadSaved();
    answers[card.dataset.qid] = e.target.value;
    save(answers);
    updateProgress();
  }});

  document.getElementById("copyBtn").addEventListener("click", () => {{
    const answers = loadSaved();
    const cards = Array.from(document.querySelectorAll(".qcard"))
      .sort((a, b) => Number(a.dataset.qid) - Number(b.dataset.qid));
    const lines = cards.map(c => c.dataset.qid + ". " + (answers[c.dataset.qid] || "—"));
    const text = lines.join("\\n");
    const box = document.getElementById("answerText");
    box.value = text;
    document.getElementById("answerOut").classList.add("show");
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

    html = PAGE_TEMPLATE.format(
        date=data.get("date", "sample"),
        info_tier=data["difficulty_tier"]["information_and_ideas"],
        craft_tier=data["difficulty_tier"]["craft_and_structure"],
        count=count,
        minutes=minutes,
        questions_html=questions_html,
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
