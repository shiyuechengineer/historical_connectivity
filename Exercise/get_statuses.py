import configparser
from datetime import datetime
# SOMETHING IS MISSING
import os
import sys
import time

import requests


# https://api.meraki.com/api_docs#list-the-status-of-every-meraki-device-in-the-organization
def org_device_statuses(api_key, org_id, retries=5):
    section = 'Organizations'
    endpoint = 'List the status of every Meraki device in the organization'
    call_type = 'GET'
    get_url = f'https://api-mp.meraki.com/api/v0/organizations/{org_id}/deviceStatuses'
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    while retries > 0:
        response = requests.get(get_url, headers=headers)

        if response.ok:
            print(f'{section} {call_type} completed with success - {endpoint}')
            return response.json()
        elif response.status_code == 429:
            wait = int(response.headers['Retry-After'])
            print(f'{section} {call_type} retrying in {wait} seconds - {endpoint}')
            time.sleep(wait)
            retries -= 1
        else:
            message = response.text
            print(f'{section} {call_type} failed with error {message} - {endpoint}')
            return None


# Store credentials in a separate file
def gather_credentials():
    cp = configparser.ConfigParser()
    try:
        cp.read('credentials.ini')
        api_key = cp.get('meraki', 'key2')
        org_id = cp.get('meraki', 'organization')
    except:
        print('Problem with your credentials.ini file!')
        sys.exit(2)
    return api_key, org_id


# Make API call to get the device statuses of an org, then save to local file
def get_org_statuses(api_key, org_id):
    data = org_device_statuses(api_key, org_id)

    if data:
        # Keep latest n logs
        dir = 'statuses'
        if dir not in os.listdir():
            os.mkdir(dir)
        n = 1000
        log_files = os.listdir(dir)
        if len(log_files) > n:
            log_files.sort()
            for file in log_files[:-n]:
                os.remove(f'{dir}/{file}')

        # Write data to file
        timestamp = f'{datetime.utcnow():%Y-%m-%d_%H-%M-%S}'
        file_name = f'{timestamp}.json'
        with open(f'{dir}/{file_name}', 'w') as fp:
            # SOMETHING IS MISSING
            pass
        print(f'Saved data to {dir}/{file_name}')

        return data, timestamp
    else:
        return None, None


if __name__ == '__main__':
    api_key, org_id = gather_credentials()
    get_org_statuses(api_key, org_id)
