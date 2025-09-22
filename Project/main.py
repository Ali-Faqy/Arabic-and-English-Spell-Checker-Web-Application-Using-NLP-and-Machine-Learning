from flask import Flask, jsonify, request
from flask_cors import CORS
import pickle
from spello.model import SpellCorrectionModel
import re
from collections import Counter
from nltk.metrics.distance import edit_distance
from nltk.util import ngrams
from collections import defaultdict
import pyarabic.araby as araby
import editdistance

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Global variables to store output
test1 = []
test2 = []
test3 = []
# Read and normalize the dataset
#########################################################Bi-Gram######################################################
# def read_dataset(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         data = file.readlines()
#     return data


def normalize_text(text):
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ئ', 'ي', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


# Tokenize text
def tokenize_text(text):
    return text.split()


# Create vocabulary limited to top 100,000 words
def create_vocabulary(tokenized_data, max_vocab_size=100000):
    all_words = [word for line in tokenized_data for word in line]
    word_counts = Counter(all_words)
    most_common_words = word_counts.most_common(max_vocab_size)
    vocabulary = {word for word, _ in most_common_words}
    return vocabulary


# Build n-gram model
def build_ngram_model(tokenized_data, n=2):
    ngram_model = defaultdict(Counter)
    for line in tokenized_data:
        for ngram in ngrams(line, n):
            prefix, word = tuple(ngram[:-1]), ngram[-1]
            ngram_model[prefix][word] += 1
    return ngram_model


# Generate candidate corrections
def get_candidates(word, vocabulary, max_distance=2):
    return [vocab_word for vocab_word in vocabulary if edit_distance(word, vocab_word) <= max_distance]


# Score candidates using bigram model
def score_candidates(previous_word, candidates, bigram_model):
    scores = {candidate: bigram_model[(previous_word,)][candidate] for candidate in candidates}
    return scores


# Select best candidates
def select_best_candidate(scores):
    if scores:
        sorted_scores = sorted(scores, key=scores.get, reverse=True)
        return sorted_scores[:3]
    return []


# Validate word
def isValid(word, vocabulary):
    return normalize_text(word) in vocabulary


# Correct and provide feedback for text
def testText(text):
    global test2
    feedback = ''
    text = 's ' + text
    tokenized_text = tokenize_text(text)
    for i in range(1, len(tokenized_text)):
        if not isValid(tokenized_text[i], vocabulary):
            candidates = get_candidates(tokenized_text[i], vocabulary)
            if candidates:
                scores = score_candidates(tokenized_text[i - 1], candidates, bigram_model)
                best_candidates = select_best_candidate(scores)
                if best_candidates:
                    top3_scores = [scores[key] for key in best_candidates]
                    feedback += (f'الكلمة {tokenized_text[i]} تحتوي على أخطاء والكلمات الثلاث الأولى هي:\n'
                                 f'البادئة: {tokenized_text[i - 1]}\n'
                                 f'البديل 1: {best_candidates[0]} بالدرجة: {top3_scores[0]}\n'
                                 f'البديل 2: {best_candidates[1]} بالدرجة: {top3_scores[1]}\n'
                                 f'البديل 3: {best_candidates[2]} بالدرجة: {top3_scores[2]}\n\n')

                    tokenized_text[i] = best_candidates[0]

    tokenized_text.remove('s')
    correct_text = ' '.join(tokenized_text)
    test2 = [correct_text, feedback]

@app.route("/PostArabicInputText", methods=["POST"])
def PostArabicInputText():
    request_data = request.get_json()

    if 'textArea' in request_data:
        text_area_value = request_data['textArea']
        text_area_str = str(text_area_value)
        print(text_area_str)
        spellCheckerByMachineLearning(text_area_str)
    elif 'textFile' in request_data:
        text_area_value = request_data['textFile']
        text_area_str = str(text_area_value)
    testText(text_area_str)
    return jsonify({"message": "Data received successfully"}), 200

@app.route("/getArabicText")
def getArabicText():
    return jsonify(test2), 200

# file_path = 'News-Multi.ar-en.ar.more.clean'
# dataset = read_dataset(file_path)
# normalized_dataset = [normalize_text(line) for line in dataset]
# tokenized_dataset = [tokenize_text(line) for line in normalized_dataset]
# vocabulary = create_vocabulary(tokenized_dataset, max_vocab_size=50000)
# bigram_model = build_ngram_model(tokenized_dataset, n=2)
#########################################################Machine Learning######################################################

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.readlines()
    return data

def train_model(data):
    sp = SpellCorrectionModel(language='en')
    sp.train(data)
    return sp

def save_model(model, filename):
    with open(filename, 'wb') as file:
        pickle.dump(model, file)

def load_model(filename):
    with open(filename, 'rb') as file:
        model = pickle.load(file)
    return model

def spellCheckerByMachineLearning(InputText):
    dataset_path = 'EnDataSet.csv'
    model_path = 'spell_model.pkl'
    global test1
    try:
        sp = load_model(model_path)
        print("Loaded pre-trained model.")
    except FileNotFoundError:
        print("Training the model...")
        data = load_data(dataset_path)
        sp = train_model(data)
        save_model(sp, model_path)
        print("Trained model saved.")

    sent = InputText
    correct = sp.spell_correct(sent)
    spell_corrected_text = correct['spell_corrected_text']
    correction_dict = correct['correction_dict']
    print(f"spell_corrected_text: '{spell_corrected_text}'\n")
    print(f"corrections: {correction_dict}")
    test1 = [spell_corrected_text, correction_dict]

@app.route("/getEnglishText")
def getEnglishText():
    return jsonify(test1), 200

@app.route("/PostEnglishInputText", methods=["POST"])
def PostEnglishInputText():
    request_data = request.get_json()

    if 'textArea' in request_data:
        text_area_value = request_data['textArea']
        text_area_str = str(text_area_value)
        print(text_area_str)
    elif 'textFile' in request_data:
        text_area_value = request_data['textFile']
        text_area_str = str(text_area_value)

    spellCheckerByMachineLearning(text_area_str)
    return jsonify({"message": "Data received successfully"}),200


####################################################levenshtein###########################################################

# def load_words(filename):
#     with open(filename, 'r', encoding='utf-8') as file:
#         return set(word.strip() for word in file)

# arabic_words = load_words('arabic_words.csv')

def spellcheck(word, maxdistance=2):
    suggestions = []
    suggestions_distance_1 = []
    if word in arabic_words:
        return [word]
    for candidate in arabic_words:
        distance = editdistance.eval(word, candidate)
        if distance <= maxdistance:
            if distance == 1:
                suggestions_distance_1.append(candidate)
            elif distance == 2:
                suggestions.append(candidate)
    if suggestions_distance_1:
        return suggestions_distance_1
    elif suggestions:
        return suggestions
    else:
        return [word]
def generate_sentences(words, index=0):
    if index == len(words):
        return [[]]

    corrected_words = spellcheck(words[index])
    rest_sentences = generate_sentences(words, index + 1)

    all_sentences = []
    for corrected_word in corrected_words:
        for rest_sentence in rest_sentences:
            all_sentences.append([corrected_word] + rest_sentence)

    return all_sentences


def test_spellcheck(input_string):
    global test3
    words = araby.tokenize(input_string)
    corrected_sentences = generate_sentences(words)
    corrected_sentences_strings = [' '.join(sentence) for sentence in corrected_sentences]
    test3 = corrected_sentences_strings

@app.route("/getlevenshteinText")
def getlevenshteinText():
    return jsonify(test3), 200

@app.route("/PostlevenshteinInputText", methods=["POST"])
def PostlevenshteinInputText():
    request_data = request.get_json()

    if 'textArea' in request_data:
        text_area_value = request_data['textArea']
        text_area_str = str(text_area_value)
        print(text_area_str)
    elif 'textFile' in request_data:
        text_area_value = request_data['textFile']
        text_area_str = str(text_area_value)

    test_spellcheck(text_area_str)
    return jsonify({"message": "Data received successfully"}),200

if __name__ == "__main__":
    app.run(debug=True)
