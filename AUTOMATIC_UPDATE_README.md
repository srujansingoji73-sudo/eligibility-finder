# Smart Benefit Finder — Automatic Source Monitoring

This upgrade adds scheduled monitoring of the official source URLs already used by the website.

## What happens automatically
1. GitHub Actions runs once every day.
2. It reads the official source URLs from `index.html`.
3. It downloads and normalizes each public source page.
4. It compares a content fingerprint with the previous check.
5. `data/source-status.json` is updated automatically.
6. If a source changed, a GitHub issue is opened for review.
7. Vercel can redeploy the status update automatically because the repository is connected to Vercel.

## Safety rule
The system does **not** silently rewrite eligibility rules. A changed government page can contain layout changes, announcements, or unrelated edits. The change is therefore flagged first, and the relevant opportunity rule is updated only after checking the official source.

## Schedule
Daily at 03:17 UTC (08:47 IST).

## Repository placement
Copy the package contents into the root of the `eligibility-finder` repository, preserving:
- `.github/workflows/monitor-official-sources.yml`
- `scripts/monitor_sources.py`
- `data/source-status.json`
- `index.html`

Then commit and push. GitHub Actions must be enabled for the repository.
