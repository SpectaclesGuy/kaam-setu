(function () {
  const TOKEN_KEY = "kaamsetu_access_token";
  let currentUserPromise = null;

  function getToken() {
    return window.localStorage.getItem(TOKEN_KEY);
  }

  async function parsePayload(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return { detail: await response.text() };
  }

  function activeClass(isActive) {
    return isActive ? "text-pine" : "text-stone-600 hover:text-pine";
  }

  function isActivePath(pathname, href) {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  }

  function link(href, label, pathname) {
    return `<a href="${href}" class="${activeClass(isActivePath(pathname, href))}">${label}</a>`;
  }

  function actionLink(href, label, variant) {
    const classes = variant === "primary"
      ? "rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white"
      : "rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700";
    return `<a href="${href}" class="${classes}">${label}</a>`;
  }

  function actionButton(id, label) {
    return `<button id="${id}" class="rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700">${label}</button>`;
  }

  function primaryButton(id, label) {
    return `<button id="${id}" class="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white">${label}</button>`;
  }

  async function getCurrentUser(force = false) {
    if (!getToken()) return null;
    if (!currentUserPromise || force) {
      currentUserPromise = fetch("/auth/me", {
        headers: { Authorization: `Bearer ${getToken()}` }
      }).then(async (response) => {
        const payload = await parsePayload(response);
        if (!response.ok) throw new Error(payload.detail || payload.message || "Authentication required");
        return payload.data;
      }).catch(() => null);
    }
    return currentUserPromise;
  }

  async function logout() {
    window.localStorage.removeItem(TOKEN_KEY);
    try {
      await fetch("/auth/logout", { method: "POST" });
    } catch {}
    window.location.href = "/";
  }

  function renderNavbar(user, options = {}) {
    const pathname = options.activePath || window.location.pathname;
    const linksNode = document.getElementById("nav-links");
    const actionsNode = document.getElementById("nav-actions");
    if (!linksNode || !actionsNode) return;

    const links = [];
    const actions = [];

    if (!user) {
      links.push(link("/", "Home", pathname));
      links.push(link("/services", "Services", pathname));
      actions.push(pathname === "/profile-setup" ? primaryButton("oauth-start", "Join Us") : actionLink("/profile-setup", "Join Us", "primary"));
    } else if (user.role === "worker") {
      links.push(link("/", "Home", pathname));
      links.push(link("/services", "Services", pathname));
      links.push(link("/worker-jobs", "Nearby Jobs", pathname));
      links.push(link("/worker-dashboard", "Worker Dashboard", pathname));
      links.push(link("/account", "My Account", pathname));
      if (!user.profile_completed) actions.push(actionLink("/profile-setup", "Complete Profile", "primary"));
      actions.push(actionButton("nav-logout", "Logout"));
    } else if (user.role === "admin") {
      links.push(link("/", "Home", pathname));
      links.push(link("/services", "Services", pathname));
      links.push(link("/admin-panel", "Admin Panel", pathname));
      links.push(link("/account", "My Account", pathname));
      actions.push(actionButton("nav-logout", "Logout"));
    } else {
      links.push(link("/", "Home", pathname));
      links.push(link("/services", "Services", pathname));
      links.push(link("/work-requests-app", "Post Work", pathname));
      links.push(link("/account", "My Account", pathname));
      if (!user.profile_completed) actions.push(actionLink("/profile-setup", "Complete Profile", "primary"));
      actions.push(actionButton("nav-logout", "Logout"));
    }

    linksNode.innerHTML = links.join("");
    actionsNode.innerHTML = actions.join("");
    const logoutButton = document.getElementById("nav-logout");
    if (logoutButton) logoutButton.addEventListener("click", logout);
  }

  async function initNavbar(options = {}) {
    const user = await getCurrentUser();
    renderNavbar(user, options);
    return user;
  }

  window.KaramSetuShell = {
    getToken,
    getCurrentUser,
    initNavbar,
    renderNavbar,
    logout,
  };
})();
