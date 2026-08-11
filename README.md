# Positdev sales explorer

A [Shiny for Python](https://shiny.posit.co/py/) app set up for **git-backed
publishing** to Posit Connect.

The dataset is generated from a fixed seed (`SEED = 20260811` in `app.py`) rather
than read from disk, so a deployed copy shows byte-identical numbers to a local
one. That makes it a useful smoke test: if the deployed app's **Runtime** card
matches your local one, the environment restored correctly.

## Files that matter for deployment

| File | Role |
|---|---|
| `app.py` | The app. Entrypoint object is `app`, so the entrypoint is `app:app`. |
| `requirements.txt` | Pinned dependencies Connect installs. |
| `manifest.json` | **Required for git-backed publishing.** Tells Connect the app mode, entrypoint, Python version, and file checksums. |

## Run locally

```bash
pip install -r requirements.txt
shiny run --reload app.py
```

Then open http://127.0.0.1:8000.

## Deploy: Posit Connect (git-backed)

Connect polls the repo and redeploys when the tracked branch changes. No CLI
push is involved.

1. Push this repo to GitHub (see *Branch note* below).
2. If the repo is private, give Connect access — either make it public, or add a
   deploy key / PAT under **Connect → Dashboard → Publish → Import from Git**.
3. In Connect, click **Publish → Import from Git**, then supply:
   - **Repository URL** — `https://github.com/sairevanth507wbg/Positdev-testing.git`
   - **Branch** — the branch you pushed
   - **Directory** — `.` (the manifest is at the repo root)
4. Connect reads `manifest.json`, restores `requirements.txt`, and deploys.

Connect re-checks the branch on an interval set by the server admin
(`Git.PollingFrequency`, default 15 minutes). Push to the tracked branch to ship
an update.

### Regenerate the manifest after any change

`manifest.json` stores a **checksum of every deployed file**. If you edit
`app.py` or `requirements.txt` and don't regenerate, Connect deploys stale
content or fails the checksum check.

```bash
rsconnect write-manifest shiny --overwrite --entrypoint app:app .
```

Commit the regenerated `manifest.json` together with the change.

> On Windows the console script may not be on `PATH`; call it directly, e.g.
> `& "C:\WBG\Python313\Scripts\rsconnect.exe" write-manifest shiny --overwrite --entrypoint app:app .`

## Deploy: Posit Connect Cloud

[connect.posit.cloud](https://connect.posit.cloud) deploys straight from GitHub
and reads `requirements.txt` — it ignores `manifest.json`, which is harmless to
leave in place. Pick the repo, branch, and `app.py` as the entrypoint.

## Requirements on the server

- **Python 3.13** — `manifest.json` records `3.13.7`. Connect matches an
  installed interpreter; if the server has no 3.13.x, deployment fails. Lower the
  pins and regenerate the manifest if your server runs an older Python.
- `pandas==3.0.5` and `numpy==2.5.2` are recent releases. If your Connect server
  installs from an internal mirror rather than PyPI, confirm those versions are
  available before the first deploy.
