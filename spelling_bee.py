from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from itertools import product
import getpass
import time
import argparse
from tqdm.auto import tqdm


def startswith(x):
    for s in args.startswith:
        if x.startswith(s):
            return True
    return False


def wordfilter(x):
    return args.center_letter in x and len(x) >= 4 and len(x) <= 9 and startswith(x)


def already_found(driver):
    elem = driver.find_element(
        By.XPATH,
        "/html/body/div[2]/div/div[2]/div[2]/div[4]/div[3]/div/div[1]/div[2]/div[2]/div/div[1]/ul",
    )
    children = elem.find_elements(By.TAG_NAME, "li")
    return [child.text for child in children]


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
    wordlist = set()
    for wordlist_file in args.wordlist:
        with open(wordlist_file, "r", errors="ignore") as f:
            wl = f.read().splitlines()
            wordlist.update(set(filter(wordfilter, wl)))

    letters = args.letters + args.center_letter
    combinations = set()

    for i in (pbar := tqdm(range(2, 8))):
        pbar.set_description(f"Generating combinations of length {i + 2}")
        w = set(map(lambda x: "".join(x), product(letters, repeat=i)))
        for s in args.startswith:
            words = map(lambda x: s + x, filter(lambda x: args.center_letter in x, w))
            combinations.update(set(words))

    matches = combinations.intersection(wordlist)

    print(f"Total combinations: {len(combinations)}")
    print(f"Found in wordlist: {len(matches)}")

    driver = webdriver.Chrome()
    driver.get("https://www.nytimes.com/puzzles/spelling-bee")
    time.sleep(1)

    elem = driver.find_element(By.XPATH, "/html/body/header/div[1]/div[2]/a[2]")
    elem.click()
    time.sleep(0.5)

    login(driver)
    _ = input("Press enter to continue")

    elem = driver.find_element(By.XPATH, "//button[@class='pz-moment__button primary']")
    elem.click()
    time.sleep(2)

    body = driver.find_element(By.TAG_NAME, "body")

    for word in matches:
        body.send_keys(word)
        body.send_keys(Keys.RETURN)
        time.sleep(0.0001)

    print(already_found(driver))

    for word in tqdm(combinations):
        body.send_keys(word)
        body.send_keys(Keys.RETURN)
        time.sleep(0.0001)

    _ = input("Press enter to continue")

    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--letters", type=str)
    parser.add_argument("--center_letter", type=str)
    parser.add_argument("--startswith", type=str, nargs="+")
    parser.add_argument("--wordlist", type=str, nargs="+")
    parser.add_argument("--email", type=str)
    args = parser.parse_args()
    password = getpass.getpass()
    main()
