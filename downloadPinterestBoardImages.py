# -*- coding: utf-8 -*-
import urllib.request
import re

from time import sleep
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

# Unused
xpath_pinboard = "//div[contains(@id, 'boardfeed')]" # This div contains the actual pinterest board, not the "more like this" section
xpath_img_pincard = "//div[@class='PinCard__imageWrapper']/descendant::img" # Filters out only pin imgs, not user avatars
xpath_mobilefeed = "//div[@data-test-id='MobileFeed']" # This div contains the actual pinterest board, not the "more like this" section

# JS fragments for scrolling
docscroll_full = "document.body.scrollHeight"
docscroll_window = "window.innerHeight"

# xpaths to find pin images and the end of the board
xpath_img = "//div[contains(@id, 'boardfeed')]/descendant::div[@data-test-id='pin']/descendant::img"
xpath_end = "//h2[text()='More like this']"

def downloadPinterestImages(link, max_scolls, sleep_delay, headless):
    opts = Options()
    opts.headless = headless
    browser = webdriver.Firefox(executable_path=r'geckodriver.exe', options=opts)

    # Load page
    browser.get(link)
    sleep(3)

    image_links = set()

    def download_image(image_url):
        # get full res of each url
        image_data = [image_url, re.sub('.com/.*?/','.com/originals/',image_url,flags=re.DOTALL)]

        name = image_data[0].rsplit('/', 1)[-1]
        print("Downloading " + name)
        try:
            print("    URL "+image_data[1])
            urllib.request.urlretrieve(image_data[1], "images/"+name)
        except:
            print("        Broken link to original, trying resampled image link")
            try:
                print("        URL "+image_data[1])
                urllib.request.urlretrieve(image_data[0], "images/thumb-"+name)
            except:
                print("       both links broken. Sorry :(")

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

        print(f"Scolled to {scroll(browser)}")

    print(f"Found {len(image_links)} images total")

    # Download each image
    for this_url in image_links:
        download_image(this_url)

    browser.quit()

def downloadPinterestImagesOLD(link, max_scolls, sleep_delay):
    opts = Options()
    # opts.headless = True
    browser = webdriver.Firefox(executable_path=r'geckodriver.exe', options=opts)

    # Load page
    browser.get(link)

    # Scroll the page until we find the "more like this" heading, can't scroll more, or exceed max number of scrolls
    initial_height = browser.execute_script("return document.body.scrollHeight")

    c = 0
    end = False
    while(True):
        c += 1
        print(f"Last scroll height {initial_height}")
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(sleep_delay)
        new_height = browser.execute_script("return document.body.scrollHeight")

        if new_height == initial_height:
            print("Found end of page, no more page to scroll")
            break

        if c > max_scolls:
            print(f"reached maximum number of scrolls: {max_scolls}")
            break

        if not end and len(browser.find_elements(By.XPATH, xpath_end)) > 0:
            print("Found end of board")
            max_scolls = c + 1
            end = True

        initial_height = new_height
    
    sleep(1)

    # Get the div containing the pins
    block = browser.find_element(By.XPATH, xpath_pinboard)

    # Grab only pin images (avoid users' profile pictures) 
    img_elements = block.find_elements(By.XPATH, xpath_img)

    print(f"Found {len(img_elements)} elements matching {xpath_img}")




    images = []
    for this_image in img_elements:
        smol = this_image.get_attribute('src')
        original = re.sub('.com/.*?/','.com/originals/',smol,flags=re.DOTALL)
        images.append([smol,original])
    
    for img in images:
        name = img[0].rsplit('/', 1)[-1]
        print("Downloading " + name)
        try:
            print("    URL "+img[1])
            #urllib.request.urlretrieve(img[1], "images/"+name)
        except:
            print("        Broken link to original, trying resampled image link")
            try:
                print("        URL "+img[1])
                #urllib.request.urlretrieve(img[0], "images/thumb-"+name)
            except:
                print("       both links broken. Sorry :(")

    browser.quit()
        
        
parser = ArgumentParser()
parser.add_argument("pinterest_URL")
parser.add_argument('-s', '--scroll_limit', type=int, default=10)
parser.add_argument('-d', '--delay', type=int, default=3)
parser.add_argument('-n', '--headless', action='store_true', default=False)
args = parser.parse_args()

downloadPinterestImages(args.pinterest_URL, args.scroll_limit, args.delay, args.headless)
