"""
nlp_engine.py
-------------
Retrieval-based matching engine (Task 4: "using either retrieval-based or
generative models" -- we use retrieval-based: fast, deterministic, and
cheap to run per-request, which is what makes "instant responses" and
commercial deployment practical without hosting a large generative model).

Approach: every predefined pattern from intents.json is embedded with
TF-IDF. An incoming user message is embedded the same way and matched via
cosine similarity against every known pattern. The tag of the closest
pattern is returned, along with a confidence score used to decide whether
to answer or fall back to a human handoff.
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def preprocess(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


class IntentMatcher:
    """Trains (fits) on predefined patterns, then matches new queries against them."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.pattern_vectors = None
        self.pattern_tags = []
        self.patterns = []

    def train(self, intents: list):
        """
        'Train the chatbot with predefined input patterns' -- fits the
        TF-IDF vocabulary and vectors over every pattern in intents.json.
        """
        self.patterns = []
        self.pattern_tags = []
        for intent in intents:
            for pattern in intent["patterns"]:
                self.patterns.append(preprocess(pattern))
                self.pattern_tags.append(intent["tag"])

        self.pattern_vectors = self.vectorizer.fit_transform(self.patterns)
        return self

    def match(self, user_text: str):
        """Returns (best_tag, confidence_score) for the closest known pattern."""
        if self.pattern_vectors is None:
            raise RuntimeError("IntentMatcher.train() must be called before match().")

        query_vec = self.vectorizer.transform([preprocess(user_text)])
        similarities = cosine_similarity(query_vec, self.pattern_vectors)[0]
        best_idx = similarities.argmax()
        return self.pattern_tags[best_idx], float(similarities[best_idx])
