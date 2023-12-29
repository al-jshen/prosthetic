import argparse
import joblib
import build_ngrams
from score import score_translation
import string
import random
from tqdm.auto import tqdm
import math
import toml
import munch


def swap_letters(existing, n=1, fixed={}):
    letters = string.ascii_lowercase

    values = [existing[l] for l in letters]

    fixed_indices = []

    if len(fixed) > 0:
        for k, v in fixed.items():
            index = ord(k) - ord("a")
            fixed_indices.append(index)
            values.remove(v)
            values.insert(index, v)

    for _ in range(n):
        i, j = random.sample(
            [x for x in range(len(letters)) if x not in fixed_indices], 2
        )
        values[i], values[j] = values[j], values[i]

    return dict(zip(letters, values))


def search_translations(
    text,
    translation,
    cngram_freq,
    wngram_freq,
    word_freq,
    dictionary,
    iters=10_000,
    swap_schedule=lambda i, t: 1,
    temperature_schedule=lambda i, t: 1.0,
    char_ngram_upweight_schedule=lambda i, t: 1.0,
    word_ngram_upweight_schedule=lambda i, t: 2.0,
    word_upweight_schedule=lambda i, t: 2.0,
    freq_smoothing=1e-5,
    word_freq_smoothing=1e-6,
    fixed=[],
):
    top_5_scores = []
    top_5_translations = []

    score = score_translation(
        text,
        translation,
        cngram_freq,
        wngram_freq,
        word_freq,
        dictionary,
        verbose=False,
        char_ngram_weight=char_ngram_upweight_schedule(0, iters),
        word_ngram_weight=word_ngram_upweight_schedule(0, iters),
        word_weight=word_upweight_schedule(0, iters),
        freq_smoothing=freq_smoothing,
        word_freq_smoothing=word_freq_smoothing,
    )
    logging = dict(
        score=[score],
        temperature=[temperature_schedule(0, iters)],
        char_ngram_upweight=[char_ngram_upweight_schedule(0, iters)],
        word_ngram_upweight=[word_ngram_upweight_schedule(0, iters)],
        word_upweight=[word_upweight_schedule(0, iters)],
    )
    pbar_every = iters // 100
    for i in (pbar := tqdm(range(iters))):
        # test new translation
        translation_new = swap_letters(translation, swap_schedule(i, iters), fixed)
        score_new = score_translation(
            text,
            translation_new,
            cngram_freq,
            wngram_freq,
            word_freq,
            dictionary,
            verbose=False,
            char_ngram_weight=char_ngram_upweight_schedule(i, iters),
            word_ngram_weight=word_ngram_upweight_schedule(i, iters),
            word_weight=word_upweight_schedule(i, iters),
            freq_smoothing=freq_smoothing,
            word_freq_smoothing=word_freq_smoothing,
        )

        try:
            # simulated annealing
            accept_ratio = math.log(score_new / score)
            u = random.uniform(0, 1)
            if u < math.exp(accept_ratio / temperature_schedule(i, iters)):
                translation = translation_new
                score = score_new

                # add score to top 5 scores if it's better than the worst score in the top 5
                # and remove the worst score
                if len(top_5_scores) < 5:
                    top_5_scores.append(score)
                    top_5_translations.append(translation)
                else:
                    if score > min(top_5_scores):
                        if score not in top_5_scores:
                            min_index = top_5_scores.index(min(top_5_scores))
                            top_5_scores[min_index] = score
                            top_5_translations[min_index] = translation
        except:
            # greedy
            if score_new > score:
                translation = translation_new
                score = score_new

                if len(top_5_scores) < 5:
                    top_5_scores.append(score)
                    top_5_translations.append(translation)
                else:
                    if score > min(top_5_scores):
                        if score not in top_5_scores:
                            min_index = top_5_scores.index(min(top_5_scores))
                            top_5_scores[min_index] = score
                            top_5_translations[min_index] = translation

        logging["score"].append(score)
        logging["temperature"].append(temperature_schedule(i, iters))
        logging["char_ngram_upweight"].append(char_ngram_upweight_schedule(i, iters))
        logging["word_ngram_upweight"].append(word_ngram_upweight_schedule(i, iters))
        logging["word_upweight"].append(word_upweight_schedule(i, iters))

        if i % pbar_every == 0:
            pbar.set_description(f"Score: {score}")

    return translation, score, logging, top_5_scores, top_5_translations


def pair(arg):
    return arg.split(",")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Configuration file")
    parsed_args = parser.parse_args()
    args = munch.munchify(toml.load(parsed_args.config))

    cngram_freq = joblib.load(args.ngram_path + "cngrams.joblib")
    wngram_freq = joblib.load(args.ngram_path + "wngrams.joblib")
    word_freq = joblib.load(args.ngram_path + "words.joblib")

    cngram_freq = {
        k: v for k, v in cngram_freq.items() if len(k) <= args.max_char_ngram
    }

    with open(args.dictionary) as f:
        dictionary = set([l.strip() for l in f])

    translation = {l: l for l in string.ascii_lowercase}

    input_text = build_ngrams.filter_text(args.input)

    if len(args.fixed) > 0:
        fixed = {k: v for k, v in map(lambda x: x.split(","), args.fixed.split(" "))}
    else:
        fixed = {}

    translation, score, logging, top_5_scores, top_5_translations = search_translations(
        input_text,
        translation,
        cngram_freq,
        wngram_freq,
        word_freq,
        dictionary,
        iters=args.iters,
        # swap_schedule=lambda i, t: math.ceil(3 - (i / t) * 3),
        swap_schedule=lambda i, t: 1,
        temperature_schedule=lambda i, t: 1
        / (i / (t / args.restarts) + 1)
        / (5 ** (i / (t / args.restarts)))
        * args.max_temp
        * (((i % (t / args.restarts)) / t) + 1) ** (-args.aggression)
        + args.min_temp,
        # temperature_schedule=lambda i, t: math.cos(100 * math.pi * i / t) ** 2 + 0.01,
        char_ngram_upweight_schedule=lambda i, t: args.char_ngram_upweight,
        word_ngram_upweight_schedule=lambda i, t: 0
        if i < t / 5
        else i / t * args.word_ngram_upweight
        if i < 0.6 * t
        else args.word_ngram_upweight,
        word_upweight_schedule=lambda i, t: 0
        if i < t / 5
        else i / t * args.word_upweight
        if i < 0.6 * t
        else args.word_upweight,
        freq_smoothing=args.freq_smoothing,
        word_freq_smoothing=args.word_freq_smoothing,
        fixed=fixed,
    )

    # print(translation)

    print(
        score_translation(
            input_text,
            translation,
            cngram_freq,
            wngram_freq,
            word_freq,
            dictionary,
            verbose=True,
            char_ngram_weight=args.char_ngram_upweight,
            word_ngram_weight=args.word_ngram_upweight,
            word_weight=args.word_upweight,
            freq_smoothing=args.freq_smoothing,
            word_freq_smoothing=args.word_freq_smoothing,
        )
    )

    print(top_5_scores)

    for t in top_5_translations:
        print(args.input.lower().translate(str.maketrans(t)))

    if args.plot:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(5, 1)
        ax[0].plot(logging["score"])
        ax[1].plot(logging["temperature"])
        ax[2].plot(logging["char_ngram_upweight"])
        ax[3].plot(logging["word_ngram_upweight"])
        ax[4].plot(logging["word_upweight"])
        plt.show()
