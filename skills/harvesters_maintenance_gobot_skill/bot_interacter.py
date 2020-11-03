import requests
import sys

endpoint_base_url = "http://10.11.1.41:3008"
reset_url = f"{endpoint_base_url}/reset"
gobot_url = f"{endpoint_base_url}/respond"

def reset():
    return requests.get(reset_url)

def gobot(text):
    payload = {"dialogs": [{"human_utterances":[{"text": text, "annotations": {}}]}]}
    return requests.post(gobot_url, json=payload).text


for line in sys.stdin:
    line = line.strip()
    if line == "reset":
        print(reset())
    else:
        print("bot:", gobot(line))

