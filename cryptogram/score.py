import argparse
import joblib
from collections import Counter
import build_ngrams
import string


def build_all_ngrams(
    text,
    dictionary,
    n_max_char=5,
    n_max_word=3,
):
    cngrams = Counter()
    wngrams = Counter()
    words = Counter()
    for n in range(1, n_max_char + 1):
        cngrams.update(build_ngrams.build_character_ngrams(text, n))
    for n in range(1, n_max_word + 1):
        wngrams.update(build_ngrams.build_word_ngrams(text, n))
    words.update(build_ngrams.build_words(text, dictionary))
    return cngrams, wngrams, words


def score_translation(
    text,
    translation,
    cngram_freq,
    wngram_freq,
    word_freq,
    dictionary,
    verbose=False,
    char_ngram_weight=1.0,
    word_ngram_weight=2.0,
    word_weight=5.0,
    freq_smoothing=1e-6,
    word_freq_smoothing=1e-6,
):
    score = 0
    decrypted = text.translate(str.maketrans(translation))
    decrypted_cngrams, decrypted_wngrams, decrypted_words = build_all_ngrams(
        decrypted, dictionary
    )

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
            char_ngram_score += (
                count
                * (cngram_freq[ngram] + freq_smoothing)
                * char_ngram_weight  # * len(ngram)
            )

    for ngram, count in decrypted_wngrams.items():
        if ngram in wngram_freq:
            if verbose:
                print("Found word ngram", ngram)
            word_ngram_score += (
                count * (wngram_freq[ngram] + word_freq_smoothing) * word_ngram_weight
                # * (1 - len(ngram.split(" ")))
            )  # weight word ngrams more and longer words more

    for word, count in decrypted_words.items():
        if word in word_freq:
            if verbose:
                print("Found word", word)
            word_score += (
                count
                * (word_freq[word] + word_freq_smoothing)
                # * len(word) ** 2
                * word_weight
            )

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
    parser.add_argument("--freq_smoothing", type=float, default=1e-6)
    parser.add_argument("--word_freq_smoothing", type=float, default=1e-6)
    parser.add_argument("--char_ngram_weight", type=float, default=1.0)
    parser.add_argument("--word_ngram_weight", type=float, default=2.0)
    parser.add_argument("--word_weight", type=float, default=5.0)
    args = parser.parse_args()

    cngram_freq = joblib.load(args.ngram_path + "cngrams.joblib")
    wngram_freq = joblib.load(args.ngram_path + "wngrams.joblib")
    word_freq = joblib.load(args.ngram_path + "words.joblib")
    with open(args.dictionary, "r") as f:
        dictionary = set([w.rstrip() for w in f.readlines()])

    translation = {l: l for l in string.ascii_lowercase}

    input_text = build_ngrams.filter_text(args.input)

    print(
        score_translation(
            input_text,
            translation,
            cngram_freq,
            wngram_freq,
            word_freq,
            dictionary,
            verbose=True,
            char_ngram_weight=args.char_ngram_weight,
            word_ngram_weight=args.word_ngram_weight,
            word_weight=args.word_weight,
            freq_smoothing=args.freq_smoothing,
            word_freq_smoothing=args.word_freq_smoothing,
        )
    )

    print(input_text.translate(str.maketrans(translation)))
