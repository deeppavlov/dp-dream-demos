#!/usr/bin/env python

import logging
import numpy as np
import time

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialogs = request.json["dialogs"]
    
    selected_skill_names = []
    selected_responses = []
    selected_confidences = []

    for dialog in dialogs:
        skill_name, response, confidence = None, None, None
        hypotheses = dialog["utterances"][-1]["hypotheses"]
        if hypotheses:
            skill_name = hypotheses[0]["skill_name"]
            response = hypotheses[0]["text"]
            confidence = hypotheses[0]["confidence"]
        
        selected_skill_names.append(skill_name)
        selected_responses.append(response)
        selected_confidences.append(confidence)
    
    total_time = time.time() - st_time
    logger.info(f"trivial_response_selector exec time = {total_time:.3f}s")
    return jsonify(list(zip(selected_skill_names, selected_responses, selected_confidences)))


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
