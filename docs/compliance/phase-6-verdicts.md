# Phase 6 compliance verdicts

Reviewed 2026-07-26 with the identifying user agent, fetching each site's
robots.txt and terms locally. Built adapters carry the full record in their
`SourcePolicy.terms_notes`; this file is the register for every source the
phase reviewed, including those that produced no adapter. Sections quote or
cite the exact pages read so each verdict is auditable.

## Built

### adjudicators_office — pass

gov.uk robots.txt disallows only print views and site-search paths. All
gov.uk content is Crown copyright under the Open Government Licence v3.0
except where stated (site footer); the annual report pages carry no contrary
statement. Discovery and fetches use the documented public APIs
(`/api/search.json`, `/api/content`). Method: official API.

### leo_decisions — pass

legalombudsman.org.uk robots.txt disallows only CMS internals (`/umbraco/`,
`/bin/`, `/config/`, `/temp/`). The site publishes no terms-of-use or
copyright page at all (privacy and accessibility policies only, confirmed
against the sitemap), so no terms restrict collection. The
ombudsman-decision-data page offers the CSV explicitly as a downloadable
file. Method: bulk download.

### committee_evidence — pass

committees-api.parliament.uk is UK Parliament's documented public API
(contact softwareengineering@parliament.uk in its OpenAPI spec); it serves
no robots.txt (404) and answers plain HTTP clients, while the committees
website sits behind a Cloudflare challenge, so only the API is used.
Written evidence is parliamentary copyright under the Open Parliament
Licence v3.0 (text verified via SPDX record OPL-UK-3.0): copying,
publishing, adaptation and commercial use are granted with attribution.
Method: official API.

Note: the plan bundles "consultation responses" into this slot. Committee
inquiries capture much of that material, but regulator consultation
responses (FCA/HMT) have no single lawful bulk source and need a scoping
decision before any further adapter.

## Resolved by the owner, 2026-07-27

The three verdicts below were put to the owner at the phase 6 review pause
and decided on 2026-07-27: FCA complaints returns proceeds with the residual
risk accepted (the fos_decisions pattern), Find Case Law is parked without a
licence application, and the iTunes reviews feed is declared `official_api`
on the purposive reading. The two proceeding sources are built; their
`SourcePolicy.terms_notes` restate the acceptance.

### fca_complaints_returns — judgement call: OGL grant vs anti-bot clause

fca.org.uk/legal (last updated 30/07/2025), read in full:

- Clause 2.2 expressly places "charts, figures, graphs, diagrams, tables and
  numerical datasets published within the Data section of this site" under
  the UK Open Government Licence, replacing the restrictive clauses 3.2-3.5.
  The firm-level complaints returns XLSX files are numerical datasets in the
  Data section (`/data/complaints-data/firm-level`), so the OGL's grant to
  copy, publish and distribute applies to them.
- Clause 4.8(iii) forbids using any "'scraper,' 'robot,' 'bot,' 'spider,'
  'data mining,' 'computer code,' or any other automated device ... to
  access, acquire, copy, or monitor any portion of the website" without
  prior written consent.

robots.txt allows the data pages and file paths (only query-string URLs and
CMS directories are disallowed). A scripted twice-yearly download of
OGL-licensed files with an identifying user agent is plainly the intended
use of published open data, and could not engage the "unreasonable burden"
clause; but clause 4.8(iii) read literally catches any scripted GET. This is
the same terms-versus-practice tension the owner accepted for fos_decisions
("proceed, record the risk", 2026-07-25). Download verified working (2025-H2
firm-level XLSX, 114 KB; history to 2013 enumerable from one robots-clean
page). **Owner decision 2026-07-27: risk accepted, proceed.** Method: bulk
download.

### tribunal_decisions (TNA Find Case Law) — licence application required

caselaw.nationalarchives.gov.uk/terms-of-use (20 August 2024) and
"When you need permission", read in full: reuse falls under the Open Justice
Licence v2.0, which **excludes computational analysis**. The guidance
defines computational analysis as including "text mining across large
numbers of judgments", "bulk extraction of data from judgments",
"statistical analysis across the full collection" and "automated
identification or classification of judgments" — precisely what
problem-finder's ingestion plus enrichment does. A separate computational
analysis licence is required; **applications are free** (see "What you need
to apply"; contact caselawlicence@nationalarchives.gov.uk). robots.txt
allows general agents (the named disallows target AI-training crawlers).
Verdict: do not build under the OJL alone. Options: the owner applies for
the free licence, or the source is parked. Never BAILII (its terms prohibit
harvesting; plan 1f). **Owner decision 2026-07-27: parked, no licence
application.** Revisit only if the owner later applies and the licence is
granted.

### app_store_reviews (iTunes RSS) — judgement call: robots disallow on the feed path

itunes.apple.com/robots.txt disallows `/*/rss/*` for all user agents, which
catches the customer-reviews feed path; the feed itself answers normally and
is Apple's long-standing official feed for app reviews. The compliance gate
hard-blocks robots-DISALLOWED only for scrape and bulk-download methods; an
`official_api` declaration would pass mechanically. The purposive reading is
that the robots disallow aims at search-engine indexing of feed pages, not
at feed consumption (feeds exist to be polled); the literal reading is that
Apple disallows automated access to those paths. **Owner decision
2026-07-27: declared `official_api` on the purposive reading, robots status
recorded DISALLOWED honestly in the policy.** Method: official API.

## Manual-import-only (gate fails, plan 1g expectation confirmed)

### trustpilot

Terms of Use for Consumers (legal.trustpilot.com, February 2025) bind anyone
using the platform "directly or indirectly (including, for example, through
use of automated technologies such as AI agents or screen scrapers)" and
state "You must not modify, copy, adapt, reproduce ... any part of our
platform". No public reviews API without a business licence. Fail.

### google_reviews

Google Terms of Service (policies.google.com/terms) prohibit "using
automated means to access content from any of our services in violation of
the machine-readable instructions on our web pages" and treat "scraping
content that doesn't belong to you" as abuse; Maps robots.txt disallows the
relevant paths. The Places API's terms restrict storing and caching content.
Fail.

### play_store

Same Google Terms of Service govern play.google.com; there is no public API
for third-party apps' reviews (the Play Developer API covers only one's own
apps). Fail.

### mse (MoneySavingExpert forum)

The terms page itself returns 403 to non-browser clients, so its terms
cannot even be reviewed automatically; forum content is user-generated with
MSE claiming licence over it. Plan resolved decision 5 already fixed this as
manual-import-only. Fail.
