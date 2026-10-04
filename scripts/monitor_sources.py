import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
STATE = ROOT / "data" / "source-status.json"
REPORT = ROOT / "data" / "change-report.json"

html = INDEX.read_text(encoding="utf-8", errors="ignore")

urls = sorted(set(re.findall(r'https?://[^"\\\'<> ]+', html)))

# Ignore technical/non-source URLs.
urls = [
    u for u in urls
    if not any(x in u for x in [
        "vercel.app",
        "github.com",
        "uidai.gov.in"
    ])
]

old = {}
if STATE.exists():
    try:
        old = json.loads(
            STATE.read_text(encoding="utf-8")
        ).get("sources", {})
    except Exception:
        old = {}

now = datetime.now(timezone.utc)

sources = {}
changed = []
failed = []

for url in urls:
    item = {
        "url": url,
        "status": "error",
        "checked_at": now.isoformat()
    }

    try:
        req = Request(
            url,
            headers={
                "User-Agent":
                "SmartBenefitFinder-SourceMonitor/1.0"
            }
        )

        with urlopen(req, timeout=20) as r:
            raw = r.read(2_000_000)
            ctype = r.headers.get("content-type", "")

        text = raw.decode("utf-8", errors="ignore")

        # Remove volatile content before comparison.
        text = re.sub(
            r"<script[\s\S]*?</script>",
            " ",
            text,
            flags=re.I
        )
        text = re.sub(
            r"<style[\s\S]*?</style>",
            " ",
            text,
            flags=re.I
        )
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        digest = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

        item.update({
            "status": "ok",
            "hash": digest,
            "content_type": ctype
        })

        previous_hash = old.get(url, {}).get("hash")

        if previous_hash and previous_hash != digest:
            changed.append({
                "url": url,
                "previous_hash": previous_hash,
                "new_hash": digest
            })

    except Exception as e:
        item["error"] = str(e)[:300]
        failed.append({
            "url": url,
            "error": str(e)[:300]
        })

    sources[url] = item


# Main monitoring status.
out = {
    "last_checked": now.isoformat(),
    "last_checked_display": now.astimezone().strftime(
        "%d %b %Y, %I:%M %p UTC"
    ),
    "sources_checked": len(urls),
    "changed_sources": len(changed),
    "changed_urls": [x["url"] for x in changed],
    "failed_sources": len(failed),
    "sources": sources
}

STATE.parent.mkdir(
    parents=True,
    exist_ok=True
)

STATE.write_text(
    json.dumps(
        out,
        indent=2,
        ensure_ascii=False
    ) + "\n",
    encoding="utf-8"
)


# Separate human-readable change report.
report = {
    "generated_at": now.isoformat(),
    "summary": {
        "sources_checked": len(urls),
        "changed_sources": len(changed),
        "failed_sources": len(failed)
    },
    "changed_sources": changed,
    "failed_sources": failed,
    "action": (
        "Review changed official sources before "
        "changing any eligibility rules."
        if changed
        else
        "No source changes detected. No eligibility "
        "rules require review."
    )
}

REPORT.write_text(
    json.dumps(
        report,
        indent=2,
        ensure_ascii=False
    ) + "\n",
    encoding="utf-8"
)

print(
    json.dumps({
        "sources_checked": len(urls),
        "changed_sources": len(changed),
        "failed_sources": len(failed)
    })
)
