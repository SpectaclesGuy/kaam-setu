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

  function t(key, fallback) {
    return window.KaramSetuI18n ? window.KaramSetuI18n.t(key, fallback) : fallback;
  }

  function link(href, labelKey, pathname, fallback) {
    const label = t(labelKey, fallback);
    return `<a href="${href}" class="${activeClass(isActivePath(pathname, href))}">${label}</a>`;
  }

  function actionLink(href, labelKey, variant, fallback) {
    const label = t(labelKey, fallback);
    const classes = variant === "primary"
      ? "rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white"
      : "rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700";
    return `<a href="${href}" class="${classes}">${label}</a>`;
  }

  function actionButton(id, labelKey, fallback) {
    const label = t(labelKey, fallback);
    return `<button id="${id}" class="rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700">${label}</button>`;
  }

  function primaryButton(id, labelKey, fallback) {
    const label = t(labelKey, fallback);
    return `<button id="${id}" class="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white">${label}</button>`;
  }

  function languageSelector() {
    const currentLanguage = window.KaramSetuI18n?.getCurrentLanguage?.() || "en";
    const options = Object.entries(window.KaramSetuI18n?.SUPPORTED_LANGUAGES || {}).map(([code, label]) => `
      <option value="${code}" ${code === currentLanguage ? "selected" : ""}>${label}</option>
    `).join("");
    return `
      <label class="flex items-center gap-2 rounded-full border border-stone-300 bg-white px-3 py-2 text-sm text-stone-700">
        <span class="hidden sm:inline">${t("lang.label", "Language")}</span>
        <select id="language-switcher" class="bg-transparent text-sm font-medium outline-none">
          ${options}
        </select>
      </label>
    `;
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

    linksNode.className = "flex flex-wrap items-center gap-4 text-sm font-medium md:gap-6";
    actionsNode.className = "flex flex-wrap items-center gap-3";

    const links = [];
    const actions = [];
    actions.push(languageSelector());

    if (!user) {
      links.push(link("/", "nav.home", pathname, "Home"));
      links.push(link("/services", "nav.services", pathname, "Services"));
      actions.push(pathname === "/profile-setup" ? primaryButton("oauth-start", "nav.join_us", "Join Us") : actionLink("/profile-setup", "nav.join_us", "primary", "Join Us"));
    } else if (user.role === "worker") {
      links.push(link("/", "nav.home", pathname, "Home"));
      links.push(link("/services", "nav.services", pathname, "Services"));
      links.push(link("/worker-jobs", "nav.nearby_jobs", pathname, "Nearby Jobs"));
      links.push(link("/worker-dashboard", "nav.worker_dashboard", pathname, "Worker Dashboard"));
      links.push(link("/account", "nav.my_account", pathname, "My Account"));
      if (!user.profile_completed) actions.push(actionLink("/profile-setup", "nav.complete_profile", "primary", "Complete Profile"));
      actions.push(actionButton("nav-logout", "nav.logout", "Logout"));
    } else if (user.role === "admin") {
      links.push(link("/", "nav.home", pathname, "Home"));
      links.push(link("/services", "nav.services", pathname, "Services"));
      links.push(link("/admin-panel", "nav.admin_panel", pathname, "Admin Panel"));
      links.push(link("/account", "nav.my_account", pathname, "My Account"));
      actions.push(actionButton("nav-logout", "nav.logout", "Logout"));
    } else {
      links.push(link("/", "nav.home", pathname, "Home"));
      links.push(link("/services", "nav.services", pathname, "Services"));
      links.push(link("/work-requests-app", "nav.post_work", pathname, "Post Work"));
      links.push(link("/account", "nav.my_account", pathname, "My Account"));
      if (!user.profile_completed) actions.push(actionLink("/profile-setup", "nav.complete_profile", "primary", "Complete Profile"));
      actions.push(actionButton("nav-logout", "nav.logout", "Logout"));
    }

    linksNode.innerHTML = links.join("");
    actionsNode.innerHTML = actions.join("");
    const languageSwitcher = document.getElementById("language-switcher");
    if (languageSwitcher) {
      languageSwitcher.addEventListener("change", async (event) => {
        const nextLanguage = event.target.value;
        await window.KaramSetuI18n.setLanguage(nextLanguage, { persist: true, syncUser: Boolean(user), apply: true });
        renderNavbar(user, options);
        window.KaramSetuI18n.applyTranslations();
        window.location.reload();
      });
    }
    const logoutButton = document.getElementById("nav-logout");
    if (logoutButton) logoutButton.addEventListener("click", logout);
  }

  async function initNavbar(options = {}) {
    await window.KaramSetuI18n?.init?.();
    const user = await getCurrentUser();
    if (user?.preferred_language && window.KaramSetuI18n?.getCurrentLanguage?.() !== user.preferred_language) {
      await window.KaramSetuI18n.setLanguage(user.preferred_language, { persist: true, syncUser: false, apply: false });
    }
    renderNavbar(user, options);
    window.KaramSetuI18n?.applyTranslations?.();
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
