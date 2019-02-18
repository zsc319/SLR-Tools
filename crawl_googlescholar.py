# -*- coding: utf-8 -*-
import logging
import time
import json
import re
import random

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


def start_session(driver, query, n=0, patents=False, citations=False, start_year=2018, end_year=1950):
    patents = "as_sdt=1,5" if not patents else "as_sdt=0,5"
    citations = "as_vis=1" if not citations else "as_vis=0"
    year = start_year
    # as_vis=1 removes citations from the result set, =0 includes them
    # as_sdt=1,5 removes patents from the results set, =0,5 includes them

    # parse all entries for each year
    while year >= end_year:
        # start=x where is x is the item number of results to display,
        # can be 0 to start from beginning
        # q is the search query (%22 are the URL-encoded exact match quotes)
        url = "https://scholar.google.com/scholar?start={n}&q={query}&hl=en&{patents}&{citations}&as_ylo={year}&as_yhi={year}".format(
            n=n, query=query, patents=patents, citations=citations, year=year)
        logging.debug("getting url")
        driver.get(url)

        logging.debug("parsing entries")

        finished = False
        while not finished:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            datalist = []  # empty list
            if soup.find(id="gs_captcha_ccl"):
                logging.error("Captcha triggered. Waiting for user input")
                input("Captcha solved?")
                # get the new page_source after captcha has been solved
                soup = BeautifulSoup(driver.page_source, 'lxml')
            entries = soup.find_all(class_="gs_r gs_or gs_scl")
            for entry in entries:
                n += 1
                # create a dictionary of each result element
                datalist.append({"id": "{0}-{1}".format(year, n),
                                 "title": re.sub(r'\[.*\]', '', entry.find(class_="gs_rt").get_text()),
                                 "author": entry.find(class_="gs_a").get_text(),
                                 "year": year
                                 })
            # update json file every page
            try:
                with open('data.json', 'r') as inp:
                    data = json.load(inp)
                data.extend(datalist)
            except FileNotFoundError:
                data = datalist
            with open('data.json', 'w') as outfile:
                json.dump(data, outfile, ensure_ascii=False)

            logging.debug("loading next page")
            try:
                next_button = driver.find_element_by_xpath(
                    '//*[contains(@class, \'gs_ico_nav_next\')]')
                time.sleep(random.randrange(2, 5))
                next_button.click()
            except NoSuchElementException:
                n = 0
                year -= 1
                finished = True

    driver.quit()


if __name__ == '__main__':
    driver = webdriver.Firefox()
    # If you want exact matches only, include %22 before and after query
    # also if needed add + for white space

    # if you want to continue a crawl, set n to the last crawled id (in steps
    # of 10)

    # set patents, citations to True if you want to include either
    # set start_year to the year from which you want to start searching
    # (backwards), this won't yield all results with more than 1000 results
    # for any year
    start_session(driver, query="%22Virtual+Reality%22",
                  n=0, patents=False, citations=False, start_year=2018, end_year=1950)
