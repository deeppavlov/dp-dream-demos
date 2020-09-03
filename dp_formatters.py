from typing import Dict, List
import logging
from copy import deepcopy
#from common.universal_templates import if_lets_chat_about_topic

logger = logging.getLogger(__name__)

LAST_N_TURNS = 5  # number of turns to consider in annotator/skill.


def last_utt_dialog(dialog: Dict) -> Dict:
    # Used by: dp_toxic_formatter, sent_segm_formatter, tfidf_formatter, sentiment_classification
    return [{'sentences': [dialog['utterances'][-1]['text']]}]


def base_formatter_service(payload: Dict) -> Dict:
    '''
    Used by: dummy_skill_formatter, intent_responder_formatter, transfertransfo_formatter,
    aiml_formatter, alice_formatter, tfidf_formatter
    '''
    return {"text": payload[0], "confidence": payload[1], "skill_name": ""}
