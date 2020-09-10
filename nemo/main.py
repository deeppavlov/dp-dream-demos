import requests
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse

from deeppavlov import build_model, configs

app = FastAPI()
asr = build_model(configs.nemo.asr)
tts = build_model('tts.json')


@app.post("/asr")
async def create_upload_file(user_id: str, file: UploadFile = File(...)):
    transcript = asr([file.file])[0]
    print(f'transcription is "{transcript}"')
    post_response = requests.post('http://agent:4242', json={"user_id": user_id, "payload": transcript})
    response = post_response.json()['response']
    print(f'response is "{response}"')
    audio_response = tts([response])[0]
    return StreamingResponse(audio_response, media_type='audio/x-wav', headers={'response': response,
                                                                                'transcript': transcript})
