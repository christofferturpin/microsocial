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
    const username = localStorage.getItem("username");
    const content = document.getElementById("editor-text").value;
    localStorage.setItem(`page-${username}`, content);
    alert("Saved!");
  }
  
  function loadEditor() {
    const username = localStorage.getItem("username");
    document.getElementById("editor-username").textContent = username;
    document.getElementById("editor-link").href = `/u/${username}`;
    document.getElementById("editor-link").textContent = `/u/${username}`;
  
    const savedContent = localStorage.getItem(`page-${username}`) || "";
    document.getElementById("editor-text").value = savedContent;
  }
  
  function loadViewer(username) {
    document.getElementById("viewer-username").textContent = username;
    const content = localStorage.getItem(`page-${username}`) || "No content found.";
    document.getElementById("viewer-content").textContent = content;
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
  