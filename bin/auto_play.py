#!/usr/bin/env python

import json
import multiprocessing as mp
import os
import time

import fire
import numpy as np
from libwordle.data import load_data, load_word_freqs
from libwordle.game import WordleGame
from libwordle.player import WordlePlayer
from libwordle.visualization import save_results, save_stats
from tqdm import tqdm



def play_game(wordle_number, word_freqs, solutions, valid_words):
    game = WordleGame(
        wordle_number=wordle_number,
        solutions=solutions,
        valid_words=valid_words,
        word_freqs=word_freqs,
    )
    player = WordlePlayer(word_freqs=word_freqs)

    while not game.is_finished:
        word = player.best_guess()
        if word is None:
            break
        hints = game.guess(word)
        player.add_hints(word, hints)

    color_grid = []
    for hints in game.all_hints:
        color_line = [{"B": 1, "G": 3, "Y": 2}[h] for h in hints]
        color_grid.append(color_line)
    output = {
        "won": game.won,
        "guesses": len(game.guesses),
        "color_grid": color_grid,
        "wordle_number": wordle_number,
        "time": time.time(),
    }

    return output


def main(
    num_games=3000,
    num_threads=None,
    output_dir = '.',
    max_vocab_size=100_000,
    debug=False,
    mobile_friendly=False,
    save_grids=False,
    random_games=False,
):

    if random_games:
        word_freqs = load_word_freqs(max_vocab_size=max_vocab_size)
        num_games = min(num_games, len(word_freqs))
        words, probs = list(zip(*word_freqs.items()))
        solutions = np.random.choice(words, size=num_games, replace=False, p=probs).tolist()
        valid_words = set(words)
    else:
        solutions, valid_words, word_freqs = load_data(max_vocab_size=max_vocab_size)
        num_games = min(num_games, len(solutions))

    num_games = num_games or len(solutions)
    results_file = os.path.join(output_dir, "results.json")

    if debug:
        with open(results_file) as f:
            results = json.load(f)
    else:
        with mp.Pool(num_threads) as p:
            r = [
                p.apply_async(play_game, (i, word_freqs, solutions, valid_words))
                for i in range(num_games)
            ]
            finished = 0
            with tqdm(total=num_games, unit="game(s)") as pb:
                while finished < num_games:
                    new_finished = len([1 for x in r if x.ready()])
                    # progress_tracker.append((time.time() - t0, new_finished))
                    pb.update(new_finished - finished)
                    finished = new_finished
            results = [x.get() for x in r]
            results = [r for r in results if r is not None]
            with open(results_file, "w") as f:
                json.dump(results, f)

    save_stats(results, output_dir)
    if save_grids:
        save_results(results, output_dir, mobile_friendly=mobile_friendly)


if __name__ == "__main__":
    fire.Fire(main)
