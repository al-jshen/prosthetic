import joblib
import pprint

cngrams = joblib.load("cngrams.joblib")
wngrams = joblib.load("wngrams.joblib")
words = joblib.load("words.joblib")

scngrams = sorted(cngrams.items(), key=lambda x: x[1], reverse=True)
swngrams = sorted(wngrams.items(), key=lambda x: x[1], reverse=True)
sword = sorted(words.items(), key=lambda x: x[1], reverse=True)

for n in range(1, 6):
    print("Top 10 character-level {}-grams:".format(n))
    pprint.pprint([x for x in scngrams if len(x[0]) == n][:10])

for n in range(1, 4):
    print("Top 10 word-level {}-grams:".format(n))
    pprint.pprint([x for x in swngrams if len(x[0].split(" ")) == n][:10])

print("Top 10 words:")
pprint.pprint(sword[:10])
