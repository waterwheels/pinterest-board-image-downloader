# -*- coding: utf-8 -*-
import urllib.request
import re
import concurrent.futures as Futures

from pathlib import Path
from time import sleep
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

# Unused
xpath_pinboard = "//div[contains(@id, 'boardfeed')]" # This div contains the actual pinterest board, not the "more like this" section
xpath_img_pincard = "//div[@class='PinCard__imageWrapper']/descendant::img" # Filters out only pin imgs, not user avatars
xpath_mobilefeed = "//div[@data-test-id='MobileFeed']" # This div contains the actual pinterest board, not the "more like this" section

# JS fragments for scrolling
docscroll_full = "document.body.scrollHeight"
docscroll_window = "window.innerHeight"

# xpaths to find pin images and the end of the board
xpath_img = "//div[contains(@id, 'boardfeed')]/descendant::div[@class='PinCard__imageWrapper']/descendant::img"
xpath_seeMore = "xpath for see more button to click?"
xpath_end = "//h2[text()='More like this']"

def downloadPinterestImages(link, max_scolls, sleep_delay, prompt=False):
    # Get name for folder
    name = link.split("/")
    name = name[-1] if name[-1] else name[-2]

    print(f"Name for board: {name}")

    # Load page
    browser.get(link)
    sleep(1)

    if prompt:
        proceed = input("Ready to start? y/n ")
        if "y" not in proceed:
            exit(0)

    save_path = Path(f"Images/{name}")
    save_path.mkdir(parents=True, exist_ok=True)

    image_links = set()

    def download_image(image_url, save_path, i):
        # get full res of each url
        image_data = [image_url, re.sub('.com/.*?/','.com/originals/',image_url,flags=re.DOTALL)]

        name = image_data[0].rsplit('/', 1)[-1]
        if "--" in name:
            temp = name.split("--", 1)
            name = f"{temp[-1].rsplit('.jpg', 1)[0]}-{temp[0]}.jpg"

        print(f"{i:<4}: Downloading " + name)
        try:
            urllib.request.urlretrieve(image_data[1], save_path / name)
        except Exception as e:
            print(f"{i:<4}:        Broken link to original, trying resampled image link\n{e}")
            try:
                urllib.request.urlretrieve(image_data[0], save_path / f"thumb-{name}")
            except:
                print(f"{i:<4}:        both links broken. Sorry :(")

    def scroll(browser, amt=docscroll_window):
        browser.execute_script(f"window.scrollBy(0, {amt});")
        sleep(sleep_delay)
        return browser.execute_script("return document.body.scrollHeight")

    scroll(browser, 1)

    c = 0
    found_end = False
    num_found = 0
    times_no_new_images = 0

    while(True):
        c += 1
        # Grab only pin images (avoid user profile pictures) 
        img_elements = browser.find_elements(By.XPATH, xpath_img)

        for x in img_elements:
            #print(x)
            source = x.get_attribute('src')
            image_links.add(source)

        num_new = len(image_links) - num_found
        num_found += num_new

        print(f"Collected {num_new} new images")

        if num_new == 0:
            if len(browser.find_elements(By.XPATH, xpath_end)) > 0:
                print("Found end of board")
                break
            else:
                times_no_new_images += 1

        if times_no_new_images >= 3:
            print("Stopped finding new images")
            break

        if c >= max_scolls:
            print("Reached maximum number of scrolls")
            break

        print(f"Scolled to {scroll(browser)}")

    print(f"Found {len(image_links)} images total")

    # Download each image
    with Futures.ThreadPoolExecutor(max_workers=16) as ex:
        for i, this_url in enumerate(image_links):
            ex.submit(download_image, this_url, save_path, i)

    ex.shutdown(wait=True)


        
        
parser = ArgumentParser()
parser.add_argument("pinterest_URL")
parser.add_argument('-s', '--scroll_limit', type=int, default=10)
parser.add_argument('-d', '--delay', type=int, default=2)
parser.add_argument('-g', '--gui', action='store_true', default=False)
args = parser.parse_args()

opts = Options()
if not args.gui:
    opts.add_argument("-headless")
    opts.add_argument("--width=3000")
    opts.add_argument("--height=10000")

service = Service('geckodriver.exe')

with webdriver.Firefox(service=service, options=opts) as browser:
    downloadPinterestImages(args.pinterest_URL, args.scroll_limit,
        args.delay, args.gui)
