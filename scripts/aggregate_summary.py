# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

def build_snapshot(papers):
    n_trials = sum(1 for p in papers if (p.get('type')=='trial' and not p.get('exclude_reason')))
    n_sr = sum(1 for p in papers if (p.get('type')=='systematic_review' and not p.get('exclude_reason')))
    return f"<p><b>Overview:</b> {n_trials} trial(s) and {n_sr} systematic review(s) currently inform the question. Efficacy suggests possible transfusion reduction with IV iron; no consistent safety harms identified to date. Subgroup evidence remains limited.</p>"
