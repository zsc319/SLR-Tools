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
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
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
        # time.sleep(random.randrange(5, 15))
        logging.info("crawling year {year}".format(year=year))
        url = "https://scholar.google.com/scholar?start={n}&q={query}&hl=en&{patents}&{citations}&as_ylo={year}&as_yhi={year}".format(
            n=n, query=urllib.parse.quote(query), patents=patents, citations=citations, year=year)

        # navigate to GS
        logging.debug("getting url")
        driver.get("https://scholar.google.com")
        time.sleep(random.randrange(2,3))

        soup = check_for_captcha()
        for i in range(5):
            driver.find_element_by_tag_name("html").send_keys(Keys.CONTROL,Keys.SUBTRACT)
            time.sleep(0.2)
        # enter query
        search_input = driver.find_element_by_xpath('//*[@id="gs_hdr_tsi"]')
        search_input.send_keys(query)
        time.sleep(random.randrange(2,3))
        search_input.send_keys(Keys.RETURN)
        time.sleep(random.randrange(2,3))
        soup = check_for_captcha()

        # in-/exclude patents or citations
        patents_button = driver.find_element_by_xpath('/html/body/div/div[11]/div[1]/div/ul[2]/li[1]')
        citations_button = driver.find_element_by_xpath('/html/body/div/div[11]/div[1]/div/ul[2]/li[2]')
        logging.info(patents_button)
        if not patents:
            patents_button.click()
        if not citations:
            citations_button.click()
        time.sleep(random.randrange(2,3))
        soup = check_for_captcha()

        result_count = int(driver.find_element_by_xpath(
            '/html/body/div/div[10]/div[3]/div').text.replace(".", "").replace("About ", "").split(" ")[0])
        if result_count > 999:
            logging.warning("With {count} results, you are missing results (Google Scholar has a limit of 1000 results per query). Try changing your query to something more specific.".format(
                count=result_count))
        else:
            logging.info("Got {count} results for query and year.".format(
                count=result_count))

        logging.debug("parsing entries")

        finished = False
        while not finished:
            # parse data as bibfiles
            time.sleep(random.randrange(3, 6))
            datalist = []  # empty list
            biblist = []

            # parse data from bib-objects
            logging.info(len(list(driver.find_elements_by_class_name("gs_or_cit"))))
            for i in range(10):
                c = 0
                try:
                    entry = list(driver.find_elements_by_class_name("gs_or_cit"))[i]
                    entry.click()
                except ElementClickInterceptedException:
                    c+=1
                    entry = list(driver.find_elements_by_class_name("gs_or_cit"))[i]
                    entry.click()
                    if c == 10:
                        raise

                time.sleep(random.randrange(2, 3))
                soup = check_for_captcha()
                driver.find_element_by_xpath("/html/body/div/div[4]/div/div[2]/div/div[2]/a[1]").click()
                time.sleep(random.randrange(2, 3))
                soup = check_for_captcha()
                bib_elem = BeautifulSoup(driver.page_source, 'lxml').get_text()
                driver.back()
                time.sleep(random.randrange(2, 3))
                driver.find_element_by_id("gs_cit-x").click()
                time.sleep(random.randrange(2, 3))
                soup = check_for_captcha()
                biblist.append(bib_elem)
                time.sleep(random.randrange(0, 1))


            # parse data from GS result pages
            soup = check_for_captcha()
            entries = soup.find_all(class_="gs_r gs_or gs_scl")
            for entry in entries:
                cite_count = int(list(entry.find(class_="gs_or_cit").next_siblings)[1].get_text().replace('Cited by ',''))
                n += 1
                # create a dictionary of each result element
                datalist.append({"id": "{0}-{1}".format(year, n),
                                 "title": re.sub(r'\[.*\]', '', entry.find(class_="gs_rt").get_text()),
                                 "author": entry.find(class_="gs_a").get_text(),
                                 "year": year,
                                 "abstract": entry.find(class_="gs_rs").get_text(),
                                 "citation_count": cite_count
                                 })
                with open('data_incomplete.bibtex', 'a') as inp:
                    inp.write("\n".join(biblist))

        # update json file every year
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
    logging.debug("Finished crawling for given query and year(s). Renaming data file.")
    os.rename("data_incomplete.json","data_complete.json")
    driver.quit()


if __name__ == '__main__':
    debug = True
    if debug:
        query = 'interface AND user AND search AND system AND "Information Retrieval" AND "Virtual Reality"'
        patents = False
        citations = True
        n=0
        start_year = 2019
        end_year = 2019
    else:
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
    driver.implicitly_wait(10) # seconds

    start_session(driver, query=query,
                  n=0, patents=patents, citations=citations, start_year=start_year, end_year=end_year)
