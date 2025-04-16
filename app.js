const clientId = "2mmm9c445j7q675u4ufur7099n";
const domain = "us-east-1zyoudaybz.auth.us-east-1.amazoncognito.com";
const redirectUri = window.location.origin;
const loginUrl = `https://${domain}/login?response_type=token&client_id=${clientId}&redirect_uri=${redirectUri}`;
const logoutUrl = `https://${domain}/logout?client_id=${clientId}&logout_uri=${redirectUri}`;

function isLoggedIn() {
  return !!localStorage.getItem("access_token");
}

function login() {
  window.location.href = loginUrl;
}

function logout() {
  localStorage.removeItem("access_token");
  history.pushState({}, "", "/");
  route();
}

function parseTokenFromUrl() {
  const hash = window.location.hash;
  if (hash.includes("access_token")) {
    const params = new URLSearchParams(hash.substring(1));
    const token = params.get("access_token");
    if (token) {
      localStorage.setItem("access_token", token);
      history.replaceState(null, "", "/me");
    }
  }
}

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

function savePage() {
  const content = document.getElementById("editor-text").value;
  const links = Array.from(document.querySelectorAll(".webring-input"))
    .map(input => input.value.trim())
    .filter(link => link.length > 0)
    .slice(0, 5);

  fetch("https://127f9tw3s0.execute-api.us-east-1.amazonaws.com/edit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ content, links })
  })
    .then(res => res.json())
    .then(data => alert("Saved! it may take up 10 seconds for your page to change."))
    .catch(err => {
      console.error("Error saving:", err);
      alert("Failed to save.");
    });
}


function loadEditor() {
  // Decode JWT to extract the username
  const token = localStorage.getItem("access_token");
  let username = "you";

  if (token) {
    const payload = JSON.parse(atob(token.split('.')[1]));
    username = payload["username"] || payload["cognito:username"] || "you";
  }

  document.getElementById("editor-username").textContent = username;
  document.getElementById("editor-link").href = `/u/${username}.html`;
  document.getElementById("editor-link").textContent = `/u/${username}.html`;

  fetch("https://127f9tw3s0.execute-api.us-east-1.amazonaws.com/me", {
    headers: getAuthHeaders()
  })
    .then(res => {
      if (!res.ok) throw new Error("Not found");
      return res.json();
    })
    .then(data => {
      // Set page content
      document.getElementById("editor-text").value = data.content || "";

      // DEBUG
      console.log("DATA FROM /me:", data);

      // Set webring links
      const linkInputs = document.querySelectorAll(".webring-input");
      const links = data.links || [];

      linkInputs.forEach((input, index) => {
        input.value = links[index] || "";
      });
    })
    .catch(err => {
      console.error("Error loading editor:", err);
      document.getElementById("editor-text").value = "";
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

function goHome(e) {
  e.preventDefault();
  history.pushState({}, "", "/");
  route();
}

function getUsernameFromToken() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.username || payload["cognito:username"] || null;
  } catch (err) {
    console.error("Failed to parse JWT:", err);
    return null;
  }
}

function loadDiscoverSection() {
  console.log("Calling /random to load discover section...");
  fetch("https://127f9tw3s0.execute-api.us-east-1.amazonaws.com/random")
    .then(res => {
      console.log("Response status:", res.status);
      return res.json();
    })
    .then(links => {
      console.log("Discover links received:", links);
      const container = document.getElementById("discover-list");
      container.innerHTML = ""; // Clear previous

      links.forEach(link => {
        // Extract username from full URL (assumes /u/username.html)
        const parts = link.split("/");
        const filename = parts[parts.length - 1];
        const username = filename.replace(".html", "");

        console.log("Adding link to DOM:", username);

        const a = document.createElement("a");
        a.href = `https://www.microsocial.link/u/${username}.html`;
        a.textContent = username;
        a.target = "_blank";
        container.appendChild(a);
        container.appendChild(document.createElement("br"));
      });
    })
    .catch(err => {
      console.error("Error loading discover section:", err);
    });
}





window.onpopstate = route;
window.onload = () => {
  parseTokenFromUrl();
  route();
  loadDiscoverSection();
};