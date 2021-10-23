#!/usr/bin/env python

import sys
import requests
import time
from selenium import webdriver
from bs4 import BeautifulSoup
import random
from datetime import datetime


def scrape_astro2020_announcements(url, driver):
    driver.get(url)
    sleep(10)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")  # for easier parsing
    stuff_of_interest = soup.find('p', {'class': 'card__title t3'})
    latest_date = stuff_of_interest.find(
        'span', {'class': 'announcement__date'}).get_text(strip=True)
    return latest_date


def send_slack_message(message, channel='announcement-watch', blocks=None):

    # Make sure it's readable only to you, i.e. chmod og-rwx slackbot_oauth_token
    slackbot_token_path = '/Users/grant/.slackbot/astro2020_announcment_oauth_token'

    # Never push the token to github!
    with open(slackbot_token_path, 'r') as tokenfile:
        # .splitlines()[0] is needed to strip the \n character from the token file
        slack_token = tokenfile.read().splitlines()[0]

    slack_channel = channel
    slack_icon_url = 'https://avatars.slack-edge.com/2021-10-20/2626830407027_f5a2fa7ea255f4ba8ab9_64.png'
    slack_user_name = 'Astro2020 Monitor'

    # Populate a JSON to push to the Slack API.
    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': slack_token,
        'channel': slack_channel,
        'text': message,
        'icon_url': slack_icon_url,
        'username': slack_user_name,
        'blocks': json.dumps(blocks) if blocks else None}).json()


def sleep(seconds):
    '''Count down the sleep period on the command line'''
    for i in range(0, seconds, 1):
        print(
            f'Chilling for {seconds - i} seconds.               ', end='\r', flush=True)
        time.sleep(1)


def main():
    '''Scrape the Astro2020 site for the latest announcement date. If it changes, send a slack message to me.'''
    # Instead of a channel, you can use your Slack user ID for a direct message
    slack_channel = 'announcement-watch'

    url = 'https://www.nationalacademies.org/our-work/decadal-survey-on-astronomy-and-astrophysics-2020-astro2020'

    iteration_counter = 0
    error_counter = 0

    # Website is dynamic, and so we need Selenium to scrape it.
    # initialize the driver - only need this once
    # I downloaded this here: https://sites.google.com/a/chromium.org/chromedriver/downloads
    driver = webdriver.Chrome('./chromedriver')

    while True:

        sleep_period = 300 + random.randint(0, 120) # this isn't a DDoS attack :)

        try:

            if iteration_counter == 0:
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) Performing initial scrape of Astro2020 site...')
                initial_announcement = scrape_astro2020_announcements(
                    url, driver)
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) Reference announcement date is: {initial_announcement}')
                send_slack_message(
                    f'Astro2020 Monitor Started. Reference announcement date is: {initial_announcement}', slack_channel)
                sleep(sleep_period)

            iteration_counter += 1
            latest_announcement = scrape_astro2020_announcements(url, driver)

            if initial_announcement != latest_announcement:
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) New announcement found! It is dated {latest_announcement}. CHECK THE SITE!')
                send_slack_message(
                    f'New Astro2020 announcement found! Latest date is {latest_announcement} (referenence date was {initial_announcement}). CHECK THE SITE!', slack_channel)
                iteration_counter = 0
                sleep(sleep_period)

            elif initial_announcement == latest_announcement:
                print(
                    f'({datetime.now().strftime("%m/%d/%Y %H:%M:%S")}) No change :( Checking again in {round(sleep_period/60,1)} minutes.')
                sleep(sleep_period)

        except Exception as e:
            print(f'ERROR! {e}')
            if error_counter == 0:
                send_slack_message(
                    f'Encountered an error and pressing on: {e}', channel=slack_channel)
                error_counter += 1
            continue


if __name__ == '__main__':
    main()
