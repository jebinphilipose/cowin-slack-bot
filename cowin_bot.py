import requests
import json
import pytz
import os
import time
import schedule
import logging
from datetime import datetime, timedelta
from fake_useragent import UserAgent
from redis_client import redis_connect

# Set request headers
temp_user_agent = UserAgent()
browser_header = {'User-Agent': temp_user_agent.random,
                  'Accept-Language': 'en_IN'}

# Get redis client
r = redis_connect()

# Setup logging
logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s\n',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')


def get_state_id_from_api(state_name):
    state_name = state_name.title()
    state_id = None
    url = 'https://cdn-api.co-vin.in/api/v2/admin/location/states'
    response = requests.get(url, headers=browser_header)
    if '403 ERROR' in response.text:
        raise Exception('Request blocked (403 ERROR)')
    if response.ok and ('states' in response.text):
        states = json.loads(response.text)['states']
        for state in states:
            if state['state_name'] == state_name:
                state_id = state['state_id']
    return state_id


def get_district_id_from_api(state_id, district_name):
    district_name = district_name.title()
    district_id = None
    url = f'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{state_id}'
    response = requests.get(url, headers=browser_header)
    if '403 ERROR' in response.text:
        raise Exception('Request blocked (403 ERROR)')
    if response.ok and ('districts' in response.text):
        districts = json.loads(response.text)['districts']
        for district in districts:
            if district['district_name'] == district_name:
                district_id = district['district_id']
    return district_id


def get_district_id_from_cache(state_name, district_name):
    key = state_name.replace(" ", "_") + "_" + district_name.replace(" ", "_")
    district_id = r.get(key)
    if district_id is not None:
        district_id = int(district_id)
    return district_id


def get_state_id_from_cache(state_name):
    state_id = r.get(state_name)
    if state_id is not None:
        state_id = int(state_id)
    return state_id


def set_district_id_in_cache(state_name, district_name, district_id):
    key = state_name.replace(" ", "_") + "_" + district_name.replace(" ", "_")
    return r.setex(key, timedelta(hours=24), district_id)


def set_state_id_in_cache(state_name, state_id):
    return r.setex(state_name, timedelta(hours=24), state_id)


def get_state_id(state_name):
    state_id = get_state_id_from_cache(state_name)
    if state_id is None:
        state_id = get_state_id_from_api(state_name)
        set_state_id_in_cache(state_name, state_id)
        logging.info(f'Setting state_id ({state_id}) for {state_name} in redis cache')
    return state_id


def get_district_id(state_name, district_name):
    district_id = get_district_id_from_cache(state_name, district_name)
    if district_id is None:
        state_id = get_state_id(state_name)
        district_id = get_district_id_from_api(state_id, district_name)
        set_district_id_in_cache(state_name, district_name, district_id)
        logging.info(f'Setting district_id ({district_id}) for {district_name}, {state_name} in redis cache')
    return district_id


def get_date_string(date):
    return date.strftime('%d-%m-%Y')


def get_users():
    with open('users.json') as f:
        users = json.load(f)
    return users


def get_unique_pincodes_and_districts():
    location_map = {
        'pincodes': [],
        'district_ids': []
    }
    users = get_users()
    for user in users:
        if user['pincode'] is not None and user['pincode'] not in location_map['pincodes']:
            location_map['pincodes'].append(user['pincode'])
        elif user['state_name'] is not None and user['district_name'] is not None:
            district_id = get_district_id(user['state_name'], user['district_name'])
            if district_id not in location_map['district_ids']:
                location_map['district_ids'].append(district_id)
    return location_map


def fetch_available_vaccine_slots(url, sessions_map, location_key):
    response = requests.get(url, headers=browser_header)
    if '403 ERROR' in response.text:
        raise Exception('Request blocked (403 ERROR)')
    if response.ok and 'centers' in response.text:
        centers = json.loads(response.text)['centers']
        for center in centers:
            if location_key not in sessions_map:
                sessions_map[location_key] = {}
            if center['center_id'] not in sessions_map[location_key]:
                sessions_map[location_key][center['center_id']] = {}
                sessions_map[location_key][center['center_id']]['name'] = center['name']
                sessions_map[location_key][center['center_id']]['address'] = center['address']
            if 'sessions' not in sessions_map[location_key][center['center_id']]:
                sessions_map[location_key][center['center_id']]['sessions'] = []
            for session in center['sessions']:
                if session['available_capacity'] > 0:
                    sessions_map[location_key][center['center_id']]['sessions'].append(session)


def get_available_vaccine_slots():
    IST = pytz.timezone('Asia/Kolkata')
    dates = [get_date_string(datetime.now(IST)),
             get_date_string(datetime.now(IST) + timedelta(days=7)),
             get_date_string(datetime.now(IST) + timedelta(days=14))]
    locations_map = get_unique_pincodes_and_districts()
    sessions_map = {}
    for pincode in locations_map['pincodes']:
        for date in dates:
            url = f'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={pincode}&date={date}'
            fetch_available_vaccine_slots(url, sessions_map, pincode)
    for district_id in locations_map['district_ids']:
        for date in dates:
            url = f'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={district_id}&date={date}'
            fetch_available_vaccine_slots(url, sessions_map, district_id)
    return sessions_map


def generate_user_notification_message(user, sessions_map):
    message = ''
    for dosage in user['dosage']:
        str_list = []
        for vaccine in user['vaccine']:        
            if user['pincode'] is not None:
                location_centers = sessions_map[user['pincode']]
            elif user['state_name'] is not None and user['district_name'] is not None:
                district_id = get_district_id(user['state_name'], user['district_name'])
                location_centers = sessions_map[district_id]
            for center in location_centers.values():
                for session in center['sessions']:
                    if session['min_age_limit'] == dosage['age'] and session['vaccine'] == vaccine:
                        if dosage['dose_type'] == 'dose1' and session['available_capacity_dose1'] > 0:
                            str_list.append(f'{session["available_capacity_dose1"]} slots of {vaccine} (DOSE 1) available at {center["name"]} for age group {dosage["age"]}+')
                        elif dosage['dose_type'] == 'dose2' and session['available_capacity_dose2'] > 0:
                            str_list.append(f'{session["available_capacity_dose2"]} slots of {vaccine} (DOSE 2) available at {center["name"]} for age group {dosage["age"]}+')
        str_list = sorted(str_list, key=lambda x: int(x.split()[0]), reverse=True)
        message = message + "\n".join(str_list) + "\n\n"
    return message.strip()


def send_slack_notification_to_users():
    try:
        sessions_map = get_available_vaccine_slots()
        users = get_users()
        for user in users:
            messsage = generate_user_notification_message(user, sessions_map)
            auth_token = os.getenv("SLACK_BOT_TOKEN")
            headers = {'Authorization': 'Bearer ' + auth_token}
            data = {
                'channel': user['slack_id'],
                'text': messsage
            }
            url = 'https://slack.com/api/chat.postMessage'
            response = requests.post(url, data=data, headers=headers)
            if json.loads(response.text)['ok']:
                logging.info(f'Notification sent to {user["name"]}')
            elif json.loads(response.text)['error'] == 'no_text':
                logging.info(f'No vaccines available for {user["name"]}')
    except Exception as e:
        logging.error(str(e))


if __name__ == "__main__":
    schedule.every(60).seconds.do(send_slack_notification_to_users)
    while True:
        schedule.run_pending()
        time.sleep(1)
