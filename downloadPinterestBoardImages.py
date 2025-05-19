# -*- coding: utf-8 -*-
import concurrent.futures as Futures
import logging
import re
import urllib.request
from argparse import ArgumentParser
from pathlib import Path
from time import sleep

import selenium
from rich.logging import RichHandler
from selenium.common.exceptions import \
    StaleElementReferenceException as StaleRefError
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

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

    logging.info(f"Name for board: {name}")

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

    def download_image(sources, save_path, i):
        # get best res of each url

        links = list(sources)

        while links:
            opt = links.pop()
            link = opt.split(" ")[0]
            try:
                urllib.request.urlretrieve(
                    link, save_path / (link.split("/")[-1]))

            except Exception as e:
                logging.info(f"Failed:     {opt} - {e}")
            else:
                logging.info(f"Downloaded: {opt}")
                return True

        logging.info(f"No downloads worked for {sources[-1].split(' ')[0]}")
        return sources

    def scroll(browser, amt=docscroll_window):
        browser.execute_script(f"window.scrollBy(0, {amt});")
        sleep(sleep_delay)
        return browser.execute_script("return document.body.scrollHeight")

    scroll(browser, 1)

    c = 0
    num_found = 0
    times_no_new_images = 0
    i = 0

    with Futures.ThreadPoolExecutor(max_workers=16) as ex:
        jobs = []

        while True:
            c += 1

            prev = len(image_links)

            # Grab only pin images (avoid user profile pictures) 
            img_elements = browser.find_elements(By.XPATH, xpath_img)

            for x in img_elements:
                i += 1
                try:
                    sources = x.get_attribute('srcset')
                except StaleRefError as e:
                    logging.info(f"Stale reference error: {e}")
                    continue

                sources = tuple([x.strip() for x in sources.split(",")])

                if sources not in image_links:
                    image_links.add(sources)
                    jobs.append(
                        ex.submit(download_image, sources, save_path, i))

            num_new = len(image_links) - prev
            num_found += num_new

            logging.info(f"Collected {num_new} new images")

            if num_new == 0:
                # if len(browser.find_elements(By.XPATH, xpath_end)) > 0:
                #     logging.info("Found end of board")
                #     break
                # else:
                times_no_new_images += 1

            if times_no_new_images >= 4:
                logging.info("Stopped finding new images")
                if prompt:
                    proceed = input("Continue anyway? y/n ")
                    if "y" in proceed.lower():
                        times_no_new_images = 0
                        continue
                break

            if c >= max_scolls:
                logging.info("Reached maximum number of scrolls")
                break

            logging.info(f"Scolled to {scroll(browser)}")

        logging.info("Checking failed downloads...")
        for x in Futures.as_completed(jobs):
            if x.result() is not True:
                logging.info(f"Retrying {x[-1]}")


    logging.info(f"Found {len(image_links)} images total")
    ex.shutdown(wait=True)


parser = ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False)
parser.add_argument("pinterest_URL")
parser.add_argument('-s', '--scroll_limit', type=int, default=100)
parser.add_argument('--delay', type=int, default=2)
parser.add_argument('-g', '--gui', action='store_true', default=False)
args = parser.parse_args()

logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
        datefmt=" ",
        handlers=[RichHandler(tracebacks_suppress=[selenium])])

opts = Options()
if not args.gui:
    opts.add_argument("-headless")
    # opts.add_argument("--width=3000")
    # opts.add_argument("--height=10000")

service = Service(GeckoDriverManager().install())

with selenium.webdriver.Firefox(service=service, options=opts) as browser:
    downloadPinterestImages(
        args.pinterest_URL, args.scroll_limit,
        args.delay, args.gui)
