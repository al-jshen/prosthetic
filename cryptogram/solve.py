import argparse
import joblib
from collections import Counter
import build_ngrams
from score import score_translation
import string
import random
from tqdm.auto import tqdm
from joblib import Parallel, delayed
import math


def swap_letters(translation, n_swaps=1):
    translation_new = translation.copy()
    for _ in range(n_swaps):
        r1, r2 = random.sample(string.ascii_lowercase, 2)
        translation_new[r1], translation_new[r2] = (
            translation_new[r2],
            translation_new[r1],
        )
    return translation_new


def build_all_ngrams(text, n_max_char=5, n_max_word=3):
    cngrams = Counter()
    wngrams = Counter()
    for n in range(1, n_max_char + 1):
        cngrams.update(build_ngrams.build_character_ngrams(text, n))
    for n in range(1, n_max_word + 1):
        wngrams.update(build_ngrams.build_word_ngrams(text, n))
    return cngrams, wngrams


def search_translations(
    text,
    translation,
    cngram_freq,
    wngram_freq,
    dictionary,
    iters=10_000,
    nswaps=1,
    temperature_schedule=lambda i, t: 1.0,
    word_ngram_upweight=2.0,
    word_upweight=5.0,
):
    score = score_translation(
        text,
        translation,
        cngram_freq,
        wngram_freq,
        dictionary,
        verbose=False,
        word_ngram_weight=word_ngram_upweight,
        word_weight=word_upweight,
    )
    pbar_every = iters // 100
    for i in (pbar := tqdm(range(iters))):
        # test new translation
        translation_new = swap_letters(translation, nswaps)
        score_new = score_translation(
            text,
            translation_new,
            cngram_freq,
            wngram_freq,
            dictionary,
            verbose=False,
            word_ngram_weight=word_ngram_upweight,
            word_weight=word_upweight,
        )

        # simulated annealing
        accept_ratio = score_new / score
        u = random.uniform(0, 1)
        if u < accept_ratio ** (1 / temperature_schedule(i, iters)):
            translation = translation_new
            score = score_new

        # # greedy
        # if score_new > score:
        #     translation = translation_new
        #     score = score_new

        if i % pbar_every == 0:
            pbar.set_description(f"Score: {score}")

    return translation, score


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="Cryptogram puzzle")
    parser.add_argument(
        "--ngram_path",
        type=str,
        help="Directory with ngrams frequency tables",
        default="./",
    )
    parser.add_argument("--dictionary", type=str, help="Dictionary file")
    parser.add_argument("--word_ngram_upweight", type=float, default=2.0)
    parser.add_argument("--word_upweight", type=float, default=5.0)
    parser.add_argument("--iters", type=int, default=20_000)
    parser.add_argument("--max_temp", type=float, default=10.0)
    parser.add_argument("--restarts", type=int, default=10)
    parser.add_argument("--aggression", type=int, default=15)
    args = parser.parse_args()

    cngram_freq = joblib.load(args.ngram_path + "cngrams.joblib")
    wngram_freq = joblib.load(args.ngram_path + "wngrams.joblib")
    with open(args.dictionary) as f:
        dictionary = set([l.strip() for l in f])

    translation = {l: l for l in string.ascii_lowercase}

    input_text = build_ngrams.filter_text(args.input)

    translation, score = search_translations(
        input_text,
        translation,
        cngram_freq,
        wngram_freq,
        dictionary,
        iters=args.iters,
        nswaps=2,
        temperature_schedule=lambda i, t: 1
        / (i / (t / args.restarts) + 1)
        * args.max_temp
        * (((i % (t / args.restarts)) / t) + 1) ** (-args.aggression),
        # temperature_schedule=lambda i, t: math.cos(100 * math.pi * i / t) ** 2 + 0.01,
        word_ngram_upweight=args.word_ngram_upweight,
        word_upweight=args.word_upweight,
    )

    print(translation)

    print(
        score_translation(
            input_text,
            translation,
            cngram_freq,
            wngram_freq,
            dictionary,
            verbose=True,
            word_ngram_weight=args.word_ngram_upweight,
            word_weight=args.word_upweight,
        )
    )
    print(input_text.translate(str.maketrans(translation)))
