import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD
import random

lemmatizer = WordNetLemmatizer()
words = []
classes = []
documents = []
ignore_words = ['?', '!']

data_file = open('data.json').read()
intents = json.loads(data_file)

for intent in intents['intents']:
    for pattern in intent['patterns']:
        # tokenize each word
        w = nltk.word_tokenize(pattern)
        words.extend(w)
        # add documents to the corpus
        documents.append((w, intent['tag']))

        # add to our classes list
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# lemmatize and lower each word and remove duplicates
words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))
# sort classes
classes = sorted(list(set(classes)))

# create our training data
training = []
output_empty = [0] * len(classes)

# training set, bag of words for each sentence
for doc in documents:
    # initialize our bag of words
    bag = []
    # list of tokenized words for the pattern
    pattern_words = doc[0]
    # lemmatize each word - create base word, in an attempt to represent related words
    pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]
    # create our bag of words array with 1, if word match found in current pattern
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)

    # output is a '0' for each tag and '1' for current tag (for each pattern)
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1

    training.append([bag, output_row])

# shuffle our features
random.shuffle(training)

# Convert training to a NumPy array
training = np.array(training, dtype=object)  # Set dtype as object to handle variable-length arrays

# split the training data into input and output (patterns and intents)
train_x = np.array(training[:, 0].tolist())  # Convert bag of words to array
train_y = np.array(training[:, 1].tolist())  # Convert output_row to array

print("Training data created")

# Save processed words and labels
pickle.dump(words, open('texts.pkl', 'wb'))
pickle.dump(classes, open('labels.pkl', 'wb'))

# Create model - Increased model complexity
model = Sequential()
model.add(Dense(256, input_shape=(len(train_x[0]),), activation='relu'))  # Increased neurons
model.add(Dropout(0.5))
model.add(Dense(128, activation='relu'))  # Increased neurons
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# Compile model. Stochastic gradient descent with Nesterov accelerated gradient gives good results for this model
sgd = SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Fitting the model with adjusted batch size and epochs
hist = model.fit(train_x, train_y, epochs=500, batch_size=32, verbose=1)  # Adjusted batch size and epochs
# Save the model
model.save('model.h5')

print("Model created")
