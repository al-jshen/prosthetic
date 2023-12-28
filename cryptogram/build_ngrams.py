from functools import partial
import os
from tqdm.auto import tqdm
from collections import Counter
import joblib
from joblib import Parallel, delayed
import argparse
import string
import re


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


def build_ngrams(text, n):
    ngrams = Counter()
    for i in range(len(text) - n):
        ngrams[text[i : i + n]] += 1
    return ngrams


def filter_text(
    text, strip_punctuation=True, strip_whitespace=True, strip_numbers=True
):
    # pattern = re.compile('[\W_]+', re.UNICODE)
    # remove tabs and newlines
    # text = (
    #     text.replace("\n", " ").replace("\t", " ").replace("\r", " ").replace("  ", " ")
    # )
    # if strip_punctuation:
    #     text = text.translate(str.maketrans("", "", string.punctuation))
    # if strip_whitespace:
    #     text = text.translate(str.maketrans("", "", string.whitespace))
    # if strip_numbers:
    #     text = text.translate(str.maketrans("", "", string.digits))
    # return text
    text = re.sub(r"[^a-z ]+", "", text)
    text = re.sub(r"\s\s+", " ", text)
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora_dir", type=str, default="../corpora")
    parser.add_argument("--n_max", type=int, default=6)
    parser.add_argument("--strip_punctuation", action="store_true")
    parser.add_argument("--strip_whitespace", action="store_true")
    parser.add_argument("--strip_numbers", action="store_true")
    parser.add_argument("--chunks", type=int, default=100)
    parser.add_argument("--n_jobs", type=int, default=-1)
    parser.add_argument("--keep_top", type=int, default=50_000)
    parser.add_argument("--save_path", type=str, default="ngrams.joblib")
    args = parser.parse_args()
    full_text = build_text(args.corpora_dir).lower()
    # split full text into 100 chunks
    len_text = len(full_text)
    len_chunks = len_text // 100
    chunks = [full_text[i : i + len_chunks] for i in range(0, len_text, len_chunks)]
    filter_fn = partial(
        filter_text,
        strip_punctuation=args.strip_punctuation,
        strip_whitespace=args.strip_whitespace,
        strip_numbers=args.strip_numbers,
    )
    filtered_text = Parallel(n_jobs=args.n_jobs)(
        (delayed(filter_fn)(chunk) for chunk in tqdm(chunks, desc="Filtering text"))
    )

    all_ngrams = []

    for n in range(1, args.n_max + 1):
        partial_ngrams = []
        partial_ngrams += Parallel(n_jobs=args.n_jobs)(
            delayed(build_ngrams)(chunk, n)
            for chunk in tqdm(filtered_text, desc=f"Building {n}-grams")
        )

        ngrams = partial_ngrams[0]
        for ngram in partial_ngrams[1:]:
            ngrams.update(ngram)

        # normalize ngrams
        total_ngrams = sum(ngrams.values())
        for ngram in ngrams:
            ngrams[ngram] /= total_ngrams

        all_ngrams.append(ngrams)

    full_ngrams = all_ngrams[0]
    for ngram in all_ngrams[1:]:
        full_ngrams.update(ngram)

    top_ngrams = full_ngrams.most_common(args.keep_top)

    joblib.dump(dict(top_ngrams), args.save_path)
