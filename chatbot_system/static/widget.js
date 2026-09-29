/**
 * widget.js
 * ---------
 * Embeddable chat widget (Task 4: "Integrate the chatbot seamlessly with
 * the target website interface").
 *
 * A site owner adds ONE line to their existing website:
 *
 *   <script src="https://your-chatbot-domain.com/widget.js"
 *           data-api="https://your-chatbot-domain.com"></script>
 *
 * ...and a floating chat bubble appears in the corner, wired up to the
 * /api/chat endpoint, without touching anything else on the host page
 * (scoped inline styles, an isolated container div, no global CSS leaks).
 */
(function () {
  var currentScript = document.currentScript;
  var API_BASE = (currentScript && currentScript.getAttribute("data-api")) || "";
  var sessionId = "web_" + Math.random().toString(36).slice(2);

  var css = `
    #tn-chat-bubble { position: fixed; bottom: 20px; right: 20px; width: 56px; height: 56px;
      border-radius: 50%; background: #2563eb; color: #fff; display: flex; align-items: center;
      justify-content: center; font-size: 26px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,.2);
      z-index: 999999; font-family: sans-serif; }
    #tn-chat-window { position: fixed; bottom: 88px; right: 20px; width: 320px; max-height: 440px;
      background: #fff; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,.25); display: none;
      flex-direction: column; overflow: hidden; z-index: 999999; font-family: sans-serif; }
    #tn-chat-header { background: #2563eb; color: #fff; padding: 12px 16px; font-weight: 600; }
    #tn-chat-messages { flex: 1; padding: 12px; overflow-y: auto; font-size: 14px; }
    .tn-msg { margin-bottom: 10px; max-width: 85%; padding: 8px 12px; border-radius: 10px; line-height: 1.4; }
    .tn-msg.bot { background: #f1f5f9; color: #111; align-self: flex-start; }
    .tn-msg.user { background: #2563eb; color: #fff; margin-left: auto; }
    #tn-chat-input-row { display: flex; border-top: 1px solid #e5e7eb; }
    #tn-chat-input { flex: 1; border: none; padding: 10px; font-size: 14px; outline: none; }
    #tn-chat-send { background: #2563eb; color: #fff; border: none; padding: 0 16px; cursor: pointer; }
  `;
  var styleEl = document.createElement("style");
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  var bubble = document.createElement("div");
  bubble.id = "tn-chat-bubble";
  bubble.innerHTML = "💬";

  var win = document.createElement("div");
  win.id = "tn-chat-window";
  win.innerHTML =
    '<div id="tn-chat-header">Chat with us</div>' +
    '<div id="tn-chat-messages" style="display:flex;flex-direction:column;"></div>' +
    '<div id="tn-chat-input-row">' +
    '<input id="tn-chat-input" placeholder="Type a message..." />' +
    '<button id="tn-chat-send">Send</button>' +
    "</div>";

  document.body.appendChild(bubble);
  document.body.appendChild(win);

  var messagesEl = win.querySelector("#tn-chat-messages");
  var inputEl = win.querySelector("#tn-chat-input");
  var sendBtn = win.querySelector("#tn-chat-send");

  function addMessage(text, sender) {
    var div = document.createElement("div");
    div.className = "tn-msg " + sender;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function toggleWindow() {
    var isOpen = win.style.display === "flex";
    win.style.display = isOpen ? "none" : "flex";
    if (!isOpen && messagesEl.children.length === 0) {
      addMessage("Hi! Ask me about orders, shipping, returns, or anything else.", "bot");
    }
  }

  function sendMessage() {
    var text = inputEl.value.trim();
    if (!text) return;
    addMessage(text, "user");
    inputEl.value = "";

    fetch(API_BASE + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        addMessage(data.response || "Sorry, something went wrong.", "bot");
      })
      .catch(function () {
        addMessage("Sorry, I couldn't reach the server. Please try again.", "bot");
      });
  }

  bubble.addEventListener("click", toggleWindow);
  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendMessage();
  });
})();
