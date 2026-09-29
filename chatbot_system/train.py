"""
train.py
--------
Explicit training step (Task 4: "Train the chatbot with predefined input
patterns for commercial use").

Fits the IntentMatcher once on intents.json and pickles the result to
model.pkl. In production, app.py loads this pickle at startup instead of
re-fitting on every request/process restart -- this is what keeps
per-message response latency near-instant (no training cost on the
request path) and is the standard pattern for deploying a retrieval-based
bot commercially.
"""

import json
import pickle

from nlp_engine import IntentMatcher

INTENTS_PATH = "intents.json"
MODEL_PATH = "model.pkl"


def train_and_save():
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    matcher = IntentMatcher()
    matcher.train(data["intents"])

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(matcher, f)

    print(f"Trained on {len(matcher.patterns)} predefined patterns "
          f"across {len(set(matcher.pattern_tags))} intents.")
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save()
