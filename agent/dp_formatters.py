import logging
from copy import deepcopy
from typing import Dict, List
from universal_templates import if_lets_chat_about_topic
from utils import service_intents

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


def is_bot_uttr_repeated_or_misheard(utt):
    is_asr = utt.get("active_skill", "") == "misheard_asr" and utt.get("confidence", 0.) == 1.
    is_repeated = "#+#repeat" in utt.get("text", "")
    if is_asr or is_repeated:
        return True
    else:
        return False


def is_human_uttr_repeat_request_or_misheard(utt):
    is_repeat_request = utt.get('annotations', {}).get("intent_catcher", {}).get("repeat", {}).get("detected", 0) == 1
    is_low_asr_conf = utt.get('annotations', {}).get('asr', {}).get('asr_confidence', "") == 'very_low'
    if is_low_asr_conf or is_repeat_request:
        return True
    else:
        return False


def last_n_human_utt_dialog_formatter(dialog: Dict, last_n_utts: int, only_last_sentence: bool = False) -> List:
    """
    Args:
        dialog (Dict): full dialog state
        last_n_utts (int): how many last user utterances to take
        only_last_sentence (bool, optional): take only last sentence in each utterance. Defaults to False.
    """
    if len(dialog["human_utterances"]) <= last_n_utts and \
            not if_lets_chat_about_topic(dialog["utterances"][0]["text"].lower()):
        # in all cases when not particular topic, convert first phrase in the dialog to `hello!`
        dialog["utterances"][0]['annotations']['sentseg']['punct_sent'] = "hello!"
    human_utts = []
    detected_intents = []
    for utt in dialog['utterances']:
        if utt['user']['user_type'] == 'human':
            sentseg_ann = utt['annotations']['sentseg']
            if only_last_sentence:
                text = sentseg_ann['segments'][-1] if len(sentseg_ann['segments']) > 0 else ''
            else:
                text = sentseg_ann['punct_sent']
            human_utts += [text]
            detected_intents += [[intent for intent, value in utt['annotations'].get('intent_catcher', {}).items()
                                 if value['detected']]]
    return [{'sentences_batch': [human_utts[-last_n_utts:]], 'intents': [detected_intents[-last_n_utts:]]}]


def remove_clarification_turns_from_dialog(dialog):
    new_dialog = deepcopy(dialog)
    new_dialog["utterances"] = []
    dialog_length = len(dialog["utterances"])

    for i, utt in enumerate(dialog["utterances"]):
        if utt['user']['user_type'] == 'human':
            new_dialog["utterances"].append(utt)
        elif utt['user']['user_type'] == 'bot':
            if 0 < i < dialog_length - 1 and is_bot_uttr_repeated_or_misheard(utt) and \
                    is_human_uttr_repeat_request_or_misheard(dialog["utterances"][i - 1]):
                new_dialog["utterances"] = new_dialog["utterances"][:-1]
            else:
                new_dialog["utterances"].append(utt)

    new_dialog["human_utterances"] = []
    new_dialog["bot_utterances"] = []

    for utt in new_dialog["utterances"]:
        if utt['user']['user_type'] == 'human':
            new_dialog["human_utterances"].append(utt)
        elif utt['user']['user_type'] == 'bot':
            new_dialog["bot_utterances"].append(utt)

    return new_dialog


def programy_formatter_dialog(dialog: Dict) -> List:
    # Used by: program_y, program_y_dangerous, program_y_wide
    dialog = remove_clarification_turns_from_dialog(dialog)
    return [{'sentences_batch': [[u['text'] for u in dialog['utterances'][-5:]]]}]
    dialog = last_n_human_utt_dialog_formatter(dialog, last_n_utts=5)[0]
    sentences = dialog['sentences_batch'][0]
    intents = dialog['intents'][0]

    # modify sentences with yes/no intents to yes/no phrase
    # todo: sent may contain multiple sentence, logic here could be improved
    prioritized_intents = service_intents - {'yes', 'no'}
    for i, (sent, ints) in enumerate(zip(sentences, intents)):
        ints = set(ints)
        if '?' not in sent and len(ints & prioritized_intents) == 0:
            if 'yes' in ints:
                sentences[i] = 'yes.'
            elif 'no' in ints:
                sentences[i] = 'no.'
    return [{'sentences_batch': [sentences]}]


def skill_with_attributes_formatter_service(payload: Dict):
    """
    Formatter should use `"state_manager_method": "add_hypothesis"` in config!!!
    Because it returns list of hypothesis even if the payload is returned for one sample!

    Args:
        payload: if one sample, list of the following structure:
            (text, confidence, ^human_attributes, ^bot_attributes, attributes) [by ^ marked optional elements]
                if several hypothesis, list of lists of the above structure

    Returns:
        list of dictionaries of the following structure:
            {"text": text, "confidence": confidence_value,
             ^"human_attributes": {}, ^"bot_attributes": {},
             **attributes},
             by ^ marked optional elements
    """
    # Used by: book_skill_formatter, skill_with_attributes_formatter, news_skill, meta_script_skill, dummy_skill
    if isinstance(payload[0], list) and isinstance(payload[1], list):
        result = [{"text": hyp[0],
                   "confidence": hyp[1]} for hyp in zip(*payload)]
    else:
        result = [{"text": payload[0],
                   "confidence": payload[1]}]

    if len(payload) >= 4:
        if isinstance(payload[2], dict) and isinstance(payload[3], dict):
            result[0]["human_attributes"] = payload[2]
            result[0]["bot_attributes"] = payload[3]
        elif isinstance(payload[2], list) and isinstance(payload[3], list):
            for i, hyp in enumerate(zip(*payload)):
                result[i]["human_attributes"] = hyp[2]
                result[i]["bot_attributes"] = hyp[3]

    if len(payload) == 3 or len(payload) == 5:
        if isinstance(payload[-1], dict):
            for key in payload[-1]:
                result[0][key] = payload[-1][key]
        elif isinstance(payload[-1], list):
            for i, hyp in enumerate(zip(*payload)):
                for key in hyp[-1]:
                    result[i][key] = hyp[-1][key]

    return result
