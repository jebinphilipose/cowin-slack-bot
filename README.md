# COWIN SLACK BOT

## Project Overview

To design & build a Slack bot that notifes a user on COVID vaccine availability.

## Getting Started

### Prerequisites

* Python 3.6+
* Git
* Redis

### Project Setup

1. Clone this repo: `$ git clone https://github.com/jebinphilipose/cowin-slack-bot.git && cd cowin-slack-bot`
2. Create `.env` file in project root, see below for list of all variables
    ```
    REDIS_HOST=
    REDIS_PORT=
    REDIS_PASS=
    SLACK_BOT_TOKEN=
    ```
    Note: You need to setup a slack workspace, create an app with required scopes, and install the app to the workspace. You can get access token from "OAuth & Permissions" under the settings page
3. Create `users.json` file in project root, with the metadata of your users in the following format:
    ```
    [
    {
      "name": "User 1",
      "pincode": null,
      "state_name": "Karnataka",
      "district_name": "Bangalore Urban",
      "vaccine": [
        "COVISHIELD",
        "COVAXIN"
      ],
      "dosage": [
        {
          "age": 18,
          "dose_type": "dose1"
        },
        {
          "age": 45,
          "dose_type": "dose1"
        }
      ],
      "slack_id": "U1339A79B1Q"
    },
    {
      "name": "User 2",
      "pincode": 201301,
      "state_name": null,
      "district_name": null,
      "vaccine": [
        "COVISHIELD"
      ],
      "dosage": [
        {
          "age": 18,
          "dose_type": "dose1"
        }
      ],
      "slack_id": "U8140H25S7A"
    }
    ]
    ```
4. Create a virtual environment: `$ python3 -m venv ./venv`
5. Activate virtualenv: `$ source venv/bin/activate`
6. Upgrade pip and install dependencies: `$ pip install --upgrade pip && pip install -r requirements.txt`
7. Now you can call `send_slack_notification_to_users` function in `cowin_bot.py` to send notification. You can also run this as a scheduled job with a specific time interval.


## Demo

![alt-text](blob/cowin_bot.gif)

## Registration Form

This is the user registration form I used to gather metadata of the users: [CoWIN BOT User Data](https://docs.google.com/forms/d/1k58jf3H9bnJ-jkP5CyR94b3lb0f7NXFUcDJsMiYoGSk/viewform?ts=60a2e269&edit_requested=true)