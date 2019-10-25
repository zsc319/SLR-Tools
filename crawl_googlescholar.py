# -*- coding: utf-8 -*-
import logging
import time
import json
import csv
import re
import os
import random
import urllib.parse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def check_for_captcha():
    soup = BeautifulSoup(driver.page_source, 'lxml')
    if soup.find(id="gs_captcha_ccl"):
        logging.warning(
            "Captcha triggered. Please solve it until you see a result page.")
        input("Press Return once you have solved the captcha: ")
         # get the new page_source after captcha has been solved
        return BeautifulSoup(driver.page_source, 'lxml')
    else:
        return soup


def start_session(driver, query, n, patents, citations, start_year, end_year):
    patents = "as_sdt=1,5" if not patents else "as_sdt=0,5"
    citations = "as_vis=1" if not citations else "as_vis=0"
    year = start_year
    logging.info("start crawling for query {query} {patents} patents {citations} citations from {start_year} to {end_year}".format(
        query=query, patents="including" if patents else "excluding", citations="including" if citations else "excluding", start_year=start_year, end_year=end_year))
    # as_vis=1 removes citations from the result set, =0 includes them
    # as_sdt=1,5 removes patents from the results set, =0,5 includes them

    # parse all entries for each year
    while year >= end_year:
        time.sleep(random.randrange(5, 15))
        logging.info("crawling year {year}".format(year=year))
        # start=x where is x is the item number of results to display,
        # can be 0 to start from beginning
        # q is the search query (%22 are the URL-encoded exact match quotes)
        url = "https://scholar.google.com/scholar?start={n}&q={query}&hl=en&{patents}&{citations}&as_ylo={year}&as_yhi={year}".format(
            n=n, query=urllib.parse.quote(query), patents=patents, citations=citations, year=year)
        logging.debug("getting url")
        driver.get(url)
        soup = check_for_captcha()

        result_count = int(driver.find_element_by_xpath(
            '//*[@id="gs_ab_md"]/div').text.replace(".", "").replace("About ", "").split(" ")[0])
        if result_count > 999:
            logging.warning("With {count} results you are missing results (Google Scholar has a limit of 1000 results per query). Try changing your query".format(
                count=result_count))
        else:
            logging.info("Got {count} results for query and year.".format(
                count=result_count))

        logging.debug("parsing entries")

        finished = False
        while not finished:
            datalist = []  # empty list
            soup = check_for_captcha()

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
                with open('data_incomplete.json', 'r') as inp:
                    data = json.load(inp)
                data.extend(datalist)
            except FileNotFoundError:
                data = datalist
            with open('data_incomplete.json', 'w') as outfile:
                json.dump(data, outfile, ensure_ascii=False)

            logging.debug("loading next page")
            try:
                next_button = driver.find_element_by_xpath(
                    '//*[contains(@class, \'gs_ico_nav_next\')]')
                time.sleep(random.randrange(5, 15))
                next_button.click()
            except NoSuchElementException:
                n = 0
                year -= 1
                finished = True
    os.rename("data_incomplete.json","data_complete.json")
    driver.quit()


if __name__ == '__main__':
    query = input('Enter query exactly as you would on the website: ')
    # if you want to continue a crawl, set n to the last crawled id (in steps
    # of 10)
    n = 0
    patents = input('Do you want to include patents? y/n? ') =='y'
    citations = input('Do you want to include citations? y/n? ') =='y'
    # set start_year to the year from which you want to start searching
    # (backwards), this won't yield all results with more than 1000 results
    # for any year
    start_year = int(input("Enter start year (newest year): "))
    end_year = int(input("Enter end year (oldest year): "))

    # init webdriver late so we don't move focus from terminal
    driver = webdriver.Firefox()

    start_session(driver, query=query,
                  n=0, patents=patents, citations=citations, start_year=start_year, end_year=end_year)
