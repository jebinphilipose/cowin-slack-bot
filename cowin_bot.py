import requests
import json
from fake_useragent import UserAgent

temp_user_agent = UserAgent()
browser_header = {'User-Agent': temp_user_agent.random}


def get_state_id(state_name):
    state_name = state_name.title()
    state_id = None
    url = 'https://cdn-api.co-vin.in/api/v2/admin/location/states'
    response = requests.get(url, headers=browser_header)
    if response.ok and ('states' in response.text):
        states = json.loads(response.text)['states']
        for state in states:
            if state['state_name'] == state_name:
                state_id = state['state_id']
    return state_id


def get_district_id(state_id, district_name):
    district_name = district_name.title()
    district_id = None
    url = f'https://cdn-api.co-vin.in/api/v2/admin/location/districts/{state_id}'
    response = requests.get(url, headers=browser_header)
    if response.ok and ('districts' in response.text):
        districts = json.loads(response.text)['districts']
        for district in districts:
            if district['district_name'] == district_name:
                district_id = district['district_id']
    return district_id
