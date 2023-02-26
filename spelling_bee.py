from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from itertools import product, chain
import getpass
import time
import argparse
from tqdm.auto import tqdm
from functools import partial
from joblib import Parallel, delayed
import os
import pickle
import time


def parse_l2(hints):
    l2 = dict()
    for h in hints:
        hh = h.split("-")
        l2[hh[0].lower()] = int(hh[1])
    return l2


def parse_counts(counts):
    cts = dict()
    for c in counts:
        cc = c.split(",")
        letter = cc[0].lower()
        length = int(cc[1])
        count = int(cc[2])
        if letter not in cts.keys():
            cts[letter] = dict()
        cts[letter][length] = count
    return cts


def wordfilter(x, starters):
    return (
        args.center_letter in x
        and len(x) >= 4
        and len(x) <= maxlen
        and set(x).issubset(letters)
        and (x[0] in starters if hintless else x[:2] in starters)
    )


def generate_combinations(l2_counts, counts):
    all_words = set()
    # for each two letter combination
    for l2 in l2_counts.keys():
        # take first letter, check the lengths
        l1 = l2[0]
        for l in counts[l1].keys():
            # generate the back of the word
            w = map(lambda x: l2 + "".join(x), product(letters, repeat=int(l) - 2))
            # join with prefix and keep only words that contain the center letter
            words = filter(lambda x: args.center_letter in x, w)
            all_words.update(set(words))

    return all_words


def generate_combinations_hintless():
    def make_combs(l1, maxlen, letters, center_letter):
        wds = []

        for l in range(4, maxlen + 1):
            w = map(lambda x: l1 + "".join(x), product(letters, repeat=l - 1))
            words = filter(lambda x: center_letter in x, w)
            wds.extend(list(words))
        return wds

    all_words = Parallel(n_jobs=-1)(
        delayed(make_combs)(l1, maxlen, letters, args.center_letter) for l1 in letters
    )

    result = set(chain.from_iterable(all_words))

    return result


def update_counts(word, l2_counts, counts):
    l2 = word[:2]
    if l2 in l2_counts.keys():
        l2_counts[l2] -= 1
        if l2_counts[l2] == 0:
            del l2_counts[l2]
    l1 = word[0]
    l = len(word)
    if l1 in counts.keys():
        if l in counts[l1].keys():
            counts[l1][l] -= 1
            if counts[l1][l] == 0:
                del counts[l1][l]
        if len(counts[l1]) == 0:
            del counts[l1]


def wordlist_filter_hinted(words, l2_counts, counts):
    # words are already
    #   - between 4 and maxlen letters long
    #   - have center letter
    #   - start with an l2
    def criterion(word):
        l2 = word[:2]
        l1 = word[0]
        l = len(word)
        return l2 in l2_counts.keys() and l1 in counts.keys() and l in counts[l1].keys()

    return set(filter(criterion, words))


def get_found(driver):
    elem = driver.find_element(
        By.XPATH,
        "/html/body/div[2]/div/div[2]/div[2]/div[4]/div[3]/div/div[1]/div[2]/div[2]/div/div[1]/ul",
    )
    children = elem.find_elements(By.TAG_NAME, "li")
    return set([child.text.lower() for child in children])


def login(driver):
    email = driver.find_element(
        By.XPATH, "/html/body/div/div/div/div/form/div/div[2]/fieldset/div/div/input"
    )
    email.send_keys(args.email)
    email.submit()
    time.sleep(0.5)
    pw = driver.find_element(
        By.XPATH, "/html/body/div/div/div/form/div/div[1]/fieldset/div/div/input"
    )
    pw.send_keys(password)
    pw.submit()


def main():
    found = set()
    wordlist = set()

    if args.wordlist is not None:
        for wordlist_file in tqdm(args.wordlist, desc="Loading wordlist"):
            with open(wordlist_file, "r", errors="ignore") as f:
                wl = f.read().splitlines()
                wordlist.update(
                    set(
                        filter(
                            partial(
                                wordfilter,
                                starters=letters
                                if hintless
                                else list(l2_counts.keys()),
                            ),
                            wl,
                        )
                    )
                )

    print("Generating combinations...")
    if not hintless:
        if args.wordlist is not None:
            combinations = wordlist_filter_hinted(wordlist, l2_counts, counts)
        else:
            combinations = generate_combinations(l2_counts, counts)
    else:
        combinations = generate_combinations_hintless()

    print("Finding matches in wordlist...")
    matches = combinations.intersection(wordlist)

    print(f"Wordlist size: {len(wordlist)}")
    print(f"Total combinations: {len(combinations)}")
    print(f"Found in wordlist: {len(matches)}")

    if args.mode == "none":
        return

    elif args.mode == "file":
        with open(args.solutions, "r") as f:
            solutions = set([i.lower() for i in f.read().splitlines()])

        print(f"Solutions size: {len(solutions)}")

        for word in matches:
            if word in solutions:
                found.add(word)

        print(f"Found {len(found)} words in wordlist.")

        if not hintless:
            for word in found:
                update_counts(word, l2_counts, counts)
            combinations = generate_combinations(l2_counts, counts)

        print(f"Checking {len(combinations)} combinations.")

        for word in tqdm(combinations):
            if word in solutions:
                found.add(word)
            if len(found) == len(solutions):
                break

        print(f"Found {len(found)}/{len(solutions)} solutions.")

    else:
        if args.mode == "nyt":
            driver = webdriver.Chrome()
            driver.get("https://www.nytimes.com/puzzles/spelling-bee")
            time.sleep(1)

            elem = driver.find_element(By.XPATH, "/html/body/header/div[1]/div[2]/a[2]")
            elem.click()
            time.sleep(0.5)

            login(driver)
            _ = input("Solve CAPTCHA, then press enter")

            elem = driver.find_element(
                By.XPATH, "//button[@class='pz-moment__button primary']"
            )
            elem.click()

            try:
                driver.find_element(By.CLASS_NAME, "pz-moment__close").click()
            except:
                pass

            _ = input("Press enter to begin cracking")

            body = driver.find_element(By.TAG_NAME, "body")

            try:
                found.update(get_found(driver))
                print(f"Already found {len(found)} words...")

                if not hintless:
                    for word in found:
                        update_counts(word, l2_counts, counts)
            except:
                pass

        elif args.mode == "freebee":
            driver = webdriver.Chrome()
            driver.get("https://freebee.fun/play/")

            _ = input("Press enter to begin cracking")

            body = driver.find_element(By.XPATH, "/html/body/div[4]/form/input[1]")

        assert driver is not None
        assert body is not None

        for word in tqdm(matches):
            try:
                body.send_keys(word)
                body.send_keys(Keys.RETURN)
                time.sleep(0.00001)
            except:
                _ = input("Press enter to continue")

        if args.mode == "nyt":
            try:
                found.update(get_found(driver))
                print(f"Found {len(found)} words in wordlist.")
            except:
                pass

        print("Generating combinations based on remaining words...")
        time.sleep(0.2)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("-").key_up(
            Keys.CONTROL
        ).perform()
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("-").key_up(
            Keys.CONTROL
        ).perform()
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("-").key_up(
            Keys.CONTROL
        ).perform()
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("-").key_up(
            Keys.CONTROL
        ).perform()
        time.sleep(0.2)

        if not hintless:
            for word in found:
                update_counts(word, l2_counts, counts)
            combinations = generate_combinations(l2_counts, counts)

        a = input("Press c to continue and anything else to quit")

        if a == "c":
            print(f"Checking {len(combinations)} combinations.")

            for word in tqdm(combinations):
                try:
                    body.send_keys(word)
                    body.send_keys(Keys.RETURN)
                    time.sleep(0.000001)
                except:
                    a = input("Press enter to continue and q to quit")
                    if a == "q":
                        break

            _ = input("Finished. Press enter to end.")

        driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--letters", type=str)
    parser.add_argument("--center_letter", type=str)
    parser.add_argument("--startswith", type=str, nargs="*")
    parser.add_argument("--counts", type=str, nargs="*")
    parser.add_argument("--wordlist", type=str, nargs="+")
    parser.add_argument("--email", type=str, nargs="?")
    parser.add_argument("--solutions", type=str)
    parser.add_argument("--maxlen", type=int, nargs="?")
    parser.add_argument("--mode", type=str, choices=["nyt", "freebee", "file", "none"])
    args = parser.parse_args()
    letters = args.letters + args.center_letter
    if args.solutions is None and args.email is not None:
        password = getpass.getpass()
    if args.startswith is None or args.counts is None:
        assert (
            args.startswith is None and args.counts is None
        ), "Must specify either both or none of --startswith and --counts"
        assert args.maxlen is not None, "Must specify --maxlen if running hintless"
        hintless = True
    else:
        hintless = False
    if not hintless:
        l2_counts = parse_l2(args.startswith)
        counts = parse_counts(args.counts)
        maxlen = 0
        for v in counts.values():
            maxlen = max(maxlen, max(v.keys()))
    else:
        maxlen = args.maxlen
    if args.mode == "file":
        assert (
            args.solutions is not None
        ), "Must specify --solutions if running in file mode"

    print(
        f"""
=== Starting ===
Letters: {args.letters}[{args.center_letter}]
Hintless: {hintless}
Max length: {maxlen}
Using wordlist: {args.wordlist is not None}
Mode: {args.mode}
"""
    )
    main()
