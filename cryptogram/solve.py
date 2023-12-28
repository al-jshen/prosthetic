import argparse
import joblib
from collections import Counter
import build_ngrams
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


def score_translation(text, translation, cngram_freq, wngram_freq, word_upweight=10.0):
    score = 0
    decrypted = text.translate(str.maketrans(translation))
    decrypted_cngrams, decrypted_wngrams = build_all_ngrams(decrypted)

    char_score = 0
    word_score = 0

    for ngram, count in decrypted_cngrams.items():
        if ngram in cngram_freq:
            char_score += count * cngram_freq[ngram]

    for ngram, count in decrypted_wngrams.items():
        if ngram in wngram_freq:
            word_score += (
                count * wngram_freq[ngram] * word_upweight * len(ngram)
            )  # weight word ngrams more and longer words more

    score = char_score + word_score

    return score


def search_translations(
    text,
    translation,
    cngram_freq,
    wngram_freq,
    iters=100,
    nswaps=1,
    temperature=1.0,
    word_upweight=10.0,
):
    score = score_translation(
        text, translation, cngram_freq, wngram_freq, word_upweight
    )
    for _ in range(iters):
        # test new translation
        translation_new = swap_letters(translation, nswaps)
        score_new = score_translation(
            text, translation_new, cngram_freq, wngram_freq, word_upweight
        )
        accept_ratio = score_new / score
        u = random.uniform(0, 1)
        # use a metropolis-hastings criterion to accept or reject the new translation
        # include a temperature parameter to control the randomness
        # like a simulated annealing algorithm
        if u < accept_ratio ** (1 / temperature):
            translation = translation_new
            score = score_new

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
    parser.add_argument("--word_upweight", type=float, default=10.0)
    parser.add_argument("--iters", type=int, default=10_000)
    parser.add_argument("--sync_every", type=int, default=10)
    parser.add_argument("--patience", type=int, default=2_000)
    parser.add_argument("--branches", type=int, default=2)
    args = parser.parse_args()

    cngram_freq = joblib.load(args.ngram_path + "cngrams.joblib")
    wngram_freq = joblib.load(args.ngram_path + "wngrams.joblib")

    translation = {l: l for l in string.ascii_lowercase}

    # build letter pairs and test swaps in parallel

    passes = args.iters // args.sync_every

    best = 0
    since_improved = 0

    input_text = build_ngrams.filter_text(args.input)

    for i in (pbar := tqdm(range(passes))):
        # start with max of 5 swaps, then decrease linearly to 1
        nswaps = int(max(1, 5 - i / passes))
        # start with high temperature, then do a cosine annealing schedule
        temperature = 30 * math.cos(math.pi / 2 * i / passes)
        translations, scores = zip(
            *Parallel(n_jobs=args.branches)(
                delayed(search_translations)(
                    input_text,
                    translation,
                    cngram_freq,
                    wngram_freq,
                    iters=args.sync_every,
                    nswaps=nswaps,
                    temperature=temperature,
                    word_upweight=args.word_upweight,
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
