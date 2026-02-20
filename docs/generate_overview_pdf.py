"""Generate SCORELOCK_OVERVIEW.pdf matching the CodeTrust design."""

from pathlib import Path
from weasyprint import HTML

ACCENT_COLOR = "#6C5CE7"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4;
    margin: 35mm 40mm 30mm 40mm;
  }

  body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    font-size: 9.2pt;
    line-height: 1.5;
    margin: 0;
    padding: 0;
  }

  .title {
    font-size: 30pt;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0 0 4px 0;
    color: #111;
  }

  .subtitle {
    font-size: 9.2pt;
    color: #444;
    margin: 0 0 14px 0;
  }

  .subtitle strong {
    color: #111;
  }

  hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 12px 0 16px 0;
  }

  .section-header {
    font-size: 8pt;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: %(accent)s;
    margin: 16px 0 5px 0;
  }

  .section-header:first-of-type {
    margin-top: 0;
  }

  p {
    margin: 0 0 10px 0;
    text-align: justify;
    hyphens: auto;
  }

  .footer {
    text-align: center;
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px solid #ddd;
  }

  .footer .domain {
    font-size: 10pt;
    font-weight: 700;
    color: #111;
    margin: 0;
  }

  .footer .site {
    font-size: 9pt;
    color: #666;
    margin: 2px 0 0 0;
  }
</style>
</head>
<body>

<div class="title">ScoreLock</div>
<div class="subtitle"><strong>AI-Driven Football Analytics Platform</strong> v0.1.0 — Created by Said Borna</div>

<hr>

<div class="section-header">What it does</div>
<p>
ScoreLock is a football analytics platform that turns raw match data into contextual, actionable
insight. It aggregates fixtures, historical statistics, and bookmaker odds from multiple sources,
runs them through a proprietary ML prediction engine trained on thousands of matches across nine
European leagues, and enriches every prediction with calibrated probabilities, value bet detection,
and real-time news sentiment analysis. The platform then auto-generates original Swedish-language
editorial content — match previews, post-match reports, round summaries, and value bet alerts —
producing thousands of unique SEO-indexable pages per season. It ships as a full-stack SaaS with
subscription tiers, a social tipping league, and integrated affiliate monetisation.
</p>

<div class="section-header">How it's built</div>
<p>
The platform is a vertically integrated system — multi-source data pipeline, ML engine, AI content
generator, real-time infrastructure, and consumer frontend — built and operated as a single
codebase. Autonomous scheduled tasks handle data synchronisation, daily predictions, model
retraining, and content publishing without manual intervention. The architecture is designed for
resilience across multiple data providers and for scale toward additional leagues, languages,
and sports.
</p>

<div class="section-header">Why it exists</div>
<p>
The football analytics space is fragmented. Livescore apps deliver data without context. Statistics
platforms provide depth without betting insight. Betting sites offer odds designed to profit from
the user, not inform them. Legacy tipping media relies on manual, shallow analysis that cannot
scale. No single product combines live data, ML-driven predictions, odds analysis, sentiment
tracking, and auto-generated editorial content in one platform. ScoreLock was built for this gap:
an independent, data-driven analytics layer that gives football enthusiasts and semi-professional
bettors the full picture — numbers, context, and narrative — without the bias of a bookmaker
behind it.
</p>

<div class="section-header">Current state</div>
<p>
ScoreLock is in active development with a clear trajectory toward market launch. The core platform
is production-stable with the data pipeline, prediction engine, content generator, frontend,
affiliate integration, and tipping league fully built. The remaining work centres on distribution,
visual polish, and league expansion. The ambition is a fully market-ready product positioned to
compete seriously in the Nordic football analytics space, with a sustainable revenue model built
on affiliate partnerships and premium subscriptions — designed from day one for scale.
</p>

<div class="footer">
  <div class="domain">scorelock.saidborna.com</div>
  <div class="site">saidborna.com</div>
</div>

</body>
</html>
""" % {"accent": ACCENT_COLOR}

OUTPUT_DIR = Path(__file__).parent
OUTPUT_PATH = OUTPUT_DIR / "SCORELOCK_OVERVIEW.pdf"


def main() -> None:
    """Generate the overview PDF."""
    html = HTML(string=HTML_CONTENT)
    html.write_pdf(str(OUTPUT_PATH))
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
