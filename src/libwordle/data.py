import json
import os

MY_DIR = os.path.dirname(os.path.realpath(__file__))


def load_data(max_vocab_size=None, vocab_data_file=None, wordle_data_file=None):
    vocab = load_vocab(max_vocab_size=max_vocab_size, data_file=vocab_data_file)
    wordle_solutions, wordle_all_words = load_wordle_data(data_file=wordle_data_file)

    # wordle will not allow words other than solutions or other_valid_words so we should
    # enforce the same behavior:
    vocab = {k: v for k, v in vocab if k in wordle_all_words}

    return vocab, wordle_solutions, wordle_all_words


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


def load_vocab(max_vocab_size=None, data_file=None):
    if data_file is None:
        data_file = os.path.join(MY_DIR, "vocab.json")

    with open(data_file, "r") as f:
        vocab = json.load(f)
    vocab = sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:max_vocab_size]

    # normalize vocab
    max_word_freq = max(vocab.values())
    vocab = {k: v / max_word_freq for k, v in vocab.items()}

    return vocab
