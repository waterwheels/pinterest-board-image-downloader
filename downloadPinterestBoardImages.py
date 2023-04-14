# -*- coding: utf-8 -*-
import urllib.request
import re
import time

from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options



#xpath_pinboard = "//div[@data-test-id='MobileFeed']" # This div contains the actual pinterest board, not the "more like this" section
xpath_pinboard = "//div[contains(@id, 'boardfeed')]" # This div contains the actual pinterest board, not the "more like this" section
xpath_img = "//div[@class='PinCard__imageWrapper']/descendant::img" # Filters out only pin imgs, not user avatars
xpath_end = "//h2[text()='More like this']" # matches the end of the pin-board


def downloadPinterestImages(link, max_scolls, sleep_delay):
    opts = Options()
    # opts.headless = True
    browser = webdriver.Firefox(executable_path=r'geckodriver.exe', options=opts)

    # Load page
    browser.get(link)

    # Scroll the page until we find the "more like this" heading, can't scroll more, or exceed max number of scrolls
    initial_height = browser.execute_script("return document.body.scrollHeight")

    c = 0
    while(True):
        c += 1
        print(f"Last scroll height {initial_height}")
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_delay)
        new_height = browser.execute_script("return document.body.scrollHeight")

        if new_height == initial_height:
            print("Found end of page, no more page to scroll")
            break

        if c > max_scolls:
            print(f"reached maximum number of scrolls: {max_scolls}")
            break

        if len(browser.find_elements(By.XPATH, xpath_end)) > 0:
            print("Found end of board")
            break

        initial_height = new_height
    
    time.sleep(10)

    # Get the div containing the pins
    block = browser.find_element(By.XPATH, xpath_pinboard)

    # Grab only pin images (avoid users' profile pictures) 
    img_elements = block.find_elements(By.XPATH, xpath_img)
    test = block.find_elements(By.XPATH, "//img")

    print(f"Found {len(img_elements)} elements matching {xpath_img}")
    print(f"Found {len(img_elements)} image elements")

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

    #browser.quit()
        
        
parser = ArgumentParser()
parser.add_argument("pinterest_URL")
parser.add_argument('-s', '--scroll_limit', type=int, default=10)
parser.add_argument('-d', '--delay', type=int, default=3)
args = parser.parse_args()

downloadPinterestImages(args.pinterest_URL, args.scroll_limit, args.delay)
