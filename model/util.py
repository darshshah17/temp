import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
import gensim.downloader as api

# Load pre-trained Word2Vec model
word2vec = api.load("word2vec-google-news-300")  # A commonly used Word2Vec model with 300 dimensions

# Load and preprocess data
input_file = "trainingData.txt"

x = []
y = []

with open(input_file, "r") as file:
    for line in file:
        sentence, danceability, energy = line.strip().rsplit(",", 2)
        
        # Convert sentence to Word2Vec embedding by summing word vectors
        sentence_vector = np.zeros(300)  # Adjust to match Word2Vec dimensions (300 in this example)
        words = sentence.split()
        valid_words = [word for word in words if word in word2vec]
        if valid_words:
            sentence_vector = np.sum([word2vec[word] for word in valid_words], axis=0)
        
        x.append(sentence_vector)
        y.append([float(danceability), float(energy)])

# Convert lists to numpy arrays
x = np.array(x)
y = np.array(y)

# Train-test split
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

# Model creation
def create_model(input_dim):
    return tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.Flatten(name='layers_flatten'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(2, activation='linear'),  # Output for danceability and energy
    ])

# Adjust input_dim to match the embedding dimension used (300 here)
model = create_model(input_dim=300)
model.compile(optimizer='adam', loss='mean_absolute_error')

# Model training
model.fit(
    x=x_train, 
    y=y_train, 
    epochs=50, 
    validation_data=(x_test, y_test),
)

# Save the model
model.save("sentimentAnalysisModel.keras")  # Saves the model as a .keras file (newer version of .h5)
