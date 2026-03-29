import pandas as pd
import numpy as np
import nltk
import string
import json
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

# -------------------- NLTK Downloads --------------------
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')

lemmatizer = WordNetLemmatizer()

# -------------------- Load Dataset --------------------
df = pd.read_csv('moonchat_data.csv', encoding='latin-1')

# -------------------- Preprocess Text --------------------
def preprocess(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.word_tokenize(text)
    return [lemmatizer.lemmatize(token) for token in tokens]

# -------------------- Build Vocabulary & Classes --------------------
words = []
classes = []
documents = []

for idx, row in df.iterrows():
    tokenized = preprocess(row['query'])
    words.extend(tokenized)
    documents.append((tokenized, row['intent']))
    if row['intent'] not in classes:
        classes.append(row['intent'])

words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

print(f"Vocabulary size: {len(words)}, Number of Intents: {len(classes)}")

# -------------------- Create Training Data --------------------
training = []
output_empty = [0] * len(classes)

for doc in documents:
    bag = [1 if w in doc[0] else 0 for w in words]  # bag-of-words
    output_row = output_empty[:]
    output_row[classes.index(doc[1])] = 1
    training.append([bag, output_row])

# Shuffle and convert to numpy arrays
np.random.shuffle(training)
training = np.array(training, dtype=object)

X = np.array(list(training[:, 0]))
y = np.array(list(training[:, 1]))

# -------------------- Split into Train/Test --------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# -------------------- Build Neural Network --------------------
model = Sequential()
model.add(Dense(128, input_shape=(len(X[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(y[0]), activation='softmax'))

model.compile(loss='categorical_crossentropy', optimizer=Adam(0.001), metrics=['accuracy'])

# -------------------- Train Model --------------------
history = model.fit(
    X_train, y_train,
    epochs=200,
    batch_size=8,
    validation_data=(X_test, y_test)
)

# -------------------- Save Model & Metadata --------------------
model.save("moonchat_model.h5")

with open('moonchat_words.json', 'w') as f:
    json.dump(words, f)

with open('moonchat_classes.json', 'w') as f:
    json.dump(classes, f)

print("Model trained and saved successfully!")