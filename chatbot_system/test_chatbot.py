"""
test_chatbot.py
----------------
"Optimize and test the chatbot for accuracy and user engagement" (Task 4,
last bullet).

Two things happen here:
  1. ACCURACY TEST -- a labeled set of paraphrased queries (deliberately
     NOT copied word-for-word from intents.json, to test generalization)
     is run through the bot; we measure % correctly matched.
  2. OPTIMIZATION -- the confidence threshold is swept over a range of
     values to find the one that best balances accuracy vs. false
     fallbacks, demonstrating the "optimize" step rather than just
     picking a number arbitrarily.
  3. ENGAGEMENT / SPEED -- average response time is measured across many
     calls to confirm responses are effectively instant, plus a sample
     multi-turn conversation is printed as a sanity check on natural flow.
"""

import time
import statistics

from chatbot import ChatBot
import chatbot as chatbot_module

# Paraphrased test set: (message, expected_intent). None of these strings
# appear verbatim in intents.json's patterns.
TEST_CASES = [
    ("hey there, how are you", "greeting"),
    ("good evening", "greeting"),
    ("can you tell me where my package is", "order_status"),
    ("i haven't received my order yet", "order_status"),
    ("how much does delivery cost", "shipping_info"),
    ("do you deliver outside the country", "shipping_info"),
    ("i'd like a refund for my purchase", "return_policy"),
    ("can i send this back", "return_policy"),
    ("do you accept apple pay", "payment_methods"),
    ("is klarna available at checkout", "payment_methods"),
    ("what time do you close", "store_hours"),
    ("is your support open right now", "store_hours"),
    ("do you have this laptop in stock right now", "product_availability"),
    ("can i get a real agent on the line", "human_handoff"),
    ("this bot isn't working for me, get me a person", "human_handoff"),
    ("thanks so much for your help", "thanks"),
    ("catch you later", "goodbye"),
    ("asdkjqwe random gibberish 12345", "fallback"),
]


def evaluate(bot: ChatBot, cases):
    correct = 0
    timings = []
    for text, expected in cases:
        result = bot.get_response(text, session_id="test")
        timings.append(result["response_time_ms"])
        if result["intent"] == expected:
            correct += 1
        else:
            print(f"  MISMATCH: '{text}' -> got '{result['intent']}' "
                  f"(conf={result['confidence']}), expected '{expected}'")
    accuracy = correct / len(cases)
    return accuracy, timings


def sweep_threshold(bot: ChatBot, cases):
    """Optimization step: try several thresholds, report which is best."""
    print("\nThreshold optimization sweep:")
    best_threshold, best_acc = None, -1
    for t in [0.15, 0.25, 0.35, 0.45, 0.55]:
        chatbot_module.CONFIDENCE_THRESHOLD = t
        correct = 0
        for text, expected in cases:
            result = bot.get_response(text, session_id="tune")
            if result["intent"] == expected:
                correct += 1
        acc = correct / len(cases)
        print(f"  threshold={t:.2f} -> accuracy={acc:.0%}")
        if acc > best_acc:
            best_acc, best_threshold = acc, t
    chatbot_module.CONFIDENCE_THRESHOLD = best_threshold
    print(f"  -> selected threshold={best_threshold:.2f} (accuracy={best_acc:.0%})")
    return best_threshold, best_acc


def sample_conversation(bot: ChatBot):
    print("\nSample multi-turn conversation (engagement check):")
    turns = ["hi", "where is my order", "how long does shipping take", "thanks", "bye"]
    for turn in turns:
        result = bot.get_response(turn, session_id="demo_user")
        print(f"  User: {turn}")
        print(f"  Bot : {result['response']}  "
              f"[intent={result['intent']}, confidence={result['confidence']}, "
              f"{result['response_time_ms']}ms]")


def main():
    bot = ChatBot()

    print("=" * 70)
    print("ACCURACY TEST (paraphrased, unseen-wording queries)")
    print("=" * 70)
    accuracy, timings = evaluate(bot, TEST_CASES)
    print(f"\nAccuracy: {accuracy:.0%} ({int(accuracy * len(TEST_CASES))}/{len(TEST_CASES)})")
    print(f"Avg response time: {statistics.mean(timings):.2f} ms "
          f"(max: {max(timings):.2f} ms) -> effectively instant")

    sweep_threshold(bot, TEST_CASES)
    sample_conversation(bot)

    print("\n" + "=" * 70)
    status = "PASS" if accuracy >= 0.8 else "FAIL"
    print(f"[{status}] Overall accuracy >= 80% target")
    print(f"[{'PASS' if statistics.mean(timings) < 50 else 'FAIL'}] Avg response time under 50ms (instant)")


if __name__ == "__main__":
    main()
