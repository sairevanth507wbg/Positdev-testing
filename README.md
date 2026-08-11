# Positdev-testing

A multi-app repo for **git-backed publishing** to Posit Connect.

Connect deploys from a *repository + branch + directory*, so each app lives in
its own folder with its own `manifest.json` and `requirements.txt`. Apps are
fully isolated: different dependencies, different Python pins, independent
deploys. Adding an app never disturbs an existing one.

## Layout

```
.
├── apps/
│   └── sales-explorer/      <- one Connect app
│       ├── app.py           entrypoint object `app`  ->  app:app
│       ├── requirements.txt this app's pinned deps
│       └── manifest.json    REQUIRED for git-backed publishing
├── .gitattributes           forces LF (see "Line endings")
├── .gitignore
└── README.md
```

Repo-level files stay at the root; everything an app needs stays inside its own
folder. Connect never looks above the directory you point it at.

## Apps

| App | Directory | Entrypoint | Deploys as |
|---|---|---|---|
| Sales explorer | `apps/sales-explorer` | `app:app` | `python-shiny` |

### Sales explorer

Filters a synthetic order book by date, region, channel, and minimum order
value; shows KPI tiles, a grouped revenue summary, the matching orders, and a
CSV download of whatever is currently filtered.

The dataset is generated from a fixed seed (`SEED = 20260811`) rather than read
from disk, so a deployed copy shows byte-identical numbers to a local one. The
**Runtime** card reports `APP_VERSION`, the interpreter, and the restored
package versions — if it matches your local run, the environment restored
correctly. Bump `APP_VERSION` when you want to confirm a redeploy actually
landed.

Run it locally:

```bash
cd apps/sales-explorer
pip install -r requirements.txt
shiny run --reload app.py
```

## Deploy to Posit Connect (git-backed)

Connect polls the branch and redeploys on change — there is no CLI push.

1. In Connect: **Publish → Import from Git**.
2. Supply:
   - **Repository URL** — `https://github.com/sairevanth507wbg/Positdev-testing.git`
   - **Branch** — the branch you want tracked
   - **Directory** — the app folder, e.g. `apps/sales-explorer`
3. Connect reads that folder's `manifest.json`, restores its `requirements.txt`,
   and deploys.

Repeat per app, pointing each Connect item at a different directory. Connect
re-checks on an interval set by the server admin (`Git.PollingFrequency`,
default 15 minutes).

If the repo is private, grant Connect access first — make it public, or add a
deploy key / PAT in the same Import from Git screen.

## Adding another app

```bash
mkdir -p apps/<new-app>
# write app.py and requirements.txt in that folder, then:
rsconnect write-manifest shiny --overwrite --entrypoint app:app apps/<new-app>
```

Commit the folder and point a new Connect item at `apps/<new-app>`. Nothing
about the existing apps changes.

> On Windows the console script may not be on `PATH`; call it directly:
> `& "C:\WBG\Python313\Scripts\rsconnect.exe" write-manifest shiny --overwrite --entrypoint app:app apps/<new-app>`

## Regenerate the manifest after every change

`manifest.json` stores a **checksum of each deployed file**. Edit `app.py` or
`requirements.txt` without regenerating and Connect deploys stale content or
fails the checksum check.

```bash
rsconnect write-manifest shiny --overwrite --entrypoint app:app apps/sales-explorer
```

Commit the regenerated manifest together with the change. Only the app you
touched needs regenerating.

## Line endings

`.gitattributes` forces `eol=lf` repo-wide. This is load-bearing, not style:
`manifest.json` stores MD5s of the file bytes, and with Windows' default
`core.autocrlf=true` your checkout would be CRLF while Connect clones LF on
Linux — so locally-generated checksums would not match what Connect sees.

## Server requirements

- **Python 3.13** — each `manifest.json` records `3.13.7`. Connect matches an
  installed interpreter; if the server has no 3.13.x, deployment fails. Lower
  the pins and regenerate if your server runs older Python.
- `pandas==3.0.5` / `numpy==2.5.2` are recent. If Connect installs from an
  internal mirror rather than PyPI, confirm those versions are available.

## Deploy to Posit Connect Cloud

[connect.posit.cloud](https://connect.posit.cloud) deploys from GitHub and reads
`requirements.txt`; it ignores `manifest.json`, which is harmless to leave in
place. Select the repo, branch, and `apps/sales-explorer/app.py` as the
entrypoint.
