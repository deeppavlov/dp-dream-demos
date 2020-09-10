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
        # r"(what|which) (is|are)( the)? (harvesters|combines) status(es)?",
        r"(harvesters|combines) status(es)?",
        r"status(es)?[a-z ]* (harvesters|combines)"
    ],
    "status_request": [
        # r"(what|which) is( the| a)? [0-9]+ (harvester|combine) status",
        r"[0-9]+ (harvester|combine) status",
        r"(harvester|combine) [0-9]+ status",
        r"status [a-z ]*[0-9]+ (harvester|combine)",
        r"status [a-z ]*(harvester|combine) [0-9]+",
    ],
    "broken_ids_request": [
        r"(what|which) (harvester|combine)s? requires? repairs?",
        r"(what|which) (harvester|combine)s?( is| are)? broken"
    ],
    "full_ids_request": [
        r"(what|which) (harvester|combine)s? (is|are|do|does) full"
    ],
    "working_ids_request": [
        r"(what|which) (harvester|combine)s? (is|are|do|does) work(ing|s)?"
    ],
    "inactive_ids_request": [
        r"(what|which) (harvester|combine)s? (is|are|do|does) inactive"
    ],
    "trip_request": [
        # r"(want|need|prepare) (rover|vehicle) for( a| the| my)? trip",
        # r"(lets|let us|let's) have( a| the)? trip"
        r"(rover|vehicle) [a-z ]*trip",
        r"trip [a-z ]*(rover|vehicle)"
    ]
}
for intent in REQUESTS:
    REQUESTS[intent] = [re.compile(template, re.IGNORECASE) for template in REQUESTS[intent]]

RESPONSES = {
    "all_statuses_request": [
        "Of TOTAL_N_HARVESTERS harvesters, harvester FULL_IDS is full, harvester WORKING_IDS is working,"
        " harvester BROKEN_IDS is awaiting repaires, harvester INACTIVE_IDS is inactive."
    ],
    "status_request": [
        "The harvester ID is STATUS."
    ],
    "broken_ids_request": {
        "yes": "Reporting: harvester BROKEN_IDS is broken.",
        "no": "No broken harvesters found.",
        "required": {"harvesters": "broken"}
    },
    "full_ids_request": {
        "yes": "Reporting: harvester FULL_IDS is full.",
        "no": "No full harvesters found.",
        "required": {"harvesters": "full"}
    },
    "working_ids_request": {
        "yes": "Reporting: harvester WORKING_IDS is working.",
        "no": "No working harvesters found.",
        "required": {"harvesters": "working"}
    },
    "inactive_ids_request": {
        "yes": "Reporting: harvester INACTIVE_IDS is inactive.",
        "no": "No inactive harvesters found.",
        "required": {"harvesters": "inactive"}
    },
    "trip_request": {
        "yes": "Prepare rover ROVER_FOR_TRIP_ID for a trip.",
        "no": "Can't prepare a rover for a trip, no available rovers.",
        "required": {"rovers": "available"}
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


def get_ids_with_statuses(status, which_statuses="harvesters"):
    # harvesters statuses are out of ["full", "working", "broken", "inactive"]
    if len(status) == 0:
        return []
    if which_statuses == "harvesters":
        status_map = {"working": ["optimal", "suboptimal"],
                      "full": ["full"],
                      "broken": ["stall"],
                      "inactive": ["inactive"]}
        statuses = status_map[status]
    else:
        statuses = [status]

    ids = []
    for str_id in DATABASE[which_statuses]:
        if DATABASE[which_statuses][str_id] in statuses:
            ids.append(str_id)
    return ids


def get_statuses_with_ids(ids, which_statuses="harvesters"):
    # harvesters statuses are out of ["full", "working", "broken", "inactive"]
    if which_statuses == "harvesters":
        status_map = {"optimal": "working",
                      "suboptimal": "working",
                      "full": "full",
                      "stall": "broken",
                      "inactive": "inactive"}
    else:
        status_map = {"available": "available",
                      "stall": "stall",
                      "inactive": "inactive"}

    statuses = []
    for str_id in ids:
        statuses.append(status_map[DATABASE[which_statuses][str_id]])
    return statuses


def fill_harvesters_status_templates(response, request_text):
    full_ids = get_ids_with_statuses("full")
    working_ids = get_ids_with_statuses("working")
    broken_ids = get_ids_with_statuses("broken")
    inactive_ids = get_ids_with_statuses("inactive")
    available_rovers_ids = get_ids_with_statuses("available", which_statuses="rovers")

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

    if len(inactive_ids) == 0:
        response = response.replace("harvester INACTIVE_IDS is", "none is")
    elif len(inactive_ids) == 1:
        response = response.replace("INACTIVE_IDS", str(inactive_ids[0]))
    else:
        response = response.replace("harvester INACTIVE_IDS is",
                                    f"harvesters {', '.join(inactive_ids)} are")

    if len(available_rovers_ids) == 1:
        response = response.replace(f"ROVER_FOR_TRIP_ID", f"{available_rovers_ids[0]}")
    elif len(available_rovers_ids) > 1:
        response = response.replace("rover ROVER_FOR_TRIP_ID", f"rovers {', '.join(available_rovers_ids)}")

    if "ID" in response:
        required_id = re.search(r"[0-9]+", request_text)
        if required_id:
            required_id = required_id[0]
        if required_id and required_id in DATABASE["harvesters"]:
            status = get_statuses_with_ids([required_id])[0]
            response = response.replace("ID", required_id)
            response = response.replace("STATUS", status)
        else:
            response = f"I can answer only about the following harvesters ids: " \
                       f"{', '.join(DATABASE['harvesters'].keys())}."

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
        required_statuses = responses_collection.get("required", {}).get("harvesters", "")
        if len(required_statuses) == 0:
            required_statuses = responses_collection.get("required", {}).get("rovers", "")
            ids = get_ids_with_statuses(required_statuses, which_statuses="rovers")
        else:
            ids = get_ids_with_statuses(required_statuses, which_statuses="harvesters")

        if len(required_statuses) == 0 or (len(required_statuses) > 0 and len(ids) > 0):
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
        logger.info(f"Found intent {intent} in user request {last_utt_text}")
        response, confidence = generate_response_from_db(intent, last_utt_text)

        responses.append(response)
        confidences.append(confidence)

    total_time = time.time() - st_time
    logger.info(f"harvesters_maintenance_skill exec time = {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
