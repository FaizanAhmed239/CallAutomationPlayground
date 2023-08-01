import pandas as pd
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Model
from tensorflow.keras.models import load_model
import os
import pickle
import numpy as np
import os
import re
import tempfile
import flask
from flask import request
from flask_cors import CORS
import whisper
import pygame


app = flask.Flask(__name__)
app.debug = True
CORS(app)

# Global variables to store the loaded model and tokenizer
loaded_model = None
loaded_tokenizer = None

def load_model_and_tokenizer():
    global loaded_model, loaded_tokenizer

    if loaded_model is None and loaded_tokenizer is None:
        # Load the model from the file
        loaded_model = load_model('./my_model_2023-07-26_accuracy_0.941_loss_0.314_10.h5')
        # Load the saved tokenizer
        with open('./tokenizer_2023-07-26_accuracy_0.941_loss_0.314_10.pkl', 'rb') as f:
            loaded_tokenizer = pickle.load(f)


def predict_label(input_string, tokenizer, model):

    # Tokenize the new input string and convert it into a sequence of indices
    new_input_tokens = tokenizer.texts_to_sequences([input_string])

    # Find the max_sequence_length from the new input tokens (assuming new_input_tokens is your list of input sequences)
    # max_sequence_length = max(len(seq) for seq in new_input_tokens)
    max_sequence_length = 10

    # Pad the sequence to match the same length as the sequences used during training
    new_input_sequence = pad_sequences(new_input_tokens, maxlen=max_sequence_length, padding='post')

    # Add an extra dimension to the input data (samples, timesteps, features)
    new_input_sequence = new_input_sequence.reshape(-1, max_sequence_length, 1)

    # Make predictions using the trained model
    predicted_labels = model.predict(new_input_sequence)

    # Convert the predicted one-hot encoded label back to the original ID
    predicted_id = int(np.argmax(predicted_labels, axis=-1)[0])

    print(f"Predicted ID for '{input_string}': {predicted_id}\n\n")
    return predicted_id


# Call the function to load the model and tokenizer when the script starts
load_model_and_tokenizer()

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if request.method == 'POST':
        language = request.form['language']
        model = request.form['model_size']

        # there are no english models for large
        if model != 'large' and language == 'english':
            model = model + '.en'
        audio_model = whisper.load_model(model)

        temp_dir = tempfile.mkdtemp()
        save_path = os.path.join(temp_dir, 'temp.wav')

        print(save_path)

        wav_file = request.files['audio_data']
        wav_file.save(save_path)

        if language == 'english':
            result = audio_model.transcribe(save_path, language='english')
        else:
            result = audio_model.transcribe(save_path)
        
        if result and result['text'] != '':
            print(result)
            processed_text = punctuation_remover(result['text'])
            processed_text = modify_consecutive_words(processed_text)
            print (processed_text+'<<<<<<')

            predicted_label= predict_label(processed_text,loaded_tokenizer,loaded_model)
            print(predicted_label)

            # Play the corresponding audio file
            play_audio(predicted_label)
        

        return result['text']
    else:
        return "This endpoint only processes POST wav blob"


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
    
def play_audio(predicted_id):
    # Assuming the audio files are located in the 'audio_files' directory
    audio_file_path = os.path.join('./audio_files', f'{predicted_id}.mp3')
    # print(audio_file_path)
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()

    print("Playing Audio")
    
    # Wait for the audio to finish playing
    while pygame.mixer.music.get_busy():
        continue

