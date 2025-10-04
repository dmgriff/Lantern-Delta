# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import json
from pathlib import Path
def update_reviews_index(root):
    data_dir = Path(root) / 'data'
    reviews = []
    for d in data_dir.iterdir():
        if d.is_dir():
            s = d/'summary.json'
            if s.exists():
                js = json.load(open(s))
                reviews.append({'slug': d.name, 'title': js.get('title', d.name)})
    json.dump({'reviews': sorted(reviews, key=lambda x: x['slug'])}, open(data_dir/'reviews_index.json','w'), indent=2)
