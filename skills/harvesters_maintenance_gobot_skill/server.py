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




# def update_database():
#     """Update database loading new version every our
#     """
#     with open("harvesters_status.json", "r") as f:
#         db = json.load(f)
#     return db, time.time()


# DATABASE, PREV_UPDATE_TIME = update_database()


# def get_ids_with_statuses(status, object="harvester"):
#     """Return ids of objects with given (inner) status
#     """
#     if len(status) == 0:
#         return []
#     if object == "harvester":
#         status_map = {"working": ["optimal", "suboptimal"],
#                       "full": ["full"],
#                       "stall": ["stall"],
#                       "inactive": ["inactive"]}
#         statuses = status_map[status]
#     else:
#         statuses = [status]

#     ids = []
#     for str_id in DATABASE[f"{object}s"]:
#         if DATABASE[f"{object}s"][str_id] in statuses:
#             ids.append(str_id)
#     return ids


# def get_statuses_with_ids(ids, object="harvester"):
#     """Return (inner) statuses of objects with given ids
#     """
#     # harvesters statuses are out of ["full", "working", "stall", "inactive"]
#     if object == "harvester":
#         status_map = {"optimal": "working",
#                       "suboptimal": "working",
#                       "full": "full",
#                       "stall": "stall",
#                       "inactive": "inactive"}
#     else:
#         status_map = {"available": "available",
#                       "stall": "stall",
#                       "inactive": "inactive"}

#     statuses = []
#     for str_id in ids:
#         statuses.append(status_map[DATABASE[f"{object}s"][str_id]])
#     return statuses


# def fill_in_particular_status(response, ids, template_to_fill, object="harvester"):
#     """Replaces `template_to_fill` (e.g. `FULL_IDS`) in templated response to objects with given `ids`
#     """
#     if len(ids) == 0:
#         response = response.replace(f"{object} {template_to_fill} is", "none is")
#     elif len(ids) == 1:
#         response = response.replace(f"{template_to_fill}", str(ids[0]))
#     else:
#         response = response.replace(f"{object} {template_to_fill} is",
#                                     f"{object}s {', '.join(ids)} are")
#     return response


# def fill_harvesters_status_templates(response, request_text):
#     """Fill all variables in the templated response
#     """
#     full_ids = get_ids_with_statuses("full")
#     working_ids = get_ids_with_statuses("working")
#     broken_ids = get_ids_with_statuses("stall")
#     inactive_ids = get_ids_with_statuses("inactive")

#     available_rovers_ids = get_ids_with_statuses("available", object="rover")
#     inactive_rovers_ids = get_ids_with_statuses("inactive", object="rover")
#     broken_rovers_ids = get_ids_with_statuses("stall", object="rover")

#     response = response.replace("TOTAL_N_HARVESTERS", str(len(DATABASE["harvesters"])))

#     response = fill_in_particular_status(response, full_ids, "FULL_IDS", "harvester")
#     response = fill_in_particular_status(response, working_ids, "WORKING_IDS", "harvester")
#     response = fill_in_particular_status(response, broken_ids, "BROKEN_IDS", "harvester")
#     response = fill_in_particular_status(response, inactive_ids, "INACTIVE_IDS", "harvester")

#     response = fill_in_particular_status(response, available_rovers_ids, "AVAILABLE_ROVER_IDS", "rover")
#     response = fill_in_particular_status(response, inactive_rovers_ids, "INACTIVE_ROVER_IDS", "rover")
#     response = fill_in_particular_status(response, broken_rovers_ids, "BROKEN_ROVER_IDS", "rover")

#     if len(available_rovers_ids) == 1:
#         avail_rover_id = available_rovers_ids[0]
#     elif len(available_rovers_ids) > 1:
#         avail_rover_id = random.choice(available_rovers_ids)
#     response = response.replace("ROVER_FOR_TRIP_ID", f"{avail_rover_id}")

#     if "ID" in response:
#         required_id = re.search(r"[0-9]+", request_text)
#         if required_id:
#             required_id = required_id[0]
#         if required_id and required_id in DATABASE["harvesters"]:
#             status = get_statuses_with_ids([required_id])[0]
#             response = response.replace("ID", required_id)
#             response = response.replace("STATUS", status)
#         else:
#             response = f"I can answer only about the following harvesters ids: " \
#                        f"{', '.join(DATABASE['harvesters'].keys())}."

#     return response


# def generate_response_from_db(intent, utterance):
#     global PREV_UPDATE_TIME
#     if time.time() - PREV_UPDATE_TIME >= 3600:
#         DATABASE, PREV_UPDATE_TIME = update_database()

#     response = ""
#     responses_collection = RESPONSES[intent]
#     if isinstance(responses_collection, list):
#         response = random.choice(responses_collection)
#     elif isinstance(responses_collection, dict):
#         required_statuses = responses_collection.get("required", {}).get("harvesters", "")
#         if len(required_statuses) == 0:
#             required_statuses = responses_collection.get("required", {}).get("rovers", "")
#             ids = get_ids_with_statuses(required_statuses, object="rover")
#         else:
#             ids = get_ids_with_statuses(required_statuses, object="harvester")

#         if len(required_statuses) == 0 or (len(required_statuses) > 0 and len(ids) > 0):
#             response = responses_collection["yes"]
#         else:
#             response = responses_collection["no"]

#     response = fill_harvesters_status_templates(response, utterance)

#     if intent == "not_relevant":
#         confidence = 0.5
#     else:
#         confidence = 1.0

#     return response, confidence


@app.route("/test", methods=["POST"])
def test():
    human_uttr = request.json["human_uttr"]

    # uttr_response, confidence = gobot.call(sentence)
    # response = gobot.generateNlg(uttr_response, DATABASE)

    return "Hello world"


# @app.route("/respond", methods=["POST"])
# def respond():
#     st_time = time.time()

#     dialogs = request.json["dialogs"]

#     responses = []
#     confidences = []

#     for dialog in dialogs:
#         sentence = dialog['human_utterances'][-1]['annotations'].get("spelling_preprocessing")
#         if sentence is None:
#             logger.warning('Not found spelling preprocessing annotation')
#             sentence = dialog['human_utterances'][-1]['text']
#         # intent = detect_intent(sentence)
#         # logger.info(f"Found intent {intent} in user request {sentence}")
#         # response, confidence = generate_response_from_db(intent, sentence)

#         uttr_response, confidence = gobot.call(sentence)
#         response = gobot.generateNlg(uttr_response, DATABASE)

#         responses.append(response)
#         confidences.append(confidence)

#     total_time = time.time() - st_time
#     logger.info(f"harvesters_maintenance_gobot_skill exec time = {total_time:.3f}s")
#     return jsonify(list(zip(responses, confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
