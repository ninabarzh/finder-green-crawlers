# green_site_crawler.py
import hashlib
import re
import json
import socket
from pathlib import Path
import asyncio
import signal
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


# DNS resolution helper
def is_domain_resolvable(url: str) -> bool:
    try:
        hostname = re.sub(r'^https?://', '', url).split('/')[0]
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False


def get_urls(category_filter: Optional[str] = None):
    base_path = Path(__file__).parent / "lists"
    categories = {
        'community.md': 'Community Greening',
        'households-and-lifestyles.md': 'Household Greening',
        'surviving-climate-change.md': 'Surviving Climate Change',
    }

    header_pattern = re.compile(r'^##\s+(.+)$')
    kv_pattern = re.compile(r'-\s*(\w+(?:\s\w+)*):\s*(.+)')

    results = []

    for filename, category in categories.items():
        if category_filter and category != category_filter:
            continue

        filepath = base_path / filename
        if not filepath.exists():
            print(f"⚠️ File not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            current_entry = {}
            current_site_name = None

            for line in f:
                line = line.strip()
                if not line:
                    continue
                header_match = header_pattern.match(line)
                if header_match:
                    if 'Website' in current_entry:
                        website_line = current_entry.get('Website', '')
                        url_match = re.search(r'\((https?://[^)]+)\)', website_line)
                        if url_match:
                            url = url_match.group(1)
                            if is_domain_resolvable(url):
                                results.append({
                                    'url': url,
                                    'category': category,
                                    'country': current_entry.get('Country', 'Unknown'),
                                    'site_name': current_site_name or 'Unknown',
                                    'description': current_entry.get('Description', '').strip(),
                                    'framework': current_entry.get('Framework', '').strip(),
                                    'last_update': current_entry.get('Last Update', '').strip(),
                                })
                    current_entry = {}
                    current_site_name = header_match.group(1).strip()
                else:
                    kv_match = kv_pattern.match(line)
                    if kv_match:
                        key = kv_match.group(1)
                        value = kv_match.group(2)
                        current_entry[key] = value

            # Check last entry after file ends
            if 'Website' in current_entry:
                website_line = current_entry.get('Website', '')
                url_match = re.search(r'\((https?://[^)]+)\)', website_line)
                if url_match:
                    url = url_match.group(1)
                    if is_domain_resolvable(url):
                        results.append({
                            'url': url,
                            'category': category,
                            'country': current_entry.get('Country', 'Unknown'),
                            'site_name': current_site_name or 'Unknown',
                            'description': current_entry.get('Description', '').strip(),
                            'framework': current_entry.get('Framework', '').strip(),
                            'last_update': current_entry.get('Last Update', '').strip(),
                        })

    return results


async def crawl_page(page, url_info):
    try:
        await page.goto(url_info['url'], timeout=60000)
        await page.wait_for_load_state('load')

        content = await page.content()
        title = await page.title()

        description = ''
        try:
            description = await page.locator('meta[name="description"]').get_attribute('content') or ''
        except (PlaywrightTimeoutError, PlaywrightError):
            pass

        cms = 'Unknown'
        if '/wp-content/' in content:
            cms = 'WordPress'
        elif 'ghost-url' in content:
            cms = 'Ghost'
        elif 'staticman' in content:
            cms = 'Static Site (Staticman)'
        elif '/sites/default/files/' in content:
            cms = 'Drupal'

        last_updated = 'Unknown'
        try:
            meta_date = await page.locator('meta[property="article:modified_time"]').get_attribute('content')
            if meta_date:
                last_updated = meta_date
        except (PlaywrightTimeoutError, PlaywrightError):
            pass

        author = 'Unknown'
        try:
            author_meta = await page.locator('meta[name="author"]').get_attribute('content')
            if author_meta:
                author = author_meta.strip()
        except (PlaywrightTimeoutError, PlaywrightError):
            pass

        tags = []
        try:
            keywords = await page.locator('meta[name="keywords"]').get_attribute('content')
            if keywords:
                tags = [tag.strip() for tag in keywords.split(',') if tag.strip()]
        except (PlaywrightTimeoutError, PlaywrightError):
            pass

        item = {
            'id': hashlib.md5(url_info['url'].encode()).hexdigest()[:8],
            'title': title[:100],
            'description': description[:200],
            'country': url_info['country'],
            'url': url_info['url'],
            'cms': cms,
            'last_updated': last_updated,
            'category': url_info['category'],
            'author': author,
            'tags': tags,
        }

        return item

    except (PlaywrightTimeoutError, PlaywrightError) as e:
        error_msg = f"Playwright error: {type(e).__name__} - {e}"
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__} - {e}"
        raise RuntimeError(error_msg) from e


async def run_crawler(category_filter=None):
    urls = get_urls(category_filter)
    results = []
    fail_log_path = Path(__file__).parent / 'logs' / 'failures.log'
    fail_log_path.parent.mkdir(exist_ok=True)

    semaphore = asyncio.Semaphore(5)  # Limit concurrency

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        async def sem_crawl(url_info):
            async with semaphore:
                page = await context.new_page()
                try:
                    item = await crawl_page(page, url_info)
                    if item:
                        results.append(item)
                except RuntimeError as e:
                    # Log failure details
                    async with asyncio.Lock():
                        with open(fail_log_path, "a", encoding="utf-8") as f:
                            f.write(f"{url_info['url']}: {e}\n")
                    print(f"Error crawling {url_info['url']}: {e}")
                finally:
                    await page.close()

        tasks = [asyncio.create_task(sem_crawl(url_info)) for url_info in urls]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("\n⚠️ Crawler interrupted. Saving progress...")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            await browser.close()

    export_to_typesense_json(results, category_filter)


def export_to_typesense_json(results, category_filter):
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    safe_cat = category_filter.replace(' ', '_').lower() if category_filter else 'all'
    filename = output_dir / f"typesense_index_{safe_cat}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ Typesense index exported to: {filename}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Crawl green sites by category.')
    parser.add_argument('--category', type=str, help='Optional category filter')
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    crawler_task = loop.create_task(run_crawler(args.category))

    def shutdown(*signal_args):
        print("\n❌ KeyboardInterrupt received. Cancelling...")
        crawler_task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    try:
        loop.run_until_complete(crawler_task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()


if __name__ == '__main__':
    main()
