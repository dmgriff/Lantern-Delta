# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import os as _os, json, time, textwrap, urllib.request, urllib.error
try:
    from scripts.ai_filter import should_exclude
    from scripts.utils import log_event
except Exception:
    from ai_filter import should_exclude
    from utils import log_event

OPENAI_API_KEY = _os.getenv("OPENAI_API_KEY")

SUMMARY_PROMPT = """You are preparing a concise, audit-friendly evidence summary for a clinical trial or systematic review.

Return HTML only, using this structure:
<dl>
  <dt>PICO</dt><dd><b>P</b>: ...; <b>I</b>: ...; <b>C</b>: ...; <b>O</b>: ...</dd>
  <dt>Primary outcome</dt><dd>effect size with 95% CI and denominator; timing; analysis population</dd>
  <dt>Key secondary</dt><dd>very short bullets</dd>
  <dt>Safety</dt><dd>infections, thrombosis, hypersensitivity; numerators/denominators if present</dd>
  <dt>Risk of bias (Cochrane)</dt><dd>low / some concerns / high + one-line major concern</dd>
  <dt>Subgroups</dt><dd>reported subgroups & consistency</dd>
</dl>

Be terse, numeric where possible. If data are not reported, write “NR”.
"""

def _openai_chat(prompt, model="gpt-4o-mini", max_tokens=700):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing")
    req = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a careful evidence summariser for clinical research."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    data = json.dumps(req).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read().decode("utf-8"))
        return resp["choices"][0]["message"]["content"].strip()

def classify_records(papers_json, spec):
    cfg = spec.get('classify',{})
    iv_terms = cfg.get('interventions',{})
    type_terms = cfg.get('types',{})
    pop_terms = cfg.get('populations',{})
    safety = [s.lower() for s in cfg.get('safety_keywords',[])]
    for rec in papers_json['papers']:
        text = ' '.join([rec.get('title',''), rec.get('journal','')]).lower()
        reason = should_exclude(rec, spec)
        if reason:
            rec['exclude_reason'] = reason
            continue
        iv = None
        if any(t in text for t in iv_terms.get('iv_iron',[])): iv = 'iv_iron'
        if any(t in text for t in iv_terms.get('esa',[])): iv = ('esa' if not iv else 'other_pbm')
        if not iv and any(t in text for t in iv_terms.get('other_pbm',[])): iv = 'other_pbm'
        rec['intervention'] = iv or rec.get('intervention') or 'other_pbm'
        t = rec.get('type')
        for ty, terms in type_terms.items():
            if any(term in text for term in terms): t = ty
        rec['type'] = t or 'trial'
        pop = None
        for k, terms in pop_terms.items():
            if any(term in text for term in terms): pop = k
        rec['population'] = pop or rec.get('population') or 'other'
        if any(k in text for k in safety):
            rec.setdefault('flags',[]).append('safety')

def _make_paper_prompt(p):
    title = p.get('title','')
    j = p.get('journal','')
    date = p.get('published','')
    abs_html = p.get('abstract_html','') or ''
    pmid = p.get('pmid','')
    doi = p.get('doi','')
    body = f"""Title: {title}
Journal/Date: {j} / {date}
PMID: {pmid}   DOI: {doi}

Abstract:
{abs_html}
"""
    return f"{SUMMARY_PROMPT}\n\n{body}"

def summarize_papers(papers_path, spec):
    data = json.load(open(papers_path))
    use_ai = bool(spec.get('openai',{}).get('enable', False))
    total = len(data['papers']); done = 0
    for p in data['papers']:
        if p.get('exclude_reason'): continue
        if p.get('summary_html') and 'NR' not in p['summary_html'] and 'Pending' not in p['summary_html']:
            done += 1; continue
        if not use_ai:
            if not p.get('summary_html'):
                p['summary_html'] = '<dl><dt>PICO</dt><dd>NR</dd><dt>Primary outcome</dt><dd>NR</dd><dt>Key secondary</dt><dd>NR</dd><dt>Safety</dt><dd>NR</dd><dt>Risk of bias</dt><dd>NR</dd><dt>Subgroups</dt><dd>NR</dd></dl>'
            continue
        try:
            prompt = _make_paper_prompt(p)
            html = _openai_chat(prompt)
            if html:
                p['summary_html'] = html
                log_event('ai_summary_generated', {'pmid': p.get('pmid'), 'title': p.get('title')[:80]})
                done += 1
            time.sleep(0.6)
        except Exception as e:
            log_event('ai_summary_error', {'pmid': p.get('pmid'), 'error': str(e)})
            if not p.get('summary_html'):
                p['summary_html'] = '<dl><dt>PICO</dt><dd>NR</dd><dt>Primary outcome</dt><dd>NR</dd><dt>Key secondary</dt><dd>NR</dd><dt>Safety</dt><dd>NR</dd><dt>Risk of bias</dt><dd>NR</dd><dt>Subgroups</dt><dd>NR</dd></dl>'
    json.dump(data, open(papers_path,'w'), indent=2)
    print(f"Summarised {done}/{total} eligible papers via OpenAI.")
