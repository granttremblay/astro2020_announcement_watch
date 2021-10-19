#!/usr/bin/env python

import sys
import requests
import time
import hashlib
from selenium import webdriver
from bs4 import BeautifulSoup
import random
from datetime import datetime



def scrape_astro2020_announcements(url, driver):
    driver.get(url)
    time.sleep(10)  # Wait for the request to complete
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")  # for easier parsing
    announcements = soup.find('p', {'class': 'card__title t3'}).contents
    return announcements


def send_slack_message(message, channel='#general', blocks=None):

    # Make sure it's readable only to you, i.e. chmod og-rwx slackbot_oauth_token
    slackbot_token_path = '/Users/grant/.slackbot/slackbot_oauth_token'

    # Never push the token to github!
    with open(slackbot_token_path, 'r') as tokenfile:
        # .splitlines()[0] is needed to strip the \n character from the token file
        slack_token = tokenfile.read().splitlines()[0]

    slack_channel = channel
    slack_icon_url = 'https://avatars.slack-edge.com/2021-01-28/1695804235940_26ef808c676830611f43_512.png'
    slack_user_name = 'HRC CommBot'

    # Populate a JSON to push to the Slack API.
    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': slack_token,
        'channel': slack_channel,
        'text': message,
        'icon_url': slack_icon_url,
        'username': slack_user_name,
        'blocks': json.dumps(blocks) if blocks else None}).json()


def sleep(seconds):
    for i in range(seconds,0,-1):
        print(f'Checking again in {i} seconds', end='\r')
        sys.stdout.flush()
        time.sleep(1)


def main():

    # Instead of a channel, you can use your Slack user ID for a direct message
    slack_channel = 'UAPFCCG1Z'

    url = 'https://www.nationalacademies.org/our-work/decadal-survey-on-astronomy-and-astrophysics-2020-astro2020'

    iteration_counter = 0
    error_counter = 0

    # Website is dynamic, and so we need Selenium to scrape it.
    # initialize the driver - only need this once
    # I downloaded this here: https://sites.google.com/a/chromium.org/chromedriver/downloads
    driver = webdriver.Chrome('./chromedriver')

    while True:

        sleep_period = 300 + random.randint(0, 120)

        try:


            if iteration_counter == 0:
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) Performing initial scrape of Astro2020 site...')
                initial_announcement = scrape_astro2020_announcements(
                    url, driver)
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) Latest announcement is: \n\n {initial_announcement}')
                send_slack_message(
                    f'Astro2020 Monitor Started. Reference announcement is: {initial_announcement}', slack_channel)
                sleep(sleep_period)

            iteration_counter += 1
            latest_announcement = scrape_astro2020_announcements(url, driver)

            if initial_announcement != latest_announcement:
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) New announcement found! \n\n {latest_announcement}')
                send_slack_message(
                    f'New Astro2020 announcement found! {latest_announcement}', slack_channel)
                iteration_counter = 0
                sleep(sleep_period)

            elif initial_announcement == latest_announcement:
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) No change :( Checking again in 5 minutes.')
                for i in xrange(sleep_period,0,-1):
                    sys.stdout.write(str(i)+' ')
                    sys.stdout.flush()
                    time.sleep(1)
                sleep(sleep_period)

        except Exception as e:
            if error_counter == 0:
                send_slack_message(
                    f'Astro2020 code is crashing: {e}', channel=slack_channel)
                error_counter += 1
            print(e)
            sys.exit()


if __name__ == '__main__':
    main()
