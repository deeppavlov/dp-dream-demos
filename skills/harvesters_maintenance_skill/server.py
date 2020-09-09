#!/usr/bin/env python

import logging
import time
import random
import re
import json

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

REQUESTS = {
    "all_statuses_request": [
        r"(what|which) (is|are)( the)? (harvesters|combines) status(es)?"
    ],
    "status_request": [
        r"(what|which) is( the| a)? [0-9]+ (harvester|combine) status"
    ],
    "broken_ids_request": [
        r"(what|which) (harvester|combine)s? requires? repairs?",
        r"(what|which) (harvester|combine)s?( is| are)? broken"
    ],
    "working_ids_request": [
        r"(what|which) (harvester|combine)s? (is|are|do|does) work(ing|s)?"
    ],
    "trip_request": [
        r"(want|need|prepare) (rover|vehicle) for( a| the| my)? trip",
        r"(lets|let us|let's) have( a| the)? trip"
    ]
}
for intent in REQUESTS:
    REQUESTS[intent] = [re.compile(template, re.IGNORECASE) for template in REQUESTS[intent]]

RESPONSES = {
    "all_statuses_request": [
        "Of TOTAL_N_HARVESTERS harvesters, harvester FULL_IDS is full, harvester WORKING_IDS is working,"
        " harvester BROKEN_IDS is awaiting repaires."
    ],
    "status_request": [
        "The harvester ID is STATUS."
    ],
    "broken_ids_request": {
        "yes": "Harvester BROKEN_IDS is broken.",
        "no": "No broken harvesters found.",
        "required_harvester": "stall"
    },
    "working_ids_request": {
        "yes": "Harvester WORKING_IDS is working.",
        "no": "No working harvesters found.",
        "required_harvester": ["optimal", "suboptimal"]
    },
    "trip_request": {
        "yes": "Prepare rover ROVER_ID for a trip.",
        "no": "Can't prepare a rover for a trip.",
        "required_rover": "available"
    },
    "not_relevant": [
        "I don't have this information.",
        "I don't understand you.",
        "I don't know what to answer."
    ]
}


def update_database():
    with open("harvesters_status.json", "r") as f:
        db = json.load(f)
    return db, time.time()


DATABASE, PREV_UPDATE_TIME = update_database()


def detect_intent(utterance):
    for intent in REQUESTS:
        for template in REQUESTS[intent]:
            if re.search(template, utterance):
                return intent
    return "not_relevant"


def get_ids_with_statuses(status):
    # statuses are out of ["full", "working", "broken", "inactive"]
    status_map = {"working": ["optimal", "suboptimal"],
                  "full": ["full"],
                  "broken": ["stall"],
                  "inactive": ["inactive"]}
    statuses = status_map[status]

    ids = []
    for str_id in DATABASE["harvesters"]:
        if DATABASE["harvesters"][str_id] in statuses:
            ids.append(str_id)
    return ids


def get_statuses_with_ids(ids):
    # statuses are out of ["full", "working", "broken", "inactive"]
    status_map = {"optimal": "working",
                  "suboptimal": "working",
                  "full": "full",
                  "stall": "broken",
                  "inactive": "inactive"}

    statuses = []
    for str_id in ids:
        statuses.append(status_map[DATABASE["harvesters"][str_id]])
    return statuses


def fill_harvesters_status_templates(response, request_text):
    full_ids = get_ids_with_statuses("full")
    working_ids = get_ids_with_statuses(["optimal", "suboptimal"])
    broken_ids = get_ids_with_statuses("stall")

    response = response.replace("TOTAL_N_HARVESTERS", str(len(DATABASE["harvesters"])))

    if len(full_ids) == 0:
        response = response.replace("harvester FULL_IDS is", "none is")
    elif len(full_ids) == 1:
        response = response.replace("FULL_IDS", str(full_ids[0]))
    else:
        response = response.replace("harvester FULL_IDS is",
                                    f"harvesters {', '.join(full_ids)} are")

    if len(working_ids) == 0:
        response = response.replace("harvester WORKING_IDS is", "none is")
    elif len(working_ids) == 1:
        response = response.replace("WORKING_IDS", str(working_ids[0]))
    else:
        response = response.replace("harvester WORKING_IDS is",
                                    f"harvesters {', '.join(working_ids)} are")

    if len(broken_ids) == 0:
        response = response.replace("harvester BROKEN_IDS is", "none is")
    elif len(broken_ids) == 1:
        response = response.replace("BROKEN_IDS", str(broken_ids[0]))
    else:
        response = response.replace("harvester BROKEN_IDS is",
                                    f"harvesters {', '.join(broken_ids)} are")

    if "ID" in response:
        required_id = re.search(r"[0-9]+", request_text)[0]
        status = get_statuses_with_ids([required_id])[0]
        response = response.replace("ID", required_id)
        response = response.replace("STATUS", status)

    return response


def generate_response_from_db(intent, utterance):
    global PREV_UPDATE_TIME
    if time.time() - PREV_UPDATE_TIME >= 3600:
        DATABASE, PREV_UPDATE_TIME = update_database()

    response = ""
    responses_collection = RESPONSES[intent]
    if isinstance(responses_collection, list):
        response = random.choice(responses_collection)
    elif isinstance(responses_collection, dict):
        harv_required_statuses = responses_collection["required"]
        ids = get_ids_with_statuses(harv_required_statuses)
        if len(ids) > 0:
            response = responses_collection["yes"]
        else:
            response = responses_collection["no"]

    response = fill_harvesters_status_templates(response, utterance)

    if intent == "not_relevant":
        confidence = 0.5
    else:
        confidence = 1.0

    return response, confidence


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialogs = request.json["dialogs"]

    responses = []
    confidences = []

    for dialog in dialogs:
        last_utt_text = dialog["human_utterances"][-1]["text"]
        intent = detect_intent(last_utt_text)
        response, confidence = generate_response_from_db(intent, last_utt_text)

        responses.append(response)
        confidences.append(confidence)

    total_time = time.time() - st_time
    logger.info(f"harvesters_maintenance_skill exec time = {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
