# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import os, json, datetime, yaml
from pathlib import Path
LOG_PATH = Path('logs/actions.jsonl')
def load_yaml(path):
    with open(path, 'r') as f: return yaml.safe_load(f)
def ensure_dirs(*paths):
    for p in paths: Path(p).mkdir(parents=True, exist_ok=True)
def log_event(event, payload):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {'ts': datetime.datetime.utcnow().isoformat()+'Z', 'event': event, 'payload': payload}
    with open(LOG_PATH, 'a') as f: f.write(json.dumps(rec)+'\n')
def parse_date(s):
    if not s: return None
    for fmt in ('%Y-%m-%d','%Y-%m','%Y'):
        try: return datetime.datetime.strptime(s, fmt)
        except Exception: pass
    try: return datetime.datetime.fromisoformat(s)
    except Exception: return None
def within_12m(d):
    if not d: return False
    now = datetime.datetime.utcnow(); last12 = now - datetime.timedelta(days=365)
    return d >= last12
def compute_metrics_v2(papers):
    types = {'trial':0,'systematic_review':0}; types12 = {'trial':0,'systematic_review':0}
    intervs = {'iv_iron':0,'esa':0,'other_pbm':0}; intervs12 = {'iv_iron':0,'esa':0,'other_pbm':0}
    pops = {'icu':0,'post_icu':0,'other':0}; pops12 = {'icu':0,'post_icu':0,'other':0}
    for p in papers:
        d = parse_date(p.get('published')); rec12 = within_12m(d)
        t = (p.get('type') or 'other').lower()
        if t in types: types[t]+=1; types12[t]+= (1 if rec12 else 0)
        iv = p.get('intervention') or 'other_pbm'
        if iv in intervs: intervs[iv]+=1; intervs12[iv]+= (1 if rec12 else 0)
        pop = p.get('population') or 'other'
        if pop in pops: pops[pop]+=1; pops12[pop]+= (1 if rec12 else 0)
    return {
        'types':{ 'trial_total':types['trial'], 'trial_12m':types12['trial'],
                  'systematic_review_total':types['systematic_review'], 'systematic_review_12m':types12['systematic_review']},
        'interventions':{
          'iv_iron_total':intervs['iv_iron'], 'iv_iron_12m':intervs12['iv_iron'],
          'esa_total':intervs['esa'], 'esa_12m':intervs12['esa'],
          'other_pbm_total':intervs['other_pbm'], 'other_pbm_12m':intervs12['other_pbm']
        },
        'populations':{
          'icu_total':pops['icu'], 'icu_12m':pops12['icu'],
          'post_icu_total':pops['post_icu'], 'post_icu_12m':pops12['post_icu'],
          'other_total':pops['other'], 'other_12m':pops12['other']
        }
    }
