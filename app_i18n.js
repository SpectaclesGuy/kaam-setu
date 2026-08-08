(function () {
  const LANGUAGE_KEY = "kaamsetu_language";
  const DEFAULT_LANGUAGE = "en";
  const SUPPORTED_LANGUAGES = {
    en: "English",
    hi: "Hindi",
    pa: "Punjabi",
  };

  const cache = {};
  let currentLanguage = DEFAULT_LANGUAGE;
  let currentMessages = {};

  function detectLanguage() {
    const stored = window.localStorage.getItem(LANGUAGE_KEY);
    if (stored && SUPPORTED_LANGUAGES[stored]) return stored;
    const browserLanguage = (navigator.language || DEFAULT_LANGUAGE).toLowerCase().slice(0, 2);
    return SUPPORTED_LANGUAGES[browserLanguage] ? browserLanguage : DEFAULT_LANGUAGE;
  }

  async function loadLanguage(language) {
    if (cache[language]) return cache[language];
    const response = await fetch(`/locales/${language}.json`);
    if (!response.ok) throw new Error(`Unable to load locale ${language}`);
    const payload = await response.json();
    cache[language] = payload;
    return payload;
  }

  function t(key, fallback = "") {
    if (currentMessages[key] != null) return currentMessages[key];
    if (cache[DEFAULT_LANGUAGE] && cache[DEFAULT_LANGUAGE][key] != null) return cache[DEFAULT_LANGUAGE][key];
    return fallback || key;
  }

  function applyTranslations(root = document) {
    root.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n, node.textContent || "");
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder, node.getAttribute("placeholder") || ""));
    });
    root.querySelectorAll("[data-i18n-html]").forEach((node) => {
      node.innerHTML = t(node.dataset.i18nHtml, node.innerHTML || "");
    });
    document.documentElement.lang = currentLanguage;
  }

  async function syncUserLanguage(language) {
    const token = window.localStorage.getItem("kaamsetu_access_token");
    if (!token) return;
    try {
      await fetch("/auth/me/language", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ preferred_language: language }),
      });
    } catch {}
  }

  async function setLanguage(language, options = {}) {
    const normalized = SUPPORTED_LANGUAGES[language] ? language : DEFAULT_LANGUAGE;
    currentMessages = await loadLanguage(normalized);
    currentLanguage = normalized;

    if (options.persist !== false) {
      window.localStorage.setItem(LANGUAGE_KEY, normalized);
    }
    if (options.syncUser) {
      await syncUserLanguage(normalized);
    }
    if (options.apply !== false) {
      applyTranslations();
    }

    window.dispatchEvent(new CustomEvent("karamsetu:language-changed", { detail: { language: normalized } }));
    return normalized;
  }

  async function init(preferredLanguage) {
    const language = preferredLanguage && SUPPORTED_LANGUAGES[preferredLanguage] ? preferredLanguage : detectLanguage();
    await setLanguage(language, { persist: true, syncUser: false, apply: false });
    return language;
  }

  window.KaramSetuI18n = {
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    init,
    setLanguage,
    applyTranslations,
    t,
    getCurrentLanguage: () => currentLanguage,
  };
})();
