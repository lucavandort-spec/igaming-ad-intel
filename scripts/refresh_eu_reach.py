"""Refresh EU reach, run dates and active status for the ads in data/ads.json
using Meta's official Ad Library API.

Needs a Meta access token with Ad Library API access in META_ACCESS_TOKEN
(https://www.facebook.com/ads/library/api). For non-political ads the API only
returns ads delivered in the EU, which is also the only place Meta publishes reach.

Usage:
    META_ACCESS_TOKEN=... python3 scripts/refresh_eu_reach.py

Writes data/ads.json in place and lists EU ads from tracked advertisers that are
not on the dashboard yet in data/new_ads.json (they need images, so they are
added on the next full scrape).
"""
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0/ads_archive"
EU = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
      "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
FIELDS = ",".join(["id", "page_id", "page_name", "ad_delivery_start_time", "ad_delivery_stop_time",
                   "eu_total_reach", "age_country_gender_reach_breakdown", "ad_creative_bodies"])
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ads.json")
COUNTRY_NAMES = {"AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia", "CY": "Cyprus",
                 "CZ": "Czechia", "DK": "Denmark", "EE": "Estonia", "FI": "Finland", "FR": "France",
                 "DE": "Germany", "GR": "Greece", "HU": "Hungary", "IE": "Ireland", "IT": "Italy",
                 "LV": "Latvia", "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "NL": "Netherlands",
                 "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia", "SI": "Slovenia",
                 "ES": "Spain", "SE": "Sweden"}


def get(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            sys.exit(f"Ad Library API error {e.code}: {body[:400]}")


def fetch_pages(token, page_ids):
    params = {"access_token": token, "ad_type": "ALL", "ad_active_status": "ALL",
              "ad_reached_countries": json.dumps(EU), "search_page_ids": json.dumps(page_ids),
              "fields": FIELDS, "limit": 250}
    data = get(API, params)
    while True:
        yield from data.get("data", [])
        nxt = data.get("paging", {}).get("next")
        if not nxt:
            break
        data = get(nxt)


def breakdown(rows):
    ctry, ages, gen = {}, {}, {}
    for c in rows or []:
        name = COUNTRY_NAMES.get(c.get("country"), c.get("country"))
        for g in c.get("age_gender_breakdowns", []):
            total = sum(int(g.get(k) or 0) for k in ("male", "female", "unknown"))
            ctry[name] = ctry.get(name, 0) + total
            ages[g.get("age_range")] = ages.get(g.get("age_range"), 0) + total
            for k, label in (("male", "Male"), ("female", "Female"), ("unknown", "Unknown")):
                gen[label] = gen.get(label, 0) + int(g.get(k) or 0)
    return ctry, ages, gen


def rescore(ads, reach_sorted):
    """Same formula as the dashboard: 45% traffic, 40% days live, 15% creative reuse."""
    import bisect
    import math
    for a in ads:
        imp = 1 - (a["pos"] - 1) / max(a["n"], 1)
        traffic = (bisect.bisect_right(reach_sorted, a["reach"]["n"]) / len(reach_sorted)
                   if a.get("reach") and reach_sorted else 0.8 * imp)
        longevity = min(math.log1p(a.get("days") or 0) / math.log1p(365), 1)
        reuse = min(math.log(a["cc"]) / math.log(20), 1) if a["cc"] > 1 else 0
        a["traffic"] = round(traffic * 100)
        a["score"] = round(100 * (0.45 * traffic + 0.40 * longevity + 0.15 * reuse), 1)
    ads.sort(key=lambda a: -a["score"])


def main():
    token = os.environ.get("META_ACCESS_TOKEN")
    if not token:
        sys.exit("Set META_ACCESS_TOKEN first.")
    db = json.load(open(DATA))
    ads = {a["id"]: a for a in db["ads"]}
    page_ids = sorted({a["pid"] for a in db["ads"] if a["eu"]})
    today = datetime.date.today()
    seen, new = set(), []
    for i in range(0, len(page_ids), 10):
        for row in fetch_pages(token, page_ids[i:i + 10]):
            ad = ads.get(row["id"])
            if not ad:
                if row.get("ad_delivery_stop_time") is None:
                    new.append({"id": row["id"], "brand": row.get("page_name"), "reach": row.get("eu_total_reach"),
                                "start": row.get("ad_delivery_start_time"),
                                "body": (row.get("ad_creative_bodies") or [""])[0][:200]})
                continue
            seen.add(row["id"])
            start = row.get("ad_delivery_start_time")
            if start:
                ad["start"] = start[:10]
                stop = row.get("ad_delivery_stop_time")
                end = datetime.date.fromisoformat(stop[:10]) if stop else today
                ad["days"] = (end - datetime.date.fromisoformat(start[:10])).days
                ad["active"] = stop is None
            if row.get("eu_total_reach"):
                ctry, ages, gen = breakdown(row.get("age_country_gender_reach_breakdown"))
                tot = sum(gen.values()) or 1
                ad["reach"] = {"n": int(row["eu_total_reach"]),
                               "male": round(100 * gen.get("Male", 0) / tot),
                               "female": round(100 * gen.get("Female", 0) / tot),
                               "age": max(ages, key=ages.get) if ages else None, "ages": ages,
                               "ctry": sorted(ctry.items(), key=lambda x: -x[1])[:3]}
    reach = sorted(a["reach"]["n"] for a in db["ads"] if a.get("reach"))
    rescore(db["ads"], reach)
    db["meta"].update({"refreshed": today.isoformat(), "withReach": len(reach), "totalReach": sum(reach)})
    json.dump(db, open(DATA, "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(sorted(new, key=lambda x: -(x["reach"] or 0)), open(os.path.join(ROOT, "data", "new_ads.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"Updated {len(seen)} ads, {len(reach)} with reach. {len(new)} new EU ads listed in data/new_ads.json.")


if __name__ == "__main__":
    main()
