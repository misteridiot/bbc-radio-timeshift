#!/usr/bin/env python

# scraper.py - scraping the BBC Radio 4 schedule to build a JSON schedule file used by the downloader and player modules

import requests as req
import extruct
import datetime as dt
import pytz
import json
import shared as sh
import logging
#import pprint

def extract_json_ld(url):
# Open BBC R4 schedule URL, extract JSON-LD, remove context to leave schedule list
# NB feels like extruct is overkill - more lightweight would be to scrape json-ld using BS4, figure how to convert to dict
#    pp = pprint.PrettyPrinter(indent=1)
    html_doc = req.get(url)
    json_ld = extruct.extract(html_doc.text, url, syntaxes=['json-ld'])
    json_ld = json_ld["json-ld"][0]["@graph"]
    logging.debug("JSON extracted")
#    pp.pprint(json_ld)
    return json_ld

def build_schedule_dict(json_ld):
# Create a schedule dictionary // for each chunk of HTML relating to an individual radio program, find key information & add to the schedule dictionary
# NB Datetimes kept in XSD format, will be converted to datetime() objects when JSON is read.
#    pp = pprint.PrettyPrinter(indent=1)

    schedule_dict = {}
    i=1

    for item in json_ld:
        pid = item['identifier']
        start_time = item['publication']['startDate']
        # Convert UTC start time into local UK time
        start_time_datetime = dt.datetime.strptime(start_time[:19], '%Y-%m-%dT%H:%M:%S')
        start_time_utc = pytz.utc.localize(start_time_datetime)
        start_time = start_time_utc.astimezone(pytz.timezone('Europe/London')).isoformat()
        end_time = item['publication']['endDate']
        # Convert UTC end time into local UK time
        end_time_datetime = dt.datetime.strptime(end_time[:19], '%Y-%m-%dT%H:%M:%S')
        end_time_utc = pytz.utc.localize(end_time_datetime)
        end_time = end_time_utc.astimezone(pytz.timezone('Europe/London')).isoformat()
        # If there's a series name, use that for name, otherwise use the episode name (looks like not all episodes are part of series)
        if "partOfSeries" in item:
            prog_name = item["partOfSeries"]['name']
        else:
            prog_name = item['name']
        schedule_dict[i] = {'PID': pid, 'NAME': prog_name, 'START_TIME': start_time, 'END_TIME': end_time}
        i=i+1
#    pp.pprint (schedule_dict)
    logging.debug("Schedule dict built")
    return schedule_dict

# Main -->
def scraper(json_dir):
    year, month, day = sh.set_date()
    url = 'https://www.bbc.co.uk/schedules/p00fzl7j/' + year + '/' + month + '/' + day
    logging.info("Attempting to scrape: %s", url)
    json_ld = extract_json_ld(url)
    logging.debug("JSON-LD extracted as dict")
    schedule_dict = build_schedule_dict(json_ld)
    logging.debug("Dict complete: %s records",str(len(schedule_dict)))
    sh.save_json(schedule_dict, year, month, day, json_dir)
    logging.debug("JSON file saved")
    return
