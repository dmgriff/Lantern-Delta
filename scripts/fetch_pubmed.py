# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import json, urllib.parse, urllib.request, datetime, re
BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
def _get(url):
    with urllib.request.urlopen(url, timeout=30) as r: return r.read().decode('utf-8')
def _fetch_abstracts(pmids):
    if not pmids: return {}
    url = BASE + 'efetch.fcgi?' + urllib.parse.urlencode({'db':'pubmed','id':','.join(pmids),'retmode':'xml'})
    xml = _get(url)
    chunks = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml, flags=re.DOTALL)
    joined = ' '.join(chunks).strip()
    return {pid: joined for pid in pmids}
def fetch_pubmed(spec, limit=50):
    q = spec['sources'][0]['search']['query']
    years = spec.get('time_horizon_years', 20)
    mindate = (datetime.datetime.utcnow() - datetime.timedelta(days=365*years)).date().isoformat()
    params = {'db':'pubmed','term': q,'retmode':'json','retmax': str(limit),'mindate': mindate,'sort':'date'}
    url = BASE + 'esearch.fcgi?' + urllib.parse.urlencode(params)
    data = json.loads(_get(url))
    ids = data.get('esearchresult',{}).get('idlist',[])
    if not ids: return []
    url = BASE + 'esummary.fcgi?' + urllib.parse.urlencode({'db':'pubmed','id':','.join(ids),'retmode':'json'})
    esum = json.loads(_get(url)); result = []
    for pid, rec in esum.get('result',{}).items():
        if pid == 'uids': continue
        title = rec.get('title'); journal = rec.get('fulljournalname')
        pubdate = rec.get('pubdate','').split(' ')[0].replace('/', '-')
        authors = [a.get('name') for a in rec.get('authors',[]) if a.get('name')]
        elocid = rec.get('elocationid','') or ''
        m = re.search(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', elocid); doi = m.group(0) if m else None
        result.append({'title':title,'authors':authors,'journal':journal,'published':pubdate or None,'pmid':pid,'doi':doi})
    try:
        abs_map = _fetch_abstracts([r['pmid'] for r in result])
        for r in result:
            if abs_map.get(r['pmid']): r['abstract_html'] = abs_map[r['pmid']]
    except Exception:
        pass
    return result
