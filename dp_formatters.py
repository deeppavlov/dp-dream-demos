from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

LAST_N_TURNS = 5  # number of turns to consider in annotator/skill.


def last_utt_dialog(dialog: Dict) -> Dict:
    return [{'sentences': [dialog['utterances'][-1]['text']]}]


def base_formatter_service(payload: Dict) -> Dict:
    """
    Used by: dummy_skill_formatter, intent_responder_formatter, transfertransfo_formatter,
             aiml_formatter, alice_formatter, tfidf_formatter
    """
    return {"text": payload[0], "confidence": payload[1], "skill_name": ""}


def base_response_selector_formatter_service(payload: List) -> Dict:
    if len(payload) == 3:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2]}
    elif len(payload) == 5:
        return {"skill_name": payload[0], "text": payload[1], "confidence": payload[2],
                "human_attributes": payload[3], "bot_attributes": payload[4]}


def full_dialog(dialog: Dict):
    return [{'dialogs': [dialog]}]
