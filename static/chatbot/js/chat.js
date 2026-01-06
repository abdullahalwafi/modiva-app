document.addEventListener("DOMContentLoaded", function () {
  const chatModal = new bootstrap.Modal(document.getElementById("chatModal"));
  const chatBox = document.getElementById("chat-box");
  const input = document.getElementById("user-input");

  const modelSelect = document.getElementById("model-select"); // ⬅️ pindahkan ke sini
  let selectedModel = "llama3-70b-8192"; // Default model awal

  document.getElementById("openChat").addEventListener("click", function () {
    chatModal.show();
  });

  document.getElementById("sendMessage").addEventListener("click", function () {
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
      .then((res) => res.json())
      .then((data) => appendMessage("ai", data.reply));
  }
});
