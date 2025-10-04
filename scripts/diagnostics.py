#!/usr/bin/env python3
# ---- import shim for both 'python scripts/x.py' and module import ----
import sys, os as _os
_pkg_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), ".."))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

import os, sys, json, importlib.util, traceback, subprocess
from pathlib import Path
ROOT = Path('.')
def check_python():
    major, minor = sys.version_info[:2]
    return (major==3 and minor>=11), f'Python {major}.{minor} (need 3.11+)'
def check_compile_py():
    ok=True; msgs=[]
    for p in ROOT.rglob('scripts/*.py'):
        try:
            spec = importlib.util.spec_from_file_location('mod', p)
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)  # noqa
        except Exception as e:
            ok=False; msgs.append(f'Syntax/import error in {p}: {e}')
    return ok, msgs or ['All scripts import successfully.']
def check_yaml():
    import yaml
    ok=True; msgs=[]
    for y in (ROOT/'reviews').glob('*.yaml'):
        try:
            cfg = yaml.safe_load(open(y))
            for k in ['slug','title','sources']: assert cfg.get(k), f'Missing key {k} in {y.name}'
        except Exception as e:
            ok=False; msgs.append(f'YAML problem {y}: {e}')
    return ok, msgs or ['Review YAML valid.']
def check_env():
    import yaml
    enable_ai=False
    for y in (ROOT/'reviews').glob('*.yaml'):
        cfg=yaml.safe_load(open(y))
        if cfg.get('openai',{}).get('enable'):
            enable_ai=True
    key = os.getenv('OPENAI_API_KEY')
    present = bool(key and key.strip())
    if enable_ai and not present:
        return False, ['openai.enable true but OPENAI_API_KEY not set']
    return True, ['AI disabled or key present.']
def check_workflow():
    wf = ROOT/'.github/workflows/living_review.yml'
    if not wf.exists(): return False, ['Workflow missing at .github/workflows/living_review.yml']
    txt = open(wf).read()
    ok = ('workflow_dispatch' in txt) and ('deploy-pages' in txt or 'deploy-pages@v4' in txt)
    return ok, ['Workflow contains dispatch and deploy steps.']
def quick_dry_run():
    try:
        r = subprocess.run([sys.executable, 'scripts/run_review.py', '--spec', 'reviews/iron_esa.yaml', '--root', '.', '--dry-run', '--limit', '5'],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
        ok = (r.returncode==0); return ok, [r.stdout[-800:]]
    except Exception as e:
        return False, [str(e)]
def main():
    checks=[('Python version', check_python), ('Compile scripts', check_compile_py), ('YAML schema', check_yaml), ('OpenAI env', check_env), ('Workflow presence', check_workflow), ('Dry-run pipeline', quick_dry_run)]
    results=[]; overall=True
    for name, fn in checks:
        try: ok, msg = fn()
        except Exception as e: ok=False; msg=[f'unexpected exception: {e}\n{traceback.format_exc()}']
        results.append({'check': name, 'ok': ok, 'messages': msg}); overall = overall and ok
    print(json.dumps({'ok': overall, 'results': results}, indent=2)); return 0 if overall else 1
if __name__ == '__main__':
    raise SystemExit(main())
