# finder.green crawlers

Creating indexes for finder.green.

---

## Crawling plan for Indices

### 1. Discover & curate initial URLs

* Action: Organise your categories (e.g. [Community Greening](community.md), [Household & Lifestyle Greening](households-and-lifestyles.md), [Surviving Climate Change](surviving-climate-change.md)).
* Sources: Use search engines, curated lists, public datasets, NGO directories, web archives.
* Tools:

  * Manual discovery + OpenSearch queries
  * Optional: use Python + DuckDuckGo API or SerpAPI

---

### 2. Identify site Software / CMS

* Action: Detect underlying site software (WordPress, Hugo, Drupal, etc.)
* How:

  * Look at HTTP headers, `meta` tags, `generator` meta tags
  * Fingerprint patterns in HTML (e.g., `wp-content`, `ghost-url`)
* Tools:

  * [`Wappalyzer`](https://www.wappalyzer.com/)
  * [`builtwith`](https://builtwith.com/) API
  * Custom Python using `requests` + `BeautifulSoup`

---

### 3. Detect Last Update Date

* Action: Try to get the most recent post/page/article timestamp
* Options:

  * Parse `<time>` or `<meta name="last-modified">`
  * Look for blog post dates via regex or structured data (`ld+json`)
  * Use sitemap if available: `/sitemap.xml`
* Fallback:

  * Use HTTP `Last-Modified` header from homepage or blog index
* Tools:

  * `requests.head` for header scraping
  * `sitemap-parser`, `feedparser`

---

### 4. Build crawlers for each site

* Action: Create small focused crawlers for each domain (respect `robots.txt`)
* Goal: Extract structured info:

  * `title`, `description`, `country`, `URL`, `CMS`, `last_updated`, `category`

* Toolchain:

  * Scrapy: for structured multi-page sites
  * Sitemap/Feed Readers: for blogs
  * Python + BeautifulSoup: for targeted scrapes
* 
* Output format: JSON objects per entry, example:

```json
{
  "id": "omved-gardens",
  "title": "OmVed Gardens",
  "description": "Urban ecological project in North London...",
  "url": "https://www.omvedgardens.com",
  "country": "UK",
  "category": "Community Greening",
  "cms": "Custom CMS",
  "last_updated": "2025-05-29T00:00:00Z"
}
```

---

### 5. Enrich and Validate Data

* Add:

  * Tags (e.g., `urban`, `agroecology`, `adaptation`, etc.)
  * Language (ISO code, from `lang` tag or `cld3`)
* Validate:

  * Ensure URLs resolve (status 200)
  * Trim excessive HTML
  * Remove duplicates or redirects

---

### 6. Transform to Typesense-Ready JSON

* Action: Convert each record to a flat JSON structure
* Fields:

  * `id`, `title`, `description`, `country`, `url`, `cms`, `last_updated`, `category`, `tags`
* Tool:

  * Python script to clean and export as newline-delimited JSON or full array
  * Example output: `community_greening.ndjson`

---

### 7. Push to Typesense

* Setup:

  * Define schema in Typesense (collection per category, or one unified)

* Index:

* Use the Typesense Python client or CLI:

```python
from typesense import Client
client.collections['green_sites'].documents.import_jsonl(open('community_greening.ndjson'))
```

* Search options:

  * Use fuzzy search, filter by category/country, sort by date

---

### 8. Schedule Recrawls

* Action: Automate a refresh every 1–3 months
* Tool:

  * GitHub Actions
  * Store previous hashes to avoid reprocessing unchanged entries

---

### Additional requirements

* Language Detection: Important for multilingual sites (e.g., `.cl` or `.pt` domains)
* Licensing / Attribution: Respect copyright when extracting content
* Robots.txt Parsing: Ensure compliance with crawling policies
* Fallback Search: If full parsing fails, use site's built-in search or Google `site:` operator
* Monitoring: Alert if a domain goes offline or changes dramatically
* Rate-Limiting: To avoid bans, throttle crawlers appropriately
* Metadata Expansion: Extract social tags (OpenGraph, Twitter cards)

