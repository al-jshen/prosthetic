from functools import partial
import os
from tqdm.auto import tqdm
from collections import Counter
import joblib
from joblib import Parallel, delayed
import argparse
import string
import re
from pprint import pprint


def build_text(corpora_dir):
    filenames = []

    for root, dirs, files in tqdm(
        os.walk(corpora_dir, topdown=False), desc="Searching for text files"
    ):
        for name in files:
            if name.endswith(".txt"):
                filenames.append(os.path.join(root, name))

    full_text = ""
    for f in tqdm(filenames, desc="Reading text files"):
        with open(f, "r") as file:
            full_text += file.read()

    return full_text


def build_character_ngrams(text, n):
    ngrams = Counter()
    words = text.split(" ")
    for word in words:
        for i in range(len(word) - n + 1):
            ngrams[word[i : i + n]] += 1
    return ngrams


def build_word_ngrams(text, n):
    ngrams = Counter()
    words = text.split(" ")
    for i in range(len(words) - n + 1):
        # the only 1-gram allowed is "a" and "i"
        if n == 1 and words[i] not in ["a", "i"]:
            continue
        ngrams[" ".join(words[i : i + n])] += 1
    return ngrams


def filter_text(text, filter_words=[]):
    text = text.strip().lower()  # remove leading and trailing spaces and make lowercase
    text = re.sub(r"[^a-z ]+", "", text)  # keep only letters and spaces
    for w in filter_words:
        text = text.replace(w, "")
    text = re.sub(r"\s\s+", " ", text)  # remove multiple spaces
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora_dir", type=str, default="../corpora")
    parser.add_argument("--n_max_char", type=int, default=5)
    parser.add_argument("--n_max_word", type=int, default=2)
    parser.add_argument("--chunks", type=int, default=100)
    parser.add_argument("--n_jobs", type=int, default=-1)
    parser.add_argument("--keep_top", type=int, default=1_000)
    parser.add_argument("--save_dir", type=str, default="./")
    parser.add_argument("--filter_words_file", type=str, default="./filter_words.txt")
    args = parser.parse_args()
    full_text = build_text(args.corpora_dir).lower()
    with open(args.filter_words_file, "r") as file:
        filter_words = [l.rstrip() for l in file]
    # split full text into 100 chunks
    len_text = len(full_text)
    len_chunks = len_text // 100
    chunks = [full_text[i : i + len_chunks] for i in range(0, len_text, len_chunks)]
    filtered_text = Parallel(n_jobs=args.n_jobs)(
        (
            delayed(filter_text)(chunk, filter_words)
            for chunk in tqdm(chunks, desc="Filtering text")
        )
    )

    cngrams = Counter()
    wngrams = Counter()

    # build character level ngrams
    for n in range(1, args.n_max_char + 1):
        partial_ngrams = []
        partial_ngrams += Parallel(n_jobs=args.n_jobs)(
            delayed(build_character_ngrams)(chunk, n)
            for chunk in tqdm(filtered_text, desc=f"Building character-level {n}-grams")
        )

        ngrams = partial_ngrams[0]
        for ngram in partial_ngrams[1:]:
            ngrams.update(ngram)

        # normalize ngrams per ngram length
        total_ngrams = sum(ngrams.values())
        for ngram in ngrams:
            ngrams[ngram] /= total_ngrams

        cngrams.update(ngrams)

    # build word level ngrams
    for n in range(1, args.n_max_word + 1):
        partial_ngrams = []
        partial_ngrams += Parallel(n_jobs=args.n_jobs)(
            delayed(build_word_ngrams)(chunk, n)
            for chunk in tqdm(filtered_text, desc=f"Building word-level {n}-grams")
        )

        ngrams = partial_ngrams[0]
        for ngram in partial_ngrams[1:]:
            ngrams.update(ngram)

        # normalize ngrams
        total_ngrams = sum(ngrams.values())
        for ngram in ngrams:
            ngrams[ngram] /= total_ngrams

        wngrams.update(ngrams)

    top_cngrams = cngrams.most_common(args.keep_top)
    top_wngrams = wngrams.most_common(args.keep_top)

    joblib.dump(dict(top_cngrams), args.save_dir + "cngrams.joblib")
    joblib.dump(dict(top_wngrams), args.save_dir + "wngrams.joblib")
