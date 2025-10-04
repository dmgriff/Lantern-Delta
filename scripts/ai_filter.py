# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import re
def should_exclude(rec, spec):
    title = (rec.get('title') or '').lower()
    journal = (rec.get('journal') or '').lower()
    abstract = (rec.get('abstract_html') or '').lower()
    text = ' '.join([title, journal, abstract])
    cfg = spec.get('ai_filter',{}).get('exclude',{})
    designs = [d.lower() for d in cfg.get('designs',[])]
    populations = [p.lower() for p in cfg.get('populations',[])]
    min_n = int(cfg.get('min_sample_size', 0) or 0)
    if any(d in text for d in designs): return 'design_excluded'
    if any(p in text for p in populations): return 'population_excluded'
    m = re.search(r'\bn\s*=\s*(\d+)', text)
    if m and int(m.group(1)) < min_n: return 'small_sample'
    return None
