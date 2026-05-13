document.addEventListener("DOMContentLoaded", function () {
  const chatModalEl = document.getElementById("chatModal");
  const chatBox = document.getElementById("chat-box");
  const input = document.getElementById("user-input");
  const openBtn = document.getElementById("openChat");
  const sendBtn = document.getElementById("sendMessage");

  if (!chatModalEl || !chatBox || !input || !openBtn || !sendBtn) return;

  let chatModal = null;
  if (window.bootstrap && typeof window.bootstrap.Modal === "function" && chatModalEl.classList.contains("modal")) {
    chatModal = new window.bootstrap.Modal(chatModalEl);
  }

  const modelSelect = document.getElementById("model-select"); // ⬅️ pindahkan ke sini
  let selectedModel = "llama3-70b-8192"; // Default model awal

  openBtn.addEventListener("click", function () {
    if (chatModal) {
      chatModal.show();
    } else {
      chatModalEl.style.display = "flex";
    }
  });

  sendBtn.addEventListener("click", function () {
    sendMessage();
  });

  input.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      sendMessage();
    }
  });

  function appendMessage(role, message) {
    const div = document.createElement("div");
    div.className =
      role === "user" ? "user-msg mb-2" : "ai-msg mb-2 text-muted";

    if (role === "user") {
      // User tetap pakai teks biasa
      div.textContent = "Anda: " + message;
    } else {
      // AI → render HTML
      div.innerHTML = "<strong>AI:</strong> " + message;
    }

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  const modelLabel = document.getElementById("selected-model-label");
  document.querySelectorAll(".model-icon").forEach((icon) => {
    icon.addEventListener("click", function () {
      document
        .querySelectorAll(".model-icon")
        .forEach((i) => i.classList.remove("selected"));
      this.classList.add("selected");
      selectedModel = this.dataset.model;
      modelLabel.textContent = this.title;
      console.log("Model dipilih:", selectedModel);
    });
  });

  function sendMessage() {
    const message = input.value.trim();
    if (!message) return;
    appendMessage("user", message);
    input.value = "";

    // alert("Model yang dipilih: " + selectedModel);

    const formattedMessage = "jawab dalam bahasa indonesia. " + message;

    fetch("/chat-api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: formattedMessage,
        model: selectedModel, // Ambil dari icon klik
      }),
    })
      .then(async (res) => {
        const contentType = res.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
          const rawText = await res.text();
          throw new Error(rawText || `HTTP ${res.status}`);
        }

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.reply || data.message || `HTTP ${res.status}`);
        }
        return data;
      })
      .then((data) => {
        appendMessage("ai", data.reply || "Maaf, tidak ada balasan.");
      })
      .catch((error) => {
        console.error("Chat error:", error);
        appendMessage(
          "ai",
          "Maaf, chatbot sedang bermasalah. Coba refresh halaman atau restart server. " +
            (error && error.message ? `<br><small>${error.message}</small>` : "")
        );
      });
  }
});
