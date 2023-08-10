import pandas as pd
import keras
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Model
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Input
import os
import pickle
import numpy as np
import os
import re
import tempfile
import flask
from flask import request
from flask_cors import CORS
from flask import jsonify
import whisper
from transformers import TFBertForSequenceClassification, BertTokenizer


app = flask.Flask(__name__)
app.debug = True
CORS(app)

# Global variables to store the loaded model and tokenizer
loaded_model = None
loaded_tokenizer = None
whisper_model = None


def load_model_and_tokenizer():
    global loaded_model, loaded_tokenizer, whisper_model

    whisper_model = whisper.load_model("large")

    if loaded_model is None and loaded_tokenizer is None:
        model_dir = "model_details/"
        loaded_model = TFBertForSequenceClassification.from_pretrained(
            model_dir)
        # loaded_model = keras.models.load_model("tf_model.h5")
        loaded_tokenizer = BertTokenizer.from_pretrained(model_dir)


def predict_label(input_string, tokenizer, model):

    inputs = tokenizer.encode_plus(
        input_string, add_special_tokens=True, return_tensors="tf")
    predictions = model(inputs["input_ids"])[0]
    predicted_class_index = tf.argmax(predictions, axis=1).numpy()[0]
    print("Predicted Response Audio:", predicted_class_index)

    return predicted_class_index


# Call the function to load the model and tokenizer when the script starts
load_model_and_tokenizer()


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if request.method == 'POST':

        temp_dir = tempfile.mkdtemp()
        save_path = os.path.join(temp_dir, 'temp.wav')

        wav_file = request.files['audio_data']
        wav_file.save(save_path)

        result = whisper_model.transcribe(
            save_path, language='english')

        if result and result['text'] != '':
            processed_text = punctuation_remover(result['text'])
            processed_text = modify_consecutive_words(processed_text)
            print(result)
            print("Processed Text:" + processed_text)

            predicted_label = int(predict_label(
                result['text'], loaded_tokenizer, loaded_model))
            print(predicted_label)

            return jsonify({'text': result['text'], 'predicted_id': predicted_label})

        else:
            print("This endpoint only processes POST wav blob")
            return 'No audio to stream', 204


def punctuation_remover(text):
    # Split text into tokens
    tokens = re.findall(r'\w+', text)
    string = ' '.join(tokens).upper()

    return string


def modify_consecutive_words(input_string):
    # Find consecutive occurrences of words (2 or more times)
    pattern = r'\b(\w+)(?:\s+\1)+\b'
    modified_string = re.sub(pattern, r'\1', input_string)
    return modified_string


@app.route('/audio/<predicted_id>', methods=['GET'])
def stream_audio(predicted_id):
    audio_file_path = os.path.join(
        './audio_files', f'{predicted_id}.mp3')

    print(audio_file_path)
    print(f"Streaming Audio {predicted_id}.mp3")

    return flask.send_file(audio_file_path, mimetype='audio/mp3')
