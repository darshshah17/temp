import numpy as np
import tensorflow as tf
import gensim.downloader as api

# Load the pre-trained model
loaded_model = tf.keras.models.load_model("sentimentAnalysisModel.keras")

# Load Word2Vec model
word2vec = api.load("word2vec-google-news-300")  # Ensure the same Word2Vec model is loaded

# Preprocess function
def preprocess_sentence(sentence, word2vec):
    sentence_vector = np.zeros(300)  # Match the Word2Vec dimensions
    words = sentence.split()
    valid_words = [word for word in words if word in word2vec]
    if valid_words:
        sentence_vector = np.sum([word2vec[word] for word in valid_words], axis=0)
    return sentence_vector

# Example usage
sentence = "I'm feeling ecstatic about this party."
sentence_vector = preprocess_sentence(sentence, word2vec)
sentence_vector = np.expand_dims(sentence_vector, axis=0)  # Reshape for model input

# Make predictions with the loaded model
predicted_scores = loaded_model.predict(sentence_vector)
danceability, energy = predicted_scores[0]
print(f"Danceability: {danceability}, Energy: {energy}")
