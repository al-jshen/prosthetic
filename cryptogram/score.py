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


def score_translation(text, translation, cngram_freq, wngram_freq):
    score = 0
    decrypted = text.translate(str.maketrans(translation))
    decrypted_cngrams, decrypted_wngrams = build_all_ngrams(decrypted)

    print("Char ngrams")
    print(decrypted_cngrams)

    print("Word ngrams")
    print(decrypted_wngrams)

    char_score = 0
    word_score = 0

    for ngram, count in decrypted_cngrams.items():
        if ngram in cngram_freq:
            char_score += count * cngram_freq[ngram]

    for ngram, count in decrypted_wngrams.items():
        if ngram in wngram_freq:
            print("Found word ngram", ngram)
            word_score += (
                count * wngram_freq[ngram] * 2 * len(ngram)
            )  # weight word ngrams more and longer words more

    print(char_score, word_score)

    score = char_score + word_score

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
    parser.add_argument("--iters", type=int, default=10_000)
    parser.add_argument("--sync_every", type=int, default=100)
    parser.add_argument("--patience", type=int, default=2_000)
    parser.add_argument("--branches", type=int, default=8)
    args = parser.parse_args()

    cngram_freq = joblib.load(args.ngram_path + "cngrams.joblib")
    wngram_freq = joblib.load(args.ngram_path + "wngrams.joblib")

    translation = {l: l for l in string.ascii_lowercase}

    input_text = build_ngrams.filter_text(args.input)

    print(score_translation(input_text, translation, cngram_freq, wngram_freq))

    # build letter pairs and test swaps in parallel

    # print(translation)
    print(input_text.translate(str.maketrans(translation)))
