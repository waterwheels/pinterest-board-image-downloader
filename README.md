# pinterest-board-image-downloader
Originally a fork of panbak's [pinterest downloader](https://github.com/panbak/pinterest-board-image-downloader), now almost entirely rewritten. 


The script accepts a pinterest board URL as an argument, and the following optional args:

    -s  --scroll_limit  sets an upper limit on the number of times the script will scroll to load more pins (default 10)
    -d  --delay         how many seconds to wait after each scroll for the page JS to load new pins (default 2, increase if you have a slow connection)
    -g  --gui           don't hide the gui
    -h                  show this information
    
The script searches the webpage DOM with XPATHs that locate pins that are actually part of the pinboard (rather than the "more like this" section, or other page images) and adds their thumbnail URLs to a set. Then it scrolls the page one window-height to load more pins and repeats the process. In my testing, pinterest currently removes divs for pins that are scrolled off the page, so this step-by-step process is necessary.

When the script finds the end of the board, it scrolls one more time to make sure, then moves on to downloading. It will also move on if it scrolls too many times in a row without finding new pins, or reaches the limit of the maximum number of scrolls. When downloading the pins, it constructs the URL to the hi-res original from the thumbnail URL and tries to download that, but will download the thumb if the hi-res link doesn't work.

### Dependencies: 
  1.  selenium `pip install selenium`
  
Selenium uses firefox to work so it needs firefox installed and [geckodriver](https://github.com/mozilla/geckodriver/releases). Download and extract the geckodriver executable to the same folder as downloadPinterestBoardImages.py.
Also make a folder named 'images' to save the downloaded pinterest pins.

If you want to use another browser such as Chrome, check the [selenium docs](https://selenium-python.readthedocs.io/installation.html).

### Issues:
If Pinterest changes the page structure more than a little, the XPATH the script uses to find pin images could stop working. In this case, inspecting the board page might allow you to work out a new XPATH that will find only pin images. This can be a little fiddly since Pinterest obfuscates their code with nonsense class names, so I have tried to use only human-readable attributes of the page structure to locate pins:

    //div[contains(@id, 'boardfeed')]                   <-- finds the board main div (not the "more like this" block)
    /descendant::div[@class='PinCard__imageWrapper']    <-- finds part of a pin deep enough in to avoid grabbing user avatars
    /descendant::img"                                   <-- finds the actual img object

### Plans:
Add loop structure so you can give it a list of Pinterest board URLs and it will do them 1-by-1 (into folders named after the board?)

Get pin alt-text, and include in file name or metadata. Could do this if there's a way to make a hashable object (for the set) out of pin thumB URL and other data
