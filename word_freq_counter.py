#!/usr/bin/env python

import json
import os
import re
from collections import Counter

from tqdm import tqdm

# get a list of all files in the directory
files = ["wikitext-103/train.csv", "wikitext-103/test.csv"] + [
    f"data/{f}" for f in os.listdir("data") if os.path.isfile(f"data/{f}") and f.endswith(".txt")
]

word_re = re.compile(r"^[A-Za-z]{5}$")
c: Counter = Counter()

for i, filename in enumerate(files):
    print(f"{i}/{len(files)}: {filename}")
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in tqdm(lines):
            words = [w.lower() for w in line.split() if word_re.match(w)]
            c.update(words)

with open("words.json", "r") as f:
    data = json.load(f)
    solutions = data["solutions"]
    herrings = data["herrings"]

most_common = c.most_common()
word_freqs = {x[0]: x[1] for x in most_common}
with open("word_freqs.json", "w") as f:
    json.dump(word_freqs, f)
    print(f"wrote word freqs to {f.name}")
