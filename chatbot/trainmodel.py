"""
MoonChat Model Training Script — Advanced TF-IDF + Neural Network
Features:
  - TF-IDF Vectorization with Unigrams and Bigrams
  - Deeper Sequential model with BatchNormalization
  - Stratified splitting & Class Weights
  - Early Stopping and Reduced LR on plateau
"""
import pandas as pd
import numpy as np
import json
import os
import sys
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# -------------------- Add Project Root to Path --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import custom preprocessing
try:
    from chatbot.nlp_utils import preprocess_text
except ImportError:
    from nlp_utils import preprocess_text

# -------------------- Load Dataset --------------------
# Priority: Final > Cleaned > Expanded > Original
# Specifically use the final data file
data_path = os.path.join(BASE_DIR, 'moonchat_data_final.csv')
if not os.path.exists(data_path):
    # Fallback to others if final is missing for some reason
    data_files = ['moonchat_data_cleaned.csv', 'moonchat_data_expanded.csv', 'moonchat_data.csv']
    for f in data_files:
        temp_path = os.path.join(BASE_DIR, f)
        if os.path.exists(temp_path):
            data_path = temp_path
            break

if not data_path:
    raise FileNotFoundError("Could not find any training data CSV in the chatbot directory.")

print(f"Loading data from: {data_path}")
df = pd.read_csv(data_path, encoding='utf-8')
print(f"Dataset shape: {df.shape}")

# Preprocess all queries
print("Preprocessing text...")
df['cleaned_query'] = df['query'].apply(preprocess_text)

# -------------------- TF-IDF Vectorization --------------------
# Use unigrams and bigrams, min_df to skip absolute noise
print("Vectorizing data...")
vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
X = vectorizer.fit_transform(df['cleaned_query']).toarray()

# Encode classes
classes = sorted(list(df['intent'].unique()))
y_indices = [classes.index(intent) for intent in df['intent']]
y = np.zeros((len(y_indices), len(classes)))
for i, idx in enumerate(y_indices):
    y[i][idx] = 1

# -------------------- Create Training Data --------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y_indices)

# Compute class weights to handle imbalance
y_train_labels = np.argmax(y_train, axis=1)
unique_classes = np.unique(y_train_labels)
# Use all classes present in y_indices to ensure mapping is complete
all_unique_classes = np.unique(y_indices)
class_weights_array = compute_class_weight('balanced', classes=all_unique_classes, y=y_train_labels)
class_weight_dict = dict(zip(all_unique_classes, class_weights_array))

# -------------------- Build Neural Network --------------------
model = Sequential([
    Dense(512, input_shape=(len(X[0]),), activation='relu'),
    BatchNormalization(),
    Dropout(0.4),
    Dense(256, activation='relu'),
    BatchNormalization(),
    Dropout(0.3),
    Dense(128, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(len(classes), activation='softmax')
])

model.compile(loss='categorical_crossentropy', optimizer=Adam(0.001), metrics=['accuracy'])

# Callbacks for better training
early_stop = EarlyStopping(monitor='val_accuracy', patience=30, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=0.00001)

# Train Model
print(f"Starting training for 200 epochs on {len(X_train)} samples...")
history = model.fit(
    X_train, y_train,
    epochs=200,
    batch_size=32,
    validation_data=(X_test, y_test),
    class_weight=class_weight_dict,
    callbacks=[reduce_lr], # Removed EarlyStopping to train for full 200 epochs
    verbose=1
)

# -------------------- Final Evaluation Summary --------------------
print("\n" + "="*50)
print("TRAINING COMPLETE - FINAL METRICS")
print("="*50)
final_train_acc = history.history['accuracy'][-1]
final_val_acc = history.history['val_accuracy'][-1]
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)

print(f"Final Training Accuracy:   {final_train_acc:.4f}")
print(f"Final Validation Accuracy: {final_val_acc:.4f}")
print(f"Hold-out Test Accuracy:    {test_acc:.4f}")
print("="*50 + "\n")

# -------------------- Save Model & Metadata --------------------
# Save in modern native Keras format
model_path = os.path.join(BASE_DIR, "moonchat_model.keras")
model.save(model_path)
print(f"Model saved to: {model_path}")

# Save TF-IDF vectorizer (needed for inference)
with open(os.path.join(BASE_DIR, "moonchat_vectorizer.pkl"), 'wb') as f:
    pickle.dump(vectorizer, f)

# Save class labels
with open(os.path.join(BASE_DIR, "moonchat_classes.json"), 'w') as f:
    json.dump(classes, f)

print(f"Retrained with TF-IDF: {len(X[0])} features, {len(classes)} classes")