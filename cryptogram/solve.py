import argparse
import joblib
from collections import Counter
import build_ngrams
import string
import random
from tqdm.auto import tqdm
from joblib import Parallel, delayed
from copy import deepcopy


def swap_letters(translation, n_swaps=1):
    translation_new = translation.copy()
    for _ in range(n_swaps):
        r1, r2 = random.sample(string.ascii_lowercase, 2)
        translation_new[r1], translation_new[r2] = (
            translation_new[r2],
            translation_new[r1],
        )
    return translation_new


def build_all_ngrams(text, n_min=1, n_max=8):
    return sum(
        [
            build_ngrams.build_ngrams(build_ngrams.filter_text(text), n)
            for n in range(n_min, n_max)
        ],
        Counter(),
    )


def score_translation(text, translation, ngrams, dictionary):
    score = 0
    decrypted = text.translate(str.maketrans(translation))
    decrypted_ngrams = build_all_ngrams(decrypted)
    for ngram, count in decrypted_ngrams.items():
        if ngram in ngrams:
            score += count * ngrams[ngram]

    ngram_score = score

    decrypted_words = decrypted.split()
    for word in decrypted_words:
        if word in dictionary:
            score += 0.01 * len(word) * ngram_score

    return score


def search_translations(text, translation, ngrams, dictionary, iters=100, nswaps=1):
    score = 0
    for _ in range(iters):
        score = score_translation(text, translation, ngrams, dictionary)
        # test new translation
        translation_new = swap_letters(translation, nswaps)
        score_new = score_translation(text, translation_new, ngrams, dictionary)
        accept_ratio = score_new / score
        u = random.uniform(0, 1)
        if u < accept_ratio:
            translation = translation_new
            score = score_new
    return translation, score


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="Cryptogram puzzle")
    parser.add_argument("--ngram_file", type=str, help="Ngram file")
    parser.add_argument("--dictionary_file", type=str, help="Dictionary file")
    parser.add_argument("--iters", type=int, default=10_000)
    parser.add_argument("--sync_every", type=int, default=100)
    parser.add_argument("--patience", type=int, default=1_000)
    parser.add_argument("--branches", type=int, default=8)
    args = parser.parse_args()

    ngrams = joblib.load(args.ngram_file)
    with open(args.dictionary_file) as f:
        dictionary = set([line.rstrip() for line in f.readlines()])

    translation = {l: l for l in string.ascii_lowercase}

    # build letter pairs and test swaps in parallel

    passes = args.iters // args.sync_every

    best = 0
    since_improved = 0

    for i in (pbar := tqdm(range(passes))):
        # start with max of 10 swaps, then linearly decrease to 1
        nswaps = max(1, 10 - i * 9 // passes)
        translations, scores = zip(
            *Parallel(n_jobs=args.branches)(
                delayed(search_translations)(
                    args.input.lower(),
                    translation,
                    ngrams,
                    dictionary,
                    iters=args.sync_every,
                    nswaps=nswaps,
                )
                for _ in range(args.branches)
            )
        )

        best_new_ix = scores.index(max(scores))
        best_new = scores[best_new_ix]
        if best_new > best:
            translation = translations[best_new_ix]
            best = best_new
            since_improved = 0
        else:
            since_improved += 1
            if since_improved > args.patience // args.sync_every:
                break

        pbar.set_description(f"Iter {i * args.sync_every}, score: {best}")

    print(translation)
    print(args.input.lower().translate(str.maketrans(translation)))
