#!/usr/bin/env python
import signal
import sys
import argparse
import logging
# for ipython
reload(logging)
import os
import requests
import time
import pytz
from dateutil import parser
from datetime import datetime, timedelta
import send_messages as sm
from pymongo import MongoClient
import traceback

utc = pytz.UTC

# Script config
DB_NAME = 'udacity_reviews'
BASE_URL = 'https://review-api.udacity.com/api/v1'
CERTS_URL = '{}/me/certifications.json'.format(BASE_URL)
ME_URL = '{}/me'.format(BASE_URL)
ME_REQUEST_URL = '{}/me/submission_requests.json'.format(BASE_URL)
CREATE_REQUEST_URL = '{}/submission_requests.json'.format(BASE_URL)
DELETE_URL_TMPL = '{}/submission_requests/{}.json'
GET_REQUEST_URL_TMPL = '{}/submission_requests/{}.json'
PUT_REQUEST_URL_TMPL = '{}/submission_requests/{}.json'
REFRESH_URL_TMPL = '{}/submission_requests/{}/refresh.json'
ASSIGNED_COUNT_URL = '{}/me/submissions/assigned_count.json'.format(BASE_URL)
ASSIGNED_URL = '{}/me/submissions/assigned.json'.format(BASE_URL)
# fill with submission_request_id from ME_REQUEST_URL
WAIT_URL = '{}/submission_requests/{}/waits.json'


REVIEW_URL = 'https://review.udacity.com/#!/submissions/{sid}'
REQUESTS_PER_SECOND = 1 # Max frequency allowed by Udacity

# projects to skip and not auto assign
exclude_list = [232] # movie data...not enough time for this one right now
proj_id_dict = {} # dict for going from project id number to text

logging.basicConfig(format='|%(asctime)s| %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

headers = None

def signal_handler(signal, frame):
    if headers:
        logger.info('Cleaning up active request')
        me_resp = requests.get(ME_REQUEST_URL, headers=headers)
        if me_resp.status_code == 200 and len(me_resp.json()) > 0:
            logger.info(DELETE_URL_TMPL.format(BASE_URL, me_resp.json()[0]['id']))
            del_resp = requests.delete(DELETE_URL_TMPL.format(BASE_URL, me_resp.json()[0]['id']),
                                       headers=headers)
            logger.info(del_resp)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def alert_for_assignment(current_request, headers):
    if current_request and current_request['status'] == 'fulfilled':
        logger.info("")
        logger.info("=================================================")
        logger.info("You have been assigned to grade a new submission!")
        logger.info("View it here: " + REVIEW_URL.format(sid=current_request['submission_id']))
        logger.info("=================================================")
        logger.info("Continuing to poll...")
        # sends text and email
        proj_name = proj_id_dict[current_request['submission_request_projects']['id']]
        print 'project name: ' + proj_name
        for i in range(10):
            print '---'
        sm.send_messages(link=REVIEW_URL.format(sid=current_request['submission_id']),
                        project=proj_name)
        return None
    return current_request

def wait_for_assign_eligible():
    while True:
        assigned_resp = requests.get(ASSIGNED_COUNT_URL, headers=headers)
        get_wait_stats()
        current_request = alert_for_assignment(current_request, headers)
        if assigned_resp.status_code == 404 or assigned_resp.json()['assigned_count'] < 2:
            break
        else:
            logger.info('Waiting for assigned submissions < 2')
        # Wait 10 seconds before checking to see if < 2 open submissions
        # that is, waiting until a create submission request will be permitted
        time.sleep(30.0)

def refresh_request(current_request):
    logger.info('Refreshing existing request')
    refresh_resp = requests.put(REFRESH_URL_TMPL.format(BASE_URL, current_request['id']),
                                headers=headers)
    refresh_resp.raise_for_status()
    if refresh_resp.status_code == 404:
        logger.info('No active request was found/refreshed.  Loop and either wait for < 2 to be assigned or immediately create')
        return None
    else:
        logger.info('Request refreshed, id is ' + str(refresh_resp.json()['id']))
        return refresh_resp.json()

def fetch_certified_pairs():
    logger.info("Requesting certifications...")
    me_resp = requests.get(ME_URL, headers=headers)
    me_resp.raise_for_status()
    languages = me_resp.json()['application']['languages'] or ['en-us']

    certs_resp = requests.get(CERTS_URL, headers=headers)
    certs_resp.raise_for_status()

    certs = certs_resp.json()
    for c in certs:
        if c['status'] == 'certified':
            print 'project:', c['project']['name'], ', id:', c['project']['id']
            the_id = c['project']['id']
            if the_id not in exclude_list:
                proj_id_dict[the_id] = c['project']['name']

    project_ids = [cert['project']['id'] for cert in certs if (cert['status'] == 'certified' and cert['project']['id'] not in exclude_list)]

    logger.info("Found certifications for project IDs: %s in languages %s",
                str(project_ids), str(languages))
    logger.info("Polling for new submissions...")

    return [{'project_id': project_id, 'language': lang} for project_id in project_ids for lang in languages]

def request_reviews():
    project_language_pairs = fetch_certified_pairs()
    logger.info("Will poll for projects/languages %s", str(project_language_pairs))

    me_req_resp = requests.get(ME_REQUEST_URL, headers=headers)
    current_request = me_req_resp.json()[0] if me_req_resp.status_code == 200 and len(me_req_resp.json()) > 0 else None
    if current_request:
        update_resp = requests.put(PUT_REQUEST_URL_TMPL.format(BASE_URL, current_request['id']),
                                   json={'projects': project_language_pairs}, headers=headers)
        current_request = update_resp.json() if update_resp.status_code == 200 else current_request

    while True:
        # Loop and wait until fewer than 2 reviews assigned, as creating
        # a request will fail
        wait_for_assign_eligible()
        if current_request is None:
            logger.info('Creating a request for ' + str(len(project_language_pairs)) +
                        ' possible project/language combinations')
            create_resp = requests.post(CREATE_REQUEST_URL,
                                        json={'projects': project_language_pairs},
                                        headers=headers)
            current_request = create_resp.json() if create_resp.status_code == 201 else None
            if current_request:
                logger.info('request id:' + str(create_resp.json()['id']))
            else:
                logger.info('request returned' + str(create_resp))
        else:
            logger.info('request id:' + str(current_request['id']))
            closing_at = parser.parse(current_request['closed_at'])

            utcnow = datetime.utcnow()
            utcnow = utcnow.replace(tzinfo=pytz.utc)

            if closing_at < utcnow + timedelta(minutes=30):
                # Refreshing a request is more costly than just loading
                # and only needs to be done to ensure the request doesn't
                # expire (1 hour)
                logger.info('0-0-0-0-0-0-0-0-0-0- refreshing request 0-0-0-0-0-0-0')
                current_request = refresh_request(current_request)
            else:
                logger.info('Checking for new assignments')
                # If an assignment has been made since status was last checked,
                # the request record will no longer be 'fulfilled'
                url = GET_REQUEST_URL_TMPL.format(BASE_URL, current_request['id'])
                get_req_resp = requests.get(url, headers=headers)
                current_request = get_req_resp.json() if me_req_resp.status_code == 200 else None

        get_wait_stats()
        current_request = alert_for_assignment(current_request, headers)
        if current_request:
            # Wait 2 minutes before next check to see if the request has been fulfilled
            time.sleep(120.0)


def get_wait_stats():
    """
    Gets place in line and number of available reviews for each available
    project, and stores to mongoDB.
    """
    logger.info("Getting wait/assignment stats")
    me_resp = requests.get(ME_URL, headers=headers)
    me_resp.raise_for_status()
    languages = me_resp.json()['application']['languages'] or ['en-us']

    certs_resp = requests.get(CERTS_URL, headers=headers)
    certs_resp.raise_for_status()

    certs = certs_resp.json()
    for lang in languages:
        for cert in certs:
            if not cert['status'] == 'certified':
                continue

            info = {}
            client = MongoClient()
            db = client[DB_NAME]
            coll = db['available_reviews']
            info['name'] = cert['project']['name']
            info['project_id'] = cert['project']['id']
            logger.info('project: ' + info['name'] + ', id: ' + str(info['project_id']))
            info['language'] = lang
            try:
                info['wait_count'] = cert['project']['awaiting_review_count']
                logger.info('awaiting review: ' + str(info['wait_count']))
            except KeyError:
                logger.info('couldn\'t get wait count; key error')
                info['wait_count'] = 0
            # now insert into mongodb
            info['datetime'] = datetime.now()
            coll.insert_one(info)
            client.close()

    me_resp = requests.get(ME_REQUEST_URL, headers=headers)
    # print 'me_resp:' + str(me_resp.json())
    if len(me_resp.json()) > 0:
        for r in me_resp.json():
            info = {}
            client = MongoClient()
            db = client[DB_NAME]
            coll = db['wait_stats']
            req_id = r['id']
            logger.info('request id:' + str(req_id))
            wait_stats = requests.get(WAIT_URL.format(BASE_URL, req_id), headers=headers)
            info = wait_stats.json()[0]
            proj_name = proj_id_dict[int(wait_stats.json()['project_id'])]
            print 'in position' + wait_stats.json()['position'] + ' for project ' + proj_name
            info['datetime'] = datetime.now()
            info['project_name'] = proj_name
            coll.insert_one(info)
            client.close()

    # waits_resp = requests.get('{}/submission_requests/{}/waits'.format(BASE_URL, resp_id))
    # if len(waits_resp.json()) > 0:
    #     for r in waits_resp.json():
    #         info = {}
    #         client = MongoClient()
    #         db = client[DB_NAME]
    #         coll = db['wait_stats']
    #         proj_id = r['id']
    #         proj_name = proj_id_dict[proj_id]
    #         position = r['position']
    #         print 'in position ' + str(position) + ' for project ' + proj_name
    #         info =


def set_headers(token):
    global headers
    headers = {'Authorization': token, 'Content-Length': '0'}


def run_main():
    set_headers(args.token)
    try:
        request_reviews()
    except Exception as e:
        print 'error!!!!'
        sm.send_error(error=e)
        traceback.print_exc()
        mtn = pytz.timezone('US/Mountain')
        print datetime.now(mtn)
        time.sleep(30) # wait 30 seconsd to let any errors clear out
        run_main()

if __name__ == "__main__":
    cmd_parser = argparse.ArgumentParser(description =
	"Poll the Udacity reviews API to claim projects to review."
    )
    cmd_parser.add_argument('--auth-token', '-T', dest='token',
	metavar='TOKEN', type=str,
	action='store', default=os.environ.get('udacity_api_key'),
	help="""
	    Your Udacity auth token. To obtain, login to review.udacity.com, open the Javascript console, and copy the output of `JSON.parse(localStorage.currentUser).token`.  This can also be stored in the environment variable UDACITY_AUTH_TOKEN.
	"""
    )
    cmd_parser.add_argument('--debug', '-d', action='store_true', help='Turn on debug statements.')
    args = cmd_parser.parse_args()

    if not args.token:
        cmd_parser.print_help()
        cmd_parser.exit()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    run_main()
