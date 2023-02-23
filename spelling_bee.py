from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from itertools import product
import getpass
import time
import argparse
from tqdm.auto import tqdm
from functools import partial


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
    startswith = False
    for s in starters:
        if x.startswith(s):
            startswith = True
    return args.center_letter in x and len(x) >= 4 and len(x) <= maxlen and startswith


def generate_combinations(l2_counts, counts):
    all_words = set()
    # for each two letter combination
    for l2 in l2_counts.keys():
        # take first letter, check the lengths
        l1 = l2[0]
        for l in counts[l1].keys():
            # generate the back of the word
            w = map(lambda x: "".join(x), product(letters, repeat=int(l) - 2))
            # join with prefix and keep only words that contain the center letter
            words = filter(lambda x: args.center_letter in x, map(lambda x: l2 + x, w))
            all_words.update(set(words))

    return all_words


def generate_combinations_hintless():
    all_words = set()
    for l1 in tqdm(letters, desc="Generating combinations"):
        for l in range(4, maxlen + 1):
            w = map(lambda x: "".join(x), product(letters, repeat=l - 1))
            words = filter(lambda x: args.center_letter in x, map(lambda x: l1 + x, w))
            all_words.update(set(words))
    return all_words


def update_counts(word, l2_counts, counts):
    l2 = word[:2]
    l2_counts[l2] -= 1
    if l2_counts[l2] == 0:
        del l2_counts[l2]
    l1 = word[0]
    l = len(word)
    counts[l1][l] -= 1
    if counts[l1][l] == 0:
        del counts[l1][l]
    if len(counts[l1]) == 0:
        del counts[l1]


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
                                starters=letters if hintless else l2_counts.keys(),
                            ),
                            wl,
                        )
                    )
                )

    if not hintless:
        combinations = generate_combinations(l2_counts, counts)
    else:
        combinations = generate_combinations_hintless()

    matches = combinations.intersection(wordlist)

    print(f"Wordlist size: {len(wordlist)}")
    print(f"Total combinations: {len(combinations)}")
    print(f"Found in wordlist: {len(matches)}")

    if args.solutions is None:
        driver = webdriver.Chrome()
        driver.get("https://www.nytimes.com/puzzles/spelling-bee")
        time.sleep(1)

        elem = driver.find_element(By.XPATH, "/html/body/header/div[1]/div[2]/a[2]")
        elem.click()
        time.sleep(0.5)

        login(driver)
        _ = input("Solve CAPTCHA, then press enter")
        # login(driver)
        # time.sleep(2)

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

        for word in matches:
            body.send_keys(word)
            body.send_keys(Keys.RETURN)
            time.sleep(0.0001)

        found.update(get_found(driver))

        print(f"Found {len(found)} words in wordlist.")

        if not hintless:
            for word in found:
                update_counts(word, l2_counts, counts)
            combinations = generate_combinations(l2_counts, counts)

        print(f"Checking {len(combinations)} combinations.")

        for word in tqdm(combinations):
            body.send_keys(word)
            body.send_keys(Keys.RETURN)
            time.sleep(0.000001)

        _ = input("Finished. Press enter to end.")

        driver.close()

    else:
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
    main()
