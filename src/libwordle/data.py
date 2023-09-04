import json
import os
import datetime

MY_DIR = os.path.dirname(os.path.realpath(__file__))
# Source: "https://bert.org/assets/posts/wordle/words.json"
WORDLE_DATA_FILE = os.path.join(MY_DIR, "wordle_words.json")
# Source: https://www.kaggle.com/datasets/rtatman/english-word-frequency
WORD_FREQS_DATA_FILE = os.path.join(MY_DIR, "word_freqs_google.json")
WORDLE_START_DATE = datetime.date(2021, 6, 19)
WORD_LENGTH = 5

CACHE = {
    "wordle_solutions": [],
    "wordle_valid_words": [],
    "word_freqs": {},
}


def load_data():
    wordle_solutions, wordle_valid_words = load_wordle_data()
    word_freqs = load_word_freqs()
    return wordle_solutions, wordle_valid_words, word_freqs


def load_wordle_data():
    if not CACHE["wordle_solutions"]:
        with open(WORDLE_DATA_FILE, "r") as f:
            data = json.load(f)
        CACHE["wordle_solutions"] = data["solutions"]
        CACHE["wordle_valid_words"] = sorted(
            list(set(data["solutions"]) | set(data["other_valid_words"]))
        )
    return CACHE["wordle_solutions"], CACHE["wordle_valid_words"]


def load_word_freqs():
    if not CACHE["word_freqs"]:
        with open(WORD_FREQS_DATA_FILE, "r") as f:
            word_freqs = json.load(f)
        word_freqs = dict(sorted(word_freqs.items(), key=lambda x: x[1], reverse=True))
        CACHE["word_freqs"] = norm(word_freqs)
    return CACHE["word_freqs"]


def norm(o):
    if isinstance(o, dict):
        total = sum(o.values())
        return {k: v / total for k, v in o.items()}
    elif isinstance(o, list):
        total = sum(o)
        return [x / total for x in o]
    else:
        raise ValueError(f"Can't normalize {type(o)}")
