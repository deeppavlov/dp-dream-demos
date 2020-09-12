from encoder.params_model import model_embedding_size as speaker_embedding_size
from utils.argutils import print_args
from utils.modelutils import check_model_paths
from synthesizer.inference import Synthesizer
from encoder import inference as encoder
from vocoder import inference as vocoder
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import argparse
import torch
import sys
from audioread.exceptions import NoBackendError
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from scipy.io import wavfile

print("Preparing the encoder, the synthesizer and the vocoder...")
encoder.load_model(Path("encoder/saved_models/pretrained.pt"))
synthesizer = Synthesizer(Path("synthesizer/saved_models/logs-pretrained/taco_pretrained"), low_mem=False, seed=None)
vocoder.load_model(Path("vocoder/saved_models/pretrained/pretrained.pt"))

## Run a test
print("Testing your configuration with small inputs.")
# Forward an audio waveform of zeroes that lasts 1 second. Notice how we can get the encoder's
# sampling rate, which may differ.
# If you're unfamiliar with digital audio, know that it is encoded as an array of floats
# (or sometimes integers, but mostly floats in this projects) ranging from -1 to 1.
# The sampling rate is the number of values (samples) recorded per second, it is set to
# 16000 for the encoder. Creating an array of length <sampling_rate> will always correspond
# to an audio of 1 second.
print("\tTesting the encoder...")
encoder.embed_utterance(np.zeros(encoder.sampling_rate))

# Create a dummy embedding. You would normally use the embedding that encoder.embed_utterance
# returns, but here we're going to make one ourselves just for the sake of showing that it's
# possible.
embed = np.random.rand(speaker_embedding_size)
# Embeddings are L2-normalized (this isn't important here, but if you want to make your own
# embeddings it will be).
embed /= np.linalg.norm(embed)
# The synthesizer can handle multiple inputs with batching. Let's create another embedding to
# illustrate that
embeds = [embed, np.zeros(speaker_embedding_size)]
texts = ["test 1", "test 2"]
print("\tTesting the synthesizer... (loading the model will output a lot of text)")
mels = synthesizer.synthesize_spectrograms(texts, embeds)

# The vocoder synthesizes one waveform at a time, but it's more efficient for long ones. We
# can concatenate the mel spectrograms to a single one.
mel = np.concatenate(mels, axis=1)
# The vocoder can take a callback function to display the generation. More on that later. For
# now we'll simply hide it like this:
no_action = lambda *args: None
print("\tTesting the vocoder...")
# For the sake of making this test short, we'll pass a short target length. The target length
# is the length of the wav segments that are processed in parallel. E.g. for audio sampled
# at 16000 Hertz, a target length of 8000 means that the target audio will be cut in chunks of
# 0.5 seconds which will all be generated together. The parameters here are absurdly short, and
# that has a detrimental effect on the quality of the audio. The default parameters are
# recommended in general.
vocoder.infer_waveform(mel, target=200, overlap=50, progress_callback=no_action)

print("All test passed! You can now synthesize speech.\n\n")

## Interactive speech generation
print("This is a GUI-less example of interface to SV2TTS. The purpose of this script is to "
      "show how you can interface this project easily with your own. See the source code for "
      "an explanation of what is happening.\n")

print("Interactive generation loop")


def load_embedding(file):
    original_wav, sampling_rate = librosa.load(file)
    preprocessed_wav = encoder.preprocess_wav(original_wav, sampling_rate)
    print("Loaded file succesfully")
    emb = encoder.embed_utterance(preprocessed_wav)
    return emb


embed = load_embedding('gerty_sample.wav')


app = FastAPI()

@app.post("/sample")
async def create_upload_file(file: UploadFile = File(...)):
    global embed
    embed = load_embedding(file.file)
    return 200

@app.post("/tts")
async def create_upload_file(text: str):
    texts = [text]
    embeds = [embed]
    # If you know what the attention layer alignments are, you can retrieve them here by
    # passing return_alignments=True
    specs = synthesizer.synthesize_spectrograms(texts, embeds)
    spec = specs[0]
    print("Created the mel spectrogram")

    ## Generating the waveform
    print("Synthesizing the waveform:")

    # Synthesizing the waveform is fairly straightforward. Remember that the longer the
    # spectrogram, the more time-efficient the vocoder.
    generated_wav = vocoder.infer_waveform(spec)

    ## Post-generation
    # There's a bug with sounddevice that makes the audio cut one second earlier, so we
    # pad it.
    generated_wav = np.pad(generated_wav, (0, synthesizer.sample_rate), mode="constant")

    # Trim excess silences to compensate for gaps in spectrograms (issue #53)
    generated_wav = encoder.preprocess_wav(generated_wav)

    # Save it on the disk
    output = BytesIO()
    wavfile.write(output, synthesizer.sample_rate, generated_wav.astype(np.float32))
    return StreamingResponse(output, media_type='audio/x-wav')