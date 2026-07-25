"""
Coverage probe — tests HN Algolia hit count for every watched company.
No DB writes. Runs locally. Shows which companies have rich history vs sparse.

Usage:
    python3 probe_coverage.py
    python3 probe_coverage.py --category "India"
    python3 probe_coverage.py --min 0   # show all including zeros
"""

import time
import argparse
import requests

# Same company list from html_formatter.py — duplicated here to avoid importing
# the full briefing stack (which needs DB / Gemini env vars).
COMPANIES = {
    # ── US Big Tech ──────────────────────────────────────
    "Apple":               "US Big Tech",
    "Meta":                "US Big Tech",
    "Microsoft":           "US Big Tech",
    "Google":              "US Big Tech",
    "Amazon":              "US Big Tech",
    "Nvidia":              "US Big Tech",
    "Intel":               "US Big Tech",
    "AMD":                 "US Big Tech",
    "Qualcomm":            "US Big Tech",
    "Broadcom":            "US Big Tech",
    "IBM":                 "US Big Tech",
    # ── AI / LLM ─────────────────────────────────────────
    "OpenAI":              "AI / LLM",
    "Anthropic":           "AI / LLM",
    "xAI":                 "AI / LLM",
    "Mistral":             "AI / LLM",
    "Cohere":              "AI / LLM",
    "Stability AI":        "AI / LLM",
    "Hugging Face":        "AI / LLM",
    "Perplexity":          "AI / LLM",
    "Together AI":         "AI / LLM",
    "Scale AI":            "AI / LLM",
    "Runway":              "AI / LLM",
    "ElevenLabs":          "AI / LLM",
    "Cursor":              "AI / LLM",
    "DeepSeek":            "AI / LLM",
    "Midjourney":          "AI / LLM",
    "Replicate":           "AI / LLM",
    # ── Cloud / Infra ────────────────────────────────────
    "Cloudflare":          "Cloud / Infra",
    "Vercel":              "Cloud / Infra",
    "Netlify":             "Cloud / Infra",
    "DigitalOcean":        "Cloud / Infra",
    "Hetzner":             "Cloud / Infra",
    "Fastly":              "Cloud / Infra",
    "Akamai":              "Cloud / Infra",
    "Equinix":             "Cloud / Infra",
    # ── DevOps / Platform ────────────────────────────────
    "GitHub":              "DevOps / Platform",
    "GitLab":              "DevOps / Platform",
    "HashiCorp":           "DevOps / Platform",
    "Docker":              "DevOps / Platform",
    "Kubernetes":          "DevOps / Platform",
    "Pulumi":              "DevOps / Platform",
    "Atlassian":           "DevOps / Platform",
    "Linear":              "DevOps / Platform",
    "Notion":              "DevOps / Platform",
    # ── Observability ────────────────────────────────────
    "Datadog":             "Observability",
    "Grafana":             "Observability",
    "New Relic":           "Observability",
    "Dynatrace":           "Observability",
    "Elastic":             "Observability",
    "Splunk":              "Observability",
    "PagerDuty":           "Observability",
    "Honeycomb":           "Observability",
    # ── Security ─────────────────────────────────────────
    "CrowdStrike":         "Security",
    "Palo Alto":           "Security",
    "Okta":                "Security",
    "Wiz":                 "Security",
    "Snyk":                "Security",
    "SentinelOne":         "Security",
    "Zscaler":             "Security",
    "Fortinet":            "Security",
    "Cloudflare WAF":      "Security",
    "Check Point":         "Security",
    "CyberArk":            "Security",
    # ── Data / Analytics ─────────────────────────────────
    "Snowflake":           "Data / Analytics",
    "Databricks":          "Data / Analytics",
    "dbt Labs":            "Data / Analytics",
    "Fivetran":            "Data / Analytics",
    "Confluent":           "Data / Analytics",
    "Airbyte":             "Data / Analytics",
    "Starburst":           "Data / Analytics",
    # ── SaaS / Enterprise ────────────────────────────────
    "Salesforce":          "SaaS / Enterprise",
    "ServiceNow":          "SaaS / Enterprise",
    "Workday":             "SaaS / Enterprise",
    "SAP":                 "SaaS / Enterprise",
    "Oracle":              "SaaS / Enterprise",
    "HubSpot":             "SaaS / Enterprise",
    "Zendesk":             "SaaS / Enterprise",
    "Twilio":              "SaaS / Enterprise",
    "Stripe":              "SaaS / Enterprise",
    "Shopify":             "SaaS / Enterprise",
    "Figma":               "SaaS / Enterprise",
    # ── Fintech / Crypto ─────────────────────────────────
    "Coinbase":            "Fintech / Crypto",
    "Block":               "Fintech / Crypto",
    "Robinhood":           "Fintech / Crypto",
    "Plaid":               "Fintech / Crypto",
    "Brex":                "Fintech / Crypto",
    "Ripple":              "Fintech / Crypto",
    "Binance":             "Fintech / Crypto",
    "Klarna":              "Fintech / Crypto",
    # ── Hardware / Transport ─────────────────────────────
    "Tesla":               "Hardware / Transport",
    "SpaceX":              "Hardware / Transport",
    "Uber":                "Hardware / Transport",
    "Waymo":               "Hardware / Transport",
    "Rivian":              "Hardware / Transport",
    "Arm":                 "Hardware / Transport",
    "Applied Materials":   "Hardware / Transport",
    # ── China ────────────────────────────────────────────
    "Baidu":               "China",
    "Alibaba":             "China",
    "Tencent":             "China",
    "ByteDance":           "China",
    "Huawei":              "China",
    "Xiaomi":              "China",
    "DJI":                 "China",
    "Meituan":             "China",
    "JD.com":              "China",
    "CATL":                "China",
    "BYD":                 "China",
    "SenseTime":           "China",
    # ── Korea / Taiwan / Japan ────────────────────────────
    "Samsung":             "Korea / Taiwan / Japan",
    "SK Hynix":            "Korea / Taiwan / Japan",
    "LG":                  "Korea / Taiwan / Japan",
    "Kakao":               "Korea / Taiwan / Japan",
    "Naver":               "Korea / Taiwan / Japan",
    "TSMC":                "Korea / Taiwan / Japan",
    "MediaTek":            "Korea / Taiwan / Japan",
    "ASUSTeK":             "Korea / Taiwan / Japan",
    "Foxconn":             "Korea / Taiwan / Japan",
    "Sony":                "Korea / Taiwan / Japan",
    "SoftBank":            "Korea / Taiwan / Japan",
    "Rakuten":             "Korea / Taiwan / Japan",
    "Toyota":              "Korea / Taiwan / Japan",
    # ── Europe ───────────────────────────────────────────
    "ASML":                "Europe",
    "Spotify":             "Europe",
    "DeepMind":            "Europe",
    "Wise":                "Europe",
    "Revolut":             "Europe",
    "N26":                 "Europe",
    "Klarna EU":           "Europe",
    "UiPath":              "Europe",
    "Siemens":             "Europe",
    "Nokia":               "Europe",
    "Ericsson":            "Europe",
    "LVMH Tech":           "Europe",
    # ── India ────────────────────────────────────────────
    "Infosys":             "India",
    "TCS":                 "India",
    "Wipro":               "India",
    "HCL":                 "India",
    "Reliance Jio":        "India",
    "Flipkart":            "India",
    "Zepto":               "India",
    "PhonePe":             "India",
    "Razorpay":            "India",
    "Freshworks":          "India",
    "Zoho":                "India",
    "Meesho":              "India",
    "Zomato":              "India",
    "CRED":                "India",
    # ── Semiconductor / EDA ──────────────────────────────
    "Marvell":             "Semiconductor",
    "Micron":              "Semiconductor",
    "Texas Instruments":   "Semiconductor",
    "ASIC Cloud":          "Semiconductor",
    "Cadence":             "Semiconductor",
    "Synopsys":            "Semiconductor",
    "KLA":                 "Semiconductor",
    "Lam Research":        "Semiconductor",
}

# HN Algolia: stories mentioning company since 2015-01-01
HN_BASE = "https://hn.algolia.com/api/v1/search"
SINCE_2015 = 1420070400  # unix timestamp


def hn_count(company: str) -> int:
    """Return total HN story count for a company query (single API call, no pagination)."""
    try:
        r = requests.get(
            HN_BASE,
            params={
                "query": company,
                "tags": "story",
                "numericFilters": f"created_at_i>{SINCE_2015}",
                "hitsPerPage": 1,  # we only want nbHits
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("nbHits", 0)
    except Exception as e:
        print(f"  [error] {company}: {e}")
        return -1


def tier(n: int) -> str:
    if n < 0:    return "ERROR"
    if n == 0:   return "NONE "
    if n < 20:   return "BARE "
    if n < 100:  return "LOW  "
    if n < 500:  return "MED  "
    if n < 1000: return "GOOD "
    return               "RICH "


def bar(n: int, width: int = 30) -> str:
    if n <= 0:
        return ""
    cap = 2000
    filled = min(int(n / cap * width), width)
    return "█" * filled + "░" * (width - filled)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", help="Filter to one category")
    parser.add_argument("--min", type=int, default=0, help="Min hits to show (default 0 = all)")
    args = parser.parse_args()

    items = COMPANIES.items()
    if args.category:
        items = [(c, cat) for c, cat in items if cat.lower() == args.category.lower()]

    # Group by category for display
    by_cat: dict[str, list] = {}
    for company, cat in items:
        by_cat.setdefault(cat, []).append(company)

    all_results = []

    print(f"\n{'='*70}")
    print(f"  HN Algolia Coverage Probe — {len(COMPANIES)} companies")
    print(f"  Tier: RICH≥1000  GOOD≥500  MED≥100  LOW≥20  BARE≥1  NONE=0")
    print(f"{'='*70}\n")

    for cat, companies in by_cat.items():
        print(f"── {cat} {'─'*(50 - len(cat))}")
        for company in companies:
            n = hn_count(company)
            t = tier(n)
            b = bar(n)
            label = f"{n:>5}" if n >= 0 else "  ERR"
            print(f"  {t} {label}  {b}  {company}")
            all_results.append((n, cat, company))
            time.sleep(0.15)  # gentle rate limiting
        print()

    # Summary
    valid = [(n, cat, c) for n, cat, c in all_results if n >= 0]
    if not valid:
        return

    print(f"{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    tiers = {"RICH": 0, "GOOD": 0, "MED": 0, "LOW": 0, "BARE": 0, "NONE": 0}
    for n, _, _ in valid:
        t = tier(n).strip()
        tiers[t] = tiers.get(t, 0) + 1

    for t, count in tiers.items():
        print(f"  {t:<6} {count:>3} companies")

    total_signals = sum(n for n, _, _ in valid)
    print(f"\n  Total estimated HN signals: ~{total_signals:,}")
    print(f"  (capped at Algolia's reported nbHits per company)\n")

    # Bottom 10
    poor = sorted(valid, key=lambda x: x[0])[:10]
    print(f"  Lowest coverage (needs RSS supplements):")
    for n, cat, c in poor:
        print(f"    {n:>5}  [{cat}]  {c}")
    print()


if __name__ == "__main__":
    main()
