"""
app.py
------
Flask backend (Task 4: "instant responses to user queries on websites" +
"integrate seamlessly with the target website interface").

The ChatBot is loaded ONCE at process startup (not per-request), which is
what makes each /api/chat call fast. This same process also serves
widget.js -- a small embeddable script any website can drop in via a
single <script> tag to get a working chat bubble wired up to this API.

Run:
    python3 train.py     # one-time: fit the model on intents.json
    python3 app.py        # start the server on http://localhost:5000

Then open http://localhost:5000/demo to see the widget running on a
sample "customer" website.
"""

from flask import Flask, request, jsonify, send_from_directory
import os

from chatbot import ChatBot

app = Flask(__name__, static_folder="static")
bot = ChatBot()  # loaded once at startup -> subsequent requests are instant


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = payload.get("session_id", "anonymous")

    if not message:
        return jsonify({"error": "Missing 'message' field."}), 400

    result = bot.get_response(message, session_id=session_id)
    return jsonify(result)


@app.route("/widget.js")
def widget_js():
    return send_from_directory("static", "widget.js", mimetype="application/javascript")


@app.route("/demo")
def demo_page():
    return send_from_directory("static", "demo.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "intents_loaded": len(bot.responses_by_tag)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
