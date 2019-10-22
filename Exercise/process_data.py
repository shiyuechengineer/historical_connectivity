import os
import sys

from get_statuses import *


# https://api.meraki.com/api_docs#list-the-devices-in-an-organization
def get_org_devices(api_key, org_id, retries=5):
    section = 'Devices'
    endpoint = 'List the devices in an organization'
    call_type = 'GET'
    get_url = f'https://api-mp.meraki.com/api/v0/organizations/{org_id}/devices'
    headers = {'X-Cisco-Meraki-API-Key': api_key, 'Content-Type': 'application/json'}

    aggregated_data = []
    page_length = 1000
    get_url += f'?perPage={page_length}'

    while True:
        sub_retries = retries

        while sub_retries > 0:
            response = requests.get(get_url, headers=headers)

            if response.ok:
                print(f'{section} {call_type} completed with success - {endpoint}')
                data = response.json()
                aggregated_data.extend(data)

                if len(data) < page_length:
                    return aggregated_data
                else:
                    links = response.headers['Link'].split(', ')
                    for link in links:
                        if 'rel=next' in link:
                            get_url = link[link.find('<')+1 : link.rfind('>')]
                    break
            elif response.status_code == 429:
                print(f'{section} {call_type} retrying in {wait} seconds - {endpoint}')
                wait = int(response.headers['Retry-After'])
                time.sleep(wait)
                sub_retries -= 1
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


# Process status changes for org-wide devices
def process_connectivity_data(api_key, org_id):
    file_name = 'connectivity.json'
    if file_name not in os.listdir():
        connectivity_data = {}
    else:
        with open(file_name) as fp:
            # SOMETHING IS MISSING
            pass

    (statuses, timestamp) = get_org_statuses(api_key, org_id)
    updated = False
    if not statuses:
        sys.exit('Problem with getting org-wide device statuses using your API key & org ID!')

    # Update data on org-wide devices (not statuses) so we can get model information
    current_serials = [status['serial'] for status in statuses]
    logged_serials = connectivity_data.keys()
    new_serials = [s for s in current_serials if s not in logged_serials]
    if new_serials:
        devices = get_org_devices(api_key, org_id)
        mappings = {device['serial']: device['model'] for device in devices}

    # Iterate through statuses to check for state changes
    for data in statuses:
        serial = data['serial']
        status = data['status']

        if serial in connectivity_data:
            states = connectivity_data[serial]['states']
            if states[-1][1] != status:
                connectivity_data[serial]['states'].append((timestamp, status))
                updated = True
        else:
            # For newly-added serials, add their model mappings
            model = mappings[serial]
            connectivity_data[serial] = {'model': model, 'states': [(timestamp, status)]}
            updated = True

    # Also update those devices no longer found in networks with status "unknown"
    old_serials = [s for s in logged_serials if s not in current_serials]
    for serial in old_serials:
        if connectivity_data[serial]['states'][-1][1] != 'unknown':
            connectivity_data[serial]['states'].append((timestamp, 'unknown'))
            updated = True

    # Update connectivity JSON data file, while keeping a backup
    if updated:
        if file_name in os.listdir():
            os.rename(file_name, f'backup_{file_name}')
        with open(file_name, 'w') as fp:
            # SOMETHING IS MISSING
            pass
        print(f'Updated {file_name} at timestamp {timestamp}')
    else:
        print('Checked device statuses, but no new updates')


if __name__ == '__main__':
    api_key, org_id = gather_credentials()
    process_connectivity_data(api_key, org_id)
