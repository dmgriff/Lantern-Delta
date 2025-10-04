
# lantern delta — full feature build (AI enabled)

- OpenAI summaries enabled end-to-end (spec + code + workflow env).
- Diagnostics ensures `OPENAI_API_KEY` is set when AI is enabled.
- `Run review` prints: “Summarised X/Y eligible papers via OpenAI.” and “AI summaries step completed.”

## Setup
1. Create a repo and upload all files at the **root**.
2. Settings → Pages → GitHub Actions.
3. Settings → Secrets and variables → **Actions** → add repository secret `OPENAI_API_KEY`.
4. Actions → **lantern-delta** → Run workflow with `dry_run: false` (for real summaries).

## Local smoke test
```bash
python scripts/diagnostics.py
python scripts/run_review.py --spec reviews/iron_esa.yaml --root . --dry-run --limit 5
```
