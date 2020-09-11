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


def base_skill_formatter(payload: Dict) -> Dict:
    return [{"text": payload[0], "confidence": payload[1]}]

def simple_formatter_service(payload: List):
    '''
    Used by: punct_dialogs_formatter, intent_catcher_formatter, asr_formatter,
    sent_rewrite_formatter, sent_segm_formatter, base_skill_selector_formatter
    '''
    logging.info('answer ' + str(payload))
    return payload

def preproc_last_human_utt_dialog(dialog: Dict) -> Dict:
    # Used by: sentseg over human uttrs
    return [{'sentences': [dialog['human_utterances'][-1]['annotations']["spelling_preprocessing"]]}]

def preproc_last_bot_utt_dialog(dialog: Dict) -> Dict:
    # Used by: sentseg over human uttrs
    return [{'sentences': [dialog['bot_utterances'][-1]['annotations']["spelling_preprocessing"]]}]

def cobot_classifiers_formatter_service(payload: List):
    # Used by: cobot_classifiers_formatter, sentiment_formatter
    if len(payload) == 3:
        return {"text": payload[0],
                "confidence": payload[1],
                "is_blacklisted": payload[2]}
    elif len(payload) == 2:
        return {"text": payload[0],
                "confidence": payload[1]}
    elif len(payload) == 1:
        return {"text": payload[0]}
    elif len(payload) == 0:
        return {"text": []}

def hypotheses_list(dialog: Dict) -> Dict:
    hypotheses = dialog["utterances"][-1]["hypotheses"]
    hypots = [h["text"] for h in hypotheses]
    return [{'sentences': hypots}]

def simple_formatter_annotator(payload: List):
    '''
    Used by: punct_dialogs_formatter, intent_catcher_formatter, asr_formatter,
    sent_rewrite_formatter, sent_segm_formatter, base_skill_selector_formatter
    '''
    return {'batch': payload}