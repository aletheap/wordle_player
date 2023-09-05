import csv
import datetime
import json
import os
from collections import OrderedDict

MY_DIR = os.path.dirname(os.path.realpath(__file__))
# Source: "https://bert.org/assets/posts/wordle/words.json" (with slurs removed)
WORDLE_DATA_FILE = os.path.join(MY_DIR, "wordle_words.json")
# Source: https://www.kaggle.com/datasets/rtatman/english-word-frequency
# WORD_FREQS_DATA_FILE = os.path.join(MY_DIR, "word_freqs_google.json")
WORD_FREQS_DATA_FILE = os.path.join(MY_DIR, "unigram_freq.csv")
WORDLE_START_DATE = datetime.date(2021, 6, 19)
WORD_LENGTH = 5

# Cache data to avoid reloading it
CACHE = {
    "wordle_solutions": [],
    "wordle_valid_words": set(),
    "word_freqs": {},
}


def load_data():
    """Load wordle solutions, wordle valid words, and English word frequencies"""
    wordle_solutions, wordle_valid_words = load_wordle_data()
    word_freqs = load_word_freqs()
    return wordle_solutions, wordle_valid_words, word_freqs


def load_wordle_data():
    """Load wordle solutions and valid words"""
    if not CACHE["wordle_solutions"]:
        with open(WORDLE_DATA_FILE, "r") as f:
            data = json.load(f)
        CACHE["wordle_solutions"] = data["solutions"]
        CACHE["wordle_valid_words"] = set(data["solutions"]) | set(data["other_valid_words"])

    return CACHE["wordle_solutions"], CACHE["wordle_valid_words"]


def load_word_freqs():
    """Load English word frequencies from Google's Unigrams dataset"""
    if not CACHE["word_freqs"]:
        with open(WORD_FREQS_DATA_FILE, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        word_freqs = [
            (row["word"], int(row["count"])) for row in rows if len(row["word"]) == WORD_LENGTH
        ]
        words, freqs = zip(*word_freqs)
        word_freqs = sorted(zip(words, freqs), key=lambda x: x[1], reverse=True)
        word_freqs = OrderedDict(word_freqs)
        CACHE["word_freqs"] = word_freqs
    return CACHE["word_freqs"]


def norm(o):
    """Normalize a dict or list of numbers to sum to 1"""
    if isinstance(o, dict):
        total = sum(o.values())
        return {k: v / total for k, v in o.items()}
    elif isinstance(o, list):
        total = sum(o)
        return [x / total for x in o]
    elif isinstance(o, tuple):
        total = sum(o)
        return tuple([x / total for x in o])
    else:
        raise ValueError(f"Can't normalize {type(o)}")
