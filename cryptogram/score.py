import argparse
import joblib
from collections import Counter
import build_ngrams
import string


def build_all_ngrams(text, n_max_char=5, n_max_word=3):
    cngrams = Counter()
    wngrams = Counter()
    for n in range(1, n_max_char + 1):
        cngrams.update(build_ngrams.build_character_ngrams(text, n))
    for n in range(1, n_max_word + 1):
        wngrams.update(build_ngrams.build_word_ngrams(text, n))
    return cngrams, wngrams


def score_translation(
    text,
    translation,
    cngram_freq,
    wngram_freq,
    dictionary,
    verbose=False,
    word_ngram_weight=2.0,
    word_weight=1.0,
):
    score = 0
    decrypted = text.translate(str.maketrans(translation))
    decrypted_cngrams, decrypted_wngrams = build_all_ngrams(decrypted)

    if verbose:
        print("Char ngrams")
        print(decrypted_cngrams)

        print("Word ngrams")
        print(decrypted_wngrams)

    char_ngram_score = 0
    word_ngram_score = 0
    word_score = 0

    for ngram, count in decrypted_cngrams.items():
        if ngram in cngram_freq:
            if verbose:
                print("Found char ngram", ngram)
            char_ngram_score += count * cngram_freq[ngram]

    for ngram, count in decrypted_wngrams.items():
        if ngram in wngram_freq:
            if verbose:
                print("Found word ngram", ngram)
            word_ngram_score += (
                count * wngram_freq[ngram] * word_ngram_weight * len(ngram) ** 2
            )  # weight word ngrams more and longer words more

    words = decrypted.split(" ")

    for word in words:
        if word in dictionary:
            if verbose:
                print("Found word", word)
            word_score += len(word) ** 2 / 100 * word_weight

    if verbose:
        print(char_ngram_score, word_ngram_score, word_score)

    score = char_ngram_score + word_ngram_score + word_score

    return score


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
    args = parser.parse_args()

    cngram_freq = joblib.load(args.ngram_path + "cngrams.joblib")
    wngram_freq = joblib.load(args.ngram_path + "wngrams.joblib")
    with open(args.dictionary, "r") as f:
        dictionary = set([w.strip() for w in f])

    translation = {l: l for l in string.ascii_lowercase}

    input_text = build_ngrams.filter_text(args.input)

    print(
        score_translation(
            input_text,
            translation,
            cngram_freq,
            wngram_freq,
            dictionary,
            verbose=True,
            word_ngram_weight=2,
            word_weight=1,
        )
    )

    print(input_text.translate(str.maketrans(translation)))
