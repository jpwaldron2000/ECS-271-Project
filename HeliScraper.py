import os
import time
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import requests

##Currently saves urls and meta data of the images into a csv in the same folder as the file
##will update to save image files once the filter is better

#CONFIG
KEYWORDS = ['helicopter', 'heli', 'drone', 'drone aircraft',  'uav', 'UAV', 'uas', 'UAS', 'rotorcraft', 'quadcopter', 'unmanned aerial']
OUTPUT_CSV = 'helicopter_drone_urls.csv'
# Set to True to download images to a folder, False to just save URLs to CSV
DOWNLOAD_IMAGES = False
IMAGE_DOWNLOAD_FOLDER = 'downloaded_images'
# How many gallery pages to scrape per site (increase for larger datasets)
MAX_PAGES = 5
# Seconds to wait between requests (be polite to servers)
REQUEST_DELAY = 2


#DRIVER SETUP

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    # options.add_argument("--headless=new")  # uncomment after confirming it works for headless scraping
    driver = uc.Chrome(options=options, version_main=147)
    return driver


#LOGIN PLACEHOLDERS
##hasn't been necessary yet but for scraping a lot of photos at once it may speed up the process

def login_airliners(driver):
    """
    Log in to airliners.net.
    Uncomment and fill in credentials when you have an account.
    """
    pass
    # AIRLINERS_USER = "your_username"
    # AIRLINERS_PASS = "your_password"
    #
    # driver.get("https://www.airliners.net/login")
    # time.sleep(2)
    # driver.find_element(By.ID, "username").send_keys(AIRLINERS_USER)
    # driver.find_element(By.ID, "password").send_keys(AIRLINERS_PASS)
    # driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    # time.sleep(3)
    # print("[INFO] Logged into airliners.net")


def login_jetphotos(driver):
    """
    Log in to jetphotos.com.
    Uncomment and fill in credentials when you have an account.
    """
    pass
    # JETPHOTOS_USER = "your_username"
    # JETPHOTOS_PASS = "your_password"
    #
    # driver.get("https://www.jetphotos.com/login")
    # time.sleep(2)
    # driver.find_element(By.NAME, "username").send_keys(JETPHOTOS_USER)
    # driver.find_element(By.NAME, "password").send_keys(JETPHOTOS_PASS)
    # driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    # time.sleep(3)
    # print("[INFO] Logged into jetphotos.com")


#KEYWORD FILTER
##note: doesn't work that well yet for drones, the drone pages include a lot of planes
##so i need to work on the filtering 

## currently unused filter was removed because image filenames/alt text don't contain
## keyword info. filtering now relies on the site's own search results.
## drone results still pull in some planes so it needs improvement

def matches_keywords(text):
    ##Return True if any keyword appears in the given text (case-insensitive).
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


#COOKIE POPUP

def dismiss_cookie_popup(driver):
    try:
        accept_btn = driver.find_element(By.ID, "didomi-notice-agree-button")
        accept_btn.click()
        time.sleep(1)
        print("[INFO] Dismissed cookie popup")
    except Exception:
        pass  # no popup, move on

def download_image(url, folder, filename):
    try:
        os.makedirs(folder, exist_ok=True)
        if url.startswith('//'):
            url = 'https:' + url
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        if response.status_code == 200:
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
    return False


#AIRLINERS.NET SCRAPER

def scrape_airliners(driver, max_pages=MAX_PAGES):
    results = []
    search_terms = ['helicopter', 'drone']

    for term in search_terms:
        print(f"[INFO] airliners.net — searching: '{term}'")

        for page in range(1, max_pages + 1):
            driver.set_page_load_timeout(10)
            url = f"https://www.airliners.net/search?keywords={term}&page={page}"
            try:
                driver.get(url)
            except Exception:
                pass
            time.sleep(3)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
                )
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                images = soup.find_all('img', class_='lazy-load')
                page_count = 0

                for img in images:
                    src = img.get('src') or img.get('data-src') or ''
                    alt = img.get('alt') or ''
                    title = img.get('title') or ''
                    parent_text = img.parent.get_text(separator=' ', strip=True) if img.parent else ''

                    if not src:
                        continue

                    photo_link = ''
                    anchor = img.find_parent('a')
                    if anchor and anchor.get('href'):
                        href = anchor['href']
                        photo_link = href if href.startswith('http') else 'https://www.airliners.net' + href

                    results.append({
                        'source': 'airliners.net',
                        'search_term': term,
                        'image_url': src,
                        'photo_page_url': photo_link,
                        'alt_text': alt,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    page_count += 1

                print(f"[INFO] airliners.net page {page} — found {page_count} matching images")

                if page_count == 0:
                    print(f"[INFO] airliners.net — no more results for '{term}', stopping early")
                    break

            except Exception as e:
                print(f"[ERROR] airliners.net page {page} for '{term}': {e}")
                break

    return results


#JETPHOTOS.COM SCRAPER
#Jet photos seems to have a more specific search system so we may have to go in and put in individual drone model names to scrape images of them

def scrape_jetphotos(driver, max_pages=MAX_PAGES):
    results = []
    search_terms = ['helicopter', 'drone','quadcopter']

    for term in search_terms:
        print(f"[INFO] jetphotos.com — searching: '{term}'")

        for page in range(1, max_pages + 1):
            driver.set_page_load_timeout(10)
            url = f"https://www.jetphotos.com/showphotos.php?keywords={term}&keywords-type=all&keywords-contain=3&search-type=Advanced&page={page}"
            try:
                driver.get(url)
            except Exception:
                pass
            time.sleep(5)

            
            dismiss_cookie_popup(driver)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
                )
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                images = soup.find_all('img', class_='result__photo')
                page_count = 0

                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
                    alt = img.get('alt') or ''
                    title = img.get('title') or ''
                    parent_text = img.parent.get_text(separator=' ', strip=True) if img.parent else ''

                    # For drone search terms, filter by alt text
                    if term in ['UAV', 'quadcopter', 'multirotor', 'drone aircraft', 'unmanned aerial']:
                        drone_terms = ['uav', 'drone', 'quadcopter', 'multirotor', 'dji', 'phantom', 'mavic', 'inspire', 'autel', 'parrot', 'unmanned']
                        if not any(t in alt.lower() for t in drone_terms):
                            continue

                    if not src:
                        continue

                    photo_link = ''
                    anchor = img.find_parent('a')
                    if anchor and anchor.get('href'):
                        href = anchor['href']
                        photo_link = href if href.startswith('http') else 'https://www.jetphotos.com' + href

                    results.append({
                        'source': 'jetphotos.com',
                        'search_term': term,
                        'image_url': src,
                        'photo_page_url': photo_link,
                        'alt_text': alt,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    page_count += 1

                print(f"[INFO] jetphotos.com page {page} — found {page_count} matching images")

                if page_count == 0:
                    print(f"[INFO] jetphotos.com — no more results for '{term}', stopping early")
                    break

            except Exception as e:
                print(f"[ERROR] jetphotos.com page {page} for '{term}': {e}")
                break

    return results


#CSV EXPORT

def save_to_csv(results, output_file=OUTPUT_CSV):
    ##Save scraped image URLs and metadata to a CSV file.
    if not results:
        print("[WARNING] No results to save.")
        return

    fieldnames = ['source', 'search_term', 'image_url', 'photo_page_url', 'alt_text', 'scraped_at']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"[INFO] Saved {len(results)} URLs to '{output_file}'")


#DEDUPLICATION

def deduplicate(results):
    ##Remove duplicate image URLs, keeping first occurrence.
    seen = set()
    unique = []
    for r in results:
        if r['image_url'] not in seen:
            seen.add(r['image_url'])
            unique.append(r)
    removed = len(results) - len(unique)
    if removed:
        print(f"[INFO] Removed {removed} duplicate URLs")
    return unique


#MAIN

def main():
    print("[INFO] Starting scraper...")
    driver = create_driver()

    try:
        # Login (currently no login, uncomment credential blocks above to enable)
        login_airliners(driver)
        login_jetphotos(driver)

        all_results = []

        # Scrape both sites
        airliners_results = scrape_airliners(driver, max_pages=MAX_PAGES)
        all_results.extend(airliners_results)
        print(f"[INFO] airliners.net total: {len(airliners_results)} images")

        jetphotos_results = scrape_jetphotos(driver, max_pages=MAX_PAGES)
        all_results.extend(jetphotos_results)
        print(f"[INFO] jetphotos.com total: {len(jetphotos_results)} images")

        # Deduplicate and save
        all_results = deduplicate(all_results)
        if DOWNLOAD_IMAGES:
            print(f"[INFO] Downloading {len(all_results)} images...")
            success = 0
            for i, r in enumerate(all_results):
                ext = r['image_url'].split('.')[-1].split('?')[0] or 'jpg'
                filename = f"{r['source']}_{r['search_term']}_{i:04d}.{ext}"
                folder = os.path.join(IMAGE_DOWNLOAD_FOLDER, r['search_term'])
                if download_image(r['image_url'], folder, filename):
                    success += 1
            print(f"[INFO] Downloaded {success}/{len(all_results)} images to '{IMAGE_DOWNLOAD_FOLDER}/'")
        else:
            save_to_csv(all_results)

        print(f"[INFO] Done. {len(all_results)} unique images processed.")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        raise

    finally:
        driver.quit()


if __name__ == '__main__':
    main()