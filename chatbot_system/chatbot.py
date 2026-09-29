"""
chatbot.py
----------
The chatbot's response layer, sitting on top of the trained IntentMatcher.

- Loads the pre-trained model (fast startup, instant per-message response).
- Applies a confidence threshold: low-confidence matches are routed to a
  fallback / human-handoff response instead of guessing wrong -- this is
  the main lever used in test_chatbot.py to "optimize... for accuracy".
- Logs every exchange (with response time) so engagement/accuracy can be
  measured and reported on -- see test_chatbot.py.
"""

import json
import os
import pickle
import random
import time

from nlp_engine import IntentMatcher  # noqa: F401 (needed for unpickling)

CONFIDENCE_THRESHOLD = 0.20  # tuned via the sweep in test_chatbot.py


class ChatBot:
    def __init__(self, intents_path="intents.json", model_path="model.pkl"):
        with open(intents_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.responses_by_tag = {i["tag"]: i["responses"] for i in self.data["intents"]}
        self.fallback_responses = self.data["fallback_responses"]

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"{model_path} not found -- run `python3 train.py` first to train the bot."
            )
        with open(model_path, "rb") as f:
            self.matcher: IntentMatcher = pickle.load(f)

        self.conversation_log = []  # powers the engagement report in test_chatbot.py

    def get_response(self, user_text: str, session_id: str = "default"):
        start = time.perf_counter()
        tag, confidence = self.matcher.match(user_text)

        if confidence < CONFIDENCE_THRESHOLD:
            tag = "fallback"
            response = random.choice(self.fallback_responses)
        else:
            response = random.choice(self.responses_by_tag[tag])

        elapsed_ms = (time.perf_counter() - start) * 1000

        self.conversation_log.append({
            "session_id": session_id,
            "user_text": user_text,
            "matched_intent": tag,
            "confidence": round(confidence, 3),
            "response": response,
            "response_time_ms": round(elapsed_ms, 2),
        })

        return {
            "response": response,
            "intent": tag,
            "confidence": round(confidence, 3),
            "response_time_ms": round(elapsed_ms, 2),
        }
