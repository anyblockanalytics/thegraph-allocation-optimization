import requests
from dotenv import load_dotenv
import os

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')



alert_map = {
    "emoji": {
        "threshold_reached": ":large_green_circle:",
        "threshold_not_reached": ":small_red_triangle_down:"
    },
    "text": {
        "threshold_reached": "THRESHOLD REACHED",
        "threshold_not_reached": "THRESHOLD NOT REACHED"
    },
    "message": {
        "threshold_reached": "Reallocating recommended",
        "threshold_not_reached": "Allocations are optimal"
    },
    "color": {
        "threshold_reached": "#32a852",
        "threshold_not_reached": "#ad1721"
    }
}


def alert_to_slack(status,threshold, threshold_interval,current_rewards, optimization_rewards,difference):


    data = {
        "text": "The Graph Optimization Alert Manager",
        "username": "Notifications",
        "channel": SLACK_CHANNEL,
        "attachments": [
            {
                "text": "{emoji} [*{state}*] ({threshold}%) Threshold Interval: {threshold_interval}\n {message}".format(
                    emoji=alert_map["emoji"][status],
                    state=alert_map["text"][status],
                    threshold = threshold,
                    threshold_interval = threshold_interval,
                    message=alert_map["message"][
                                status] + '\nCurrent GRT Rewards: ' +
                                str(current_rewards) + '\nGRT Rewards after Optimization: ' + str(optimization_rewards) +
                                '\n Difference in Rewards: ' + str(difference) + " GRT"
                ),
                "color": alert_map["color"][status],
                "attachment_type": "default",

            }]
    }
    r = requests.post(SLACK_WEBHOOK_URL, json=data)
    return r.status_code

