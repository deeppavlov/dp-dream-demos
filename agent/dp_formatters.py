import logging
from typing import Dict, List

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


def entity_linking_formatter(payload: List):
    response = []
    for entity_name, wikidata_ids, id_types in zip(*payload):
        item = {
            'entity_name': entity_name,
            'wikidata_ids': [
                {
                    "id": id,
                    "instance_of": instance_of
                }
                for id, instance_of in zip(wikidata_ids, id_types)
            ]
        }
        response.append(item)
    return response


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


def programy_formatter_dialog(dialog: Dict) -> List:
    return [{'sentences_batch': [[u['text'] for u in dialog['utterances'][-5:]]]}]


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


def replace_with_annotated_utterances(dialog, mode="punct_sent"):
    if mode == "punct_sent":
        for utt in dialog['utterances']:
            utt['text'] = utt['annotations']['sentseg']['punct_sent']
        for utt in dialog['human_utterances']:
            utt['text'] = utt['annotations']['sentseg']['punct_sent']
    elif mode == "segments":
        for utt in dialog['utterances']:
            utt['text'] = utt['annotations']['sentseg']['segments']
        for utt in dialog['human_utterances']:
            utt['text'] = utt['annotations']['sentseg']['segments']
        for utt in dialog['bot_utterances']:
            utt['text'] = utt['annotations']['sentseg']['segments']
    elif mode == "modified_sents":
        for utt in dialog['utterances']:
            utt['text'] = utt['annotations']['sentrewrite']['modified_sents'][-1]
        for utt in dialog['human_utterances']:
            utt['text'] = utt['annotations']['sentrewrite']['modified_sents'][-1]
    return dialog


def get_last_n_turns(dialog: Dict, bot_last_turns=None, human_last_turns=None, total_last_turns=None):
    bot_last_turns = bot_last_turns or LAST_N_TURNS
    human_last_turns = human_last_turns or bot_last_turns + 1
    total_last_turns = total_last_turns or bot_last_turns * 2 + 1
    dialog["utterances"] = dialog["utterances"][-total_last_turns:]
    dialog["human_utterances"] = dialog["human_utterances"][-human_last_turns:]
    dialog["bot_utterances"] = dialog["bot_utterances"][-bot_last_turns:]
    return dialog


def utt_sentseg_punct_dialog(dialog: Dict):
    '''
    Used by: skill_with_attributes_formatter; punct_dialogs_formatter,
    dummy_skill_formatter, base_response_selector_formatter
    '''
    dialog = get_last_n_turns(dialog)
    dialog = replace_with_annotated_utterances(dialog, mode="punct_sent")
    return [{'dialogs': [dialog]}]


def ner_formatter_dialog(dialog: Dict):
    # Used by: ner_formatter
    return [{'last_utterances': [dialog['utterances'][-1]['annotations']['sentseg']['segments']]}]


def dp_toxic_formatter_service(payload: List):
    # Used by: dp_toxic_formatter
    return payload[0]


def last_utt_sentseg_segments_dialog(dialog: Dict):
    # Used by: intent_catcher_formatter
    return [{'sentences': [dialog['utterances'][-1]['annotations']['sentseg']['segments']]}]


def sent_rewrite_formatter_dialog(dialog: Dict) -> Dict:
    print('one', flush=True)
    # Used by: sent_rewrite_formatter
    dialog = get_last_n_turns(dialog)
    utterances_histories = []
    annotation_histories = []
    print('two', flush=True)
    for utt in dialog['utterances']:
        annotation_histories.append(utt['annotations'])
        utterances_histories.append(utt['annotations']['sentseg']['segments'])
    return [{
        'utterances_histories': [utterances_histories],
        'annotation_histories': [annotation_histories]
    }]


def ner_formatter_last_bot_dialog(dialog: Dict):
    return [{'last_utterances': [dialog['bot_utterances'][-1]['annotations']['sentseg']['segments']]}]


def sent_rewrite_formatter_w_o_last_dialog(dialog: Dict) -> Dict:
    dialog = get_last_n_turns(dialog, LAST_N_TURNS + 1)
    utterances_histories = []
    annotation_histories = []
    for utt in dialog['utterances'][:-1]:
        annotation_histories.append(utt['annotations'])
        utterances_histories.append(utt['annotations']['sentseg']['segments'])
    return [{
        'utterances_histories': [utterances_histories],
        'annotation_histories': [annotation_histories]
    }]


def last_bot_utt_dialog(dialog: Dict) -> Dict:
    return [{'sentences': [dialog['bot_utterances'][-1]['text']]}]
