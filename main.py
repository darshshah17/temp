from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from transformers import pipeline
import logging
import tempfile
import numpy as np
import tensorflow as tf
import gensim.downloader as api

# Load the custom model
loaded_model = tf.keras.models.load_model("model/sentimentAnalysisModel.keras")

# Load the Word2Vec model
word2vec = api.load("word2vec-google-news-300")


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

# Allow cross-origin requests from localhost:3000
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

# Set up OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = "http://localhost:5001/callback"

if not openai_api_key or not spotify_client_id or not spotify_client_secret:
    raise ValueError("Environment variables not properly set. Check OPENAI_API_KEY, SPOTIFY_CLIENT_ID, and SPOTIFY_CLIENT_SECRET.")

client = OpenAI(api_key=openai_api_key)

# Load tokenizer and model
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
model = RobertaForSequenceClassification.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment')

# Create a sentiment analysis pipeline
sentiment_pipeline = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

ALLOWED_EXTENSIONS = {'m4a', 'wav', 'mp3'}
spotify_access_token = None  # Global variable for storing the access token

def preprocess_sentence(sentence, word2vec):
    sentence_vector = np.zeros(300)  # Ensure this matches the Word2Vec dimensions
    words = sentence.split()
    valid_words = [word for word in words if word in word2vec]
    if valid_words:
        sentence_vector = np.sum([word2vec[word] for word in valid_words], axis=0)
    return sentence_vector

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return jsonify({"status": "Running", "message": "Welcome to the top secret API :)"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/login')
def login():
    """Redirects the user to Spotify for authorization."""
    auth_url = (
        f"https://accounts.spotify.com/authorize?response_type=token"
        f"&client_id={spotify_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=playlist-read-private"
    )
    return redirect(auth_url)


@app.route('/callback', methods=['POST'])
def callback():
    """Handles the Spotify authorization callback."""
    code = request.json.get('code')
    
    if not code:
        return jsonify({'error': 'Authorization code not provided'}), 400

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": spotify_client_id,
        "client_secret": spotify_client_secret
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        token_data = response.json()
        
        # Store the access token in the session
        session['spotify_access_token'] = token_data.get('access_token')
        logger.debug("Access token stored in session")
        
        return jsonify({'message': 'Spotify access token obtained successfully!'})
    except requests.exceptions.RequestException as e:
        logger.error(f"Spotify token exchange failed: {str(e)}")
        return jsonify({'error': 'Failed to obtain Spotify access token.'}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    global spotify_access_token
    logger.info("Starting file upload process")
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format'}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        file.save(temp_file.name)
        
        with open(temp_file.name, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            transcript = str(response)

        os.unlink(temp_file.name)

    # Emotion Analysis (Valence Calculation)
    result = sentiment_pipeline(transcript)
    label = result[0]['label']
    score = result[0]['score']

    logger.info(f"Emotion analysis complete: {label}, {score}")

    if label == 'LABEL_0':
        valence = (1 - score) * 0.5  
    elif label == 'LABEL_1': 
        valence = 0.4 + (score * 0.2)
    elif label == 'LABEL_2': 
        valence = 0.5 + (score * 0.5)  

    # Danceability and Energy Prediction
    sentence_vector = preprocess_sentence(transcript, word2vec)
    sentence_vector = np.expand_dims(sentence_vector, axis=0)  # Reshape for model input
    predicted_scores = loaded_model.predict(sentence_vector)
    danceability, energy = predicted_scores[0]
    # logger.info(f"Danceability: {danceability}, Energy: {energy}")
    

    # Store valence in session if needed for other purposes
    session['valence'] = valence

    # Calculate finalScore with weighted sum
    # Adjust weights as necessary based on importance
    audioFinalScore = (0.5 * valence) + (0.3 * danceability) + (0.2 * energy)
    # audioFinalScore = valence

    return jsonify({
        'transcription': transcript,
        'label': label,
        'score': float(score),
        'valence': float(valence),
        'danceability': float(danceability),
        'energy': float(energy),
        'audioFinalScore': float(audioFinalScore)
    })


@app.route('/analyze-tracks', methods=['POST'])
def analyze_tracks():
    data = request.json
    tracks = data.get('tracks', [])
    input_final_score = data.get('input_final_score')  # Now we get audioFinalScore as input_final_score

    logger.info(f"Received {len(tracks)} tracks for analysis.")
    logger.info(f"Input final score: {input_final_score}")

    if input_final_score is None:
        logger.error("Input final score not provided")
        return jsonify({'error': 'Input final score is required.'}), 400

    if not tracks:
        logger.error("No tracks received in the request")
        return jsonify({'error': 'No tracks to analyze.'}), 400

    try:
        updated_tracks = []
        track_ids = [track['id'] for track in tracks]
        
        # Fetch audio features for each batch of tracks
        for i in range(0, len(track_ids), 100):
            batch_ids = track_ids[i:i + 100]
            features = fetch_audio_features(batch_ids, request.headers.get('Authorization').split(' ')[1])

            logger.info(f"Fetched {len(features)} audio features for batch {i // 100 + 1}")

            for track, feature in zip(tracks[i:i + 100], features):
                if feature:
                    track_valence = feature.get('valence', 0)
                    track_danceability = feature.get('danceability', 0)
                    track_energy = feature.get('energy', 0)

                    # Calculate trackFinalScore
                    trackFinalScore = (0.5 * track_valence) + (0.3 * track_danceability) + (0.2 * track_energy)
                    # trackFinalScore = track_valence
                    
                    # Calculate closeness based on trackFinalScore and input_final_score
                    track['valence'] = track_valence
                    track['danceability'] = track_danceability
                    track['energy'] = track_energy
                    track['trackFinalScore'] = trackFinalScore
                    track['closeness'] = abs(trackFinalScore - input_final_score)
                    
                    updated_tracks.append(track)

        updated_tracks.sort(key=lambda t: t['closeness'])
        
        return jsonify({'tracks': updated_tracks})
    except Exception as e:
        logger.error(f"Error analyzing tracks: {e}")
        return jsonify({'error': 'An error occurred while analyzing tracks.'}), 500

def fetch_audio_features(track_ids, access_token):
    try:
        url = 'https://api.spotify.com/v1/audio-features'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        params = {
            'ids': ','.join(track_ids)
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        features = data.get('audio_features', [])
        logger.info(f"Fetched audio features: {len(features)} items")  # Log number of features fetched
        return features
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching audio features: {e}")
        return []



def get_spotify_recommendations(valence):
    return valence
    # """Fetches Spotify song recommendations based on valence."""
    # access_token = session.get('spotify_access_token')

    # if not access_token:
    #     logger.error("No Spotify access token found in session")
    #     return {'error': 'Spotify access token not found. Please login to Spotify first.'}

    # url = "https://api.spotify.com/v1/recommendations"
    # headers = {
    #     "Authorization": f"Bearer {access_token}"
    # }
    # params = {
    # }

    # try:
    #     response = requests.get(url, headers=headers, params=params)
    #     response.raise_for_status()
    #     data = response.json()
    #     tracks = [{'name': track['name'], 'artist': track['artists'][0]['name']} for track in data.get('tracks', [])]
    #     return tracks
    # except requests.exceptions.RequestException as e:
    #     logger.error(f"Spotify API error: {str(e)}")
    #     return {'error': 'Failed to fetch recommendations from Spotify.'}

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be running on http://localhost:5001")
    print("Make sure your .env file contains OPENAI_API_KEY, SPOTIFY_CLIENT_ID, and SPOTIFY_CLIENT_SECRET")
    app.run(host='0.0.0.0', port=5001, debug=True)