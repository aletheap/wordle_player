import json
import os

MY_DIR = os.path.dirname(os.path.realpath(__file__))


def load_data(max_vocab_size=None, word_freqs_data_file=None, wordle_data_file=None):
    wordle_solutions, wordle_valid_words = load_wordle_data(data_file=wordle_data_file)
    word_freqs = load_word_freqs(
        max_vocab_size=max_vocab_size,
        data_file=word_freqs_data_file,
        only_include_words=wordle_valid_words,
    )

    return wordle_solutions, wordle_valid_words, word_freqs


def load_wordle_data(data_file=None):
    if data_file is None:
        data_file = os.path.join(MY_DIR, "wordle_words.json")

    # Load all Wordle words. Source: "https://bert.org/assets/posts/wordle/words.json"
    with open(data_file, "r") as f:
        data = json.load(f)
    solutions = data["solutions"]
    other_valid_words = set(data["other_valid_words"])
    all_words = set(solutions) | other_valid_words

    return solutions, all_words


def load_word_freqs(max_vocab_size=None, data_file=None, only_include_words=None):
    if data_file is None:
        data_file = os.path.join(MY_DIR, "word_freqs.json")

    with open(data_file, "r") as f:
        word_freqs = json.load(f)

    # only include words
    if only_include_words is not None:
        word_freqs = {k: v for k, v in word_freqs.items() if k in only_include_words}

    # truncate to max len
    word_freqs = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)[:max_vocab_size]

    # normalize word_freqs
    total_freqs = sum([x[1] for x in word_freqs])
    word_freqs = {w: f / total_freqs for w, f in word_freqs}

    return word_freqs
