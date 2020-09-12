import re

import requests
from deeppavlov import build_model, configs
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from num2words import num2words

app = FastAPI()
asr = build_model(configs.nemo.asr)
tts = build_model('tts.json')


@app.post("/asr")
async def create_upload_file(user_id: str, file: UploadFile = File(...)):
    transcript = asr([file.file])[0]
    print(f'transcription is "{transcript}"')
    post_response = requests.post('http://agent:4242', json={"user_id": user_id, "payload": transcript})
    response_payload = post_response.json()
    response = response_payload['response']
    print(f'response is "{response}"')
    response = re.sub(r'([0-9]+)', lambda x: num2words(x.group(0)), response)
    response_payload['response'] = response
    return JSONResponse(content=response_payload, headers={'transcript': transcript})
    audio_response = tts([response])[0]

    active_skill = response_payload['active_skill']
    emotion = 'none'
    for skill_dict in response_payload['debug_output']:
        if skill_dict['skill_name'] == active_skill:
            emotions = skill_dict['annotations']['emotion_classification'][0]
            emotion = max(emotions, key=emotions.get)

    return StreamingResponse(audio_response, media_type='audio/x-wav', headers={'response': response,
                                                                                'transcript': transcript,
                                                                                'emotion': emotion})
