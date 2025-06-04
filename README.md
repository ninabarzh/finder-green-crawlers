# finder.green crawlers

Creating indexes for finder.green.

## Development requirements

* Use categories [Community Greening](community.md), [Household & Lifestyle Greening](households-and-lifestyles.md), [Surviving Climate Change](surviving-climate-change.md) and [GreenTech](greentech.md).
* Sources: Use search engines, curated lists, public datasets, NGO directories, web archives.
* Language detection: Important for multilingual sites (e.g., `.cl` or `.pt` domains)
* Licensing/Attribution: Respect copyright when extracting content
* `Robots.txt` parsing: Ensure compliance with crawling policies
* Fallback search: If full parsing fails, use site's built-in search or Google `site:` operator
* Monitoring: Alert if a domain is offline or changed dramatically
* Rate-limiting: To avoid bans, throttle crawlers appropriately
* Metadata expansion: Extract social tags (OpenGraph, Twitter/X cards)
* Use codecarbon to estimate carbon emissions per crawl and limit resource-intensive requests https://github.com/mlco2/codecarbon
* Automate sustainability metrics: Integrate APIs like Website Carbon Calculator to assess and/or verify claims of carbon neutrality https://www.websitecarbon.com/api/
* Export to CSV/JSON with fields: `id`, `title`, `description`, `country`, `url`, `cms`, `last_updated`, `category`, `tags`
* Use additional fields like `domain`, `hosting_provider`, and `carbon_footprint`

## Community & Collaboration

* Adopt Best Practices: Follow the OpenSanctions crawler model for issue tracking and volunteer onboarding. https://github.com/opensanctions/crawler-planning
* Partner with NGOs: Collaborate with groups like the African Climate Foundation to expand regional coverage. https://africanclimatefoundation.org/
* Align with the Sustainable Web Manifesto to ensure ethical crawling practices https://sustainablewebdesign.org/
