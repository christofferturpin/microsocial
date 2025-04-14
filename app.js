function isLoggedIn() {
  return !!localStorage.getItem("username");
}

function fakeLogin() {
  const username = prompt("Enter your username:");
  if (!username) return;
  localStorage.setItem("username", username);
  history.pushState({}, "", "/me");
  route();
}

function logout() {
  localStorage.removeItem("username");
  history.pushState({}, "", "/");
  route();
}

function savePage() {
  const content = document.getElementById("editor-text").value;

  fetch("https://127f9tw3s0.execute-api.us-east-1.amazonaws.com/edit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ content })
  })
    .then(res => res.json())
    .then(data => {
      alert("Saved to cloud!");
    })
    .catch(err => {
      console.error("Error saving:", err);
      alert("Failed to save.");
    });
}

function loadEditor() {
  const username = localStorage.getItem("username");
  document.getElementById("editor-username").textContent = username;
  document.getElementById("editor-link").href = `/u/${username}`;
  document.getElementById("editor-link").textContent = `/u/${username}`;

  fetch("https://127f9tw3s0.execute-api.us-east-1.amazonaws.com/me")
    .then(res => {
      if (!res.ok) throw new Error("Not found");
      return res.json();
    })
    .then(data => {
      document.getElementById("editor-text").value = data.content || "";
    })
    .catch(err => {
      document.getElementById("editor-text").value = "";
    });
}

function loadViewer(username) {
  document.getElementById("viewer-username").textContent = username;
  const contentBox = document.getElementById("viewer-content");

  fetch(`https://127f9tw3s0.execute-api.us-east-1.amazonaws.com/u/${username}`)
    .then(res => {
      if (!res.ok) throw new Error("Not found");
      return res.json();
    })
    .then(data => {
      contentBox.textContent = data.content || "(This page is blank.)";
    })
    .catch(err => {
      contentBox.textContent = "User doesn't exist.";
    });
}

function showView(viewName) {
  document.querySelectorAll(".view").forEach(el => el.classList.remove("active"));
  document.getElementById(`view-${viewName}`).classList.add("active");
}

function route() {
  const path = window.location.pathname;

  if (path.startsWith("/u/")) {
    const username = decodeURIComponent(path.substring(3));
    showView("viewer");
    loadViewer(username);
  } else if (path === "/me" && isLoggedIn()) {
    showView("editor");
    loadEditor();
  } else {
    showView("login");
  }
}

// Home navigation override
function goHome(e) {
  e.preventDefault();
  history.pushState({}, "", "/");
  route();
}

// Handle browser nav
window.onpopstate = route;
window.onload = route;
