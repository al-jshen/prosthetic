import joblib

ngrams = joblib.load("ngrams.joblib")
print(sorted(ngrams)[:50])
