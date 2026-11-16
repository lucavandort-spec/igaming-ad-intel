# Casino Ad Intel

A dashboard of live casino-related ads from Meta's Ad Library, worldwide, ranked by
how long each ad has been running and how many people it reached.

**Live:** see the GitHub Pages link in the repo's About panel.

## What's in it
- `index.html`: the dashboard (static, no build step)
- `data/ads.json`: every ad with brand, market, category, format, start date, days live,
  measured EU reach and demographics where Meta publishes them, and scores
- `images/<ad id>.jpg`: the creative (static image, or the video's thumbnail)
- `designs/`: other pages, shown under the dashboard's **Designs** tab (see below)

## How traffic is measured
Meta publishes reach (people who saw an ad) **only for ads shown in the EU**. Those ads
show a measured number. For everything else Meta publishes no numbers, so the dashboard
estimates traffic from where the ad sits in Meta's "most impressions" ordering for that
advertiser.

## Keeping the data fresh
`scripts/refresh_eu_reach.py` updates reach, run dates and active status through Meta's
official Ad Library API. The `Refresh EU reach` GitHub Action runs it every Monday once a
`META_ACCESS_TOKEN` repository secret is added:

1. Get Ad Library API access at https://www.facebook.com/ads/library/api (needs a
   Facebook developer account with identity confirmation) and create an access token.
2. In this repo: Settings → Secrets and variables → Actions → New repository secret →
   name `META_ACCESS_TOKEN`.
3. Actions → Refresh EU reach → Run workflow to test it.

Each push to `main` redeploys the site, so any data update shows up within a minute or two.

New ads and non-EU markets (UK, US, Canada, LatAm) are not covered by the API, so those
come from a full re-scrape of the public Ad Library (`scripts/scrape/` holds the
extraction scripts and category rules used for the first pull).

## Designs
- `designs/sir-betalot-statics.html`: gallery of twenty Sir Betalot static ads, each in 4:5
  and 9:16 (JPGs in `designs/sir-betalot/v1` and `v2`). Set 1 (12 Nov 2026) is the ten
  researched concepts on one template; set 2 (15 Nov 2026) is ten experimental visual styles.
  All copy is sample. Sources and render scripts live outside this repo, in `creatives/`.

Self-contained pages (data embedded, no build step) built from a StrategyTune EURUSD 15m
backtest session:

- `designs/trade-calendar.html`: daily P&L calendar with equity and drawdown curves,
  P&L by entry day and hour, R-multiple distribution, exit types and the full trade list.
- `designs/eval-simulator.html`: replays the trades through prop-firm eval rules ($25,000
  account, $200 risk per trade, +$1,250 to pass, −$1,000 to fail, a fresh account after
  each pass or fail) and shows every result plus the eval currently running. The rules can
  be changed on the page.

Both are snapshots of the session as saved on 12 Nov 2026 (115 trades). Live versions that
refresh from StrategyTune exist as private Claude artifacts and only open for the owner's
Claude account.

## Snapshot
First pull: 10 Nov 2026. 1,889 ads from 258 advertisers across 43 markets; 137 ads with
measured EU reach.
