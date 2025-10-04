#!/usr/bin/env python3
# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import argparse, json, datetime, traceback
from pathlib import Path
try:
    from scripts.fetch_pubmed import fetch_pubmed
    from scripts.classify_and_summarize import classify_records, summarize_papers
    from scripts.utils import load_yaml, ensure_dirs, log_event, compute_metrics_v2
    from scripts.aggregate_summary import build_snapshot
    from scripts.build_index import update_reviews_index
except Exception:
    from fetch_pubmed import fetch_pubmed
    from classify_and_summarize import classify_records, summarize_papers
    from utils import load_yaml, ensure_dirs, log_event, compute_metrics_v2
    from aggregate_summary import build_snapshot
    from build_index import update_reviews_index

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--root', default='.')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=50)
    a = ap.parse_args()
    root = Path(a.root)
    spec = load_yaml(a.spec)
    slug = spec['slug']; title = spec['title']
    outdir = root / 'data' / slug
    ensure_dirs(outdir, root/'logs')
    try:
        papers_path = outdir / 'papers.json'
        if a.dry_run:
            seed = root / 'data' / 'sample_ic_anaemia' / 'papers.json'
            if seed.exists():
                json.dump(json.load(open(seed)), open(papers_path,'w'), indent=2)
            log_event('dry_run_used_sample', {'spec': slug})
        else:
            records = fetch_pubmed(spec, limit=a.limit)
            json.dump({'papers': records}, open(papers_path,'w'), indent=2)
            log_event('pubmed_fetched', {'spec': slug, 'count': len(records)})
        papers = json.load(open(papers_path))
        classify_records(papers, spec); json.dump(papers, open(papers_path,'w'), indent=2)
        summarize_papers(papers_path, spec); papers = json.load(open(papers_path))
        metrics = compute_metrics_v2([p for p in papers['papers'] if not p.get('exclude_reason')])
        snapshot = build_snapshot(papers['papers'])
        summary = {'title': title, 'updated_utc': datetime.datetime.utcnow().isoformat()+'Z', 'metrics': metrics, 'summary_html': snapshot}
        json.dump(summary, open(outdir/'summary.json','w'), indent=2)
        update_reviews_index(root)
        print("AI summaries step completed.")
        print(f'Completed review: {slug}')
    except Exception as e:
        log_event('error', {'spec': slug, 'error': str(e), 'trace': traceback.format_exc()})
        raise
if __name__ == '__main__':
    main()
