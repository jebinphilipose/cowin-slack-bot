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
