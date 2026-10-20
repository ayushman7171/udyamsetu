// ThriveHub Comprehensive Localization Engine (i18n)
// Supports English + 22 Scheduled Indian Languages with RTL Support & English Fallback

(function (window) {
  "use strict";

  const SUPPORTED_LANGUAGES = [
    { code: "en", name: "English", native_name: "English", dir: "ltr", status: "complete" },
    { code: "hi", name: "Hindi", native_name: "हिन्दी", dir: "ltr", status: "complete" },
    { code: "mr", name: "Marathi", native_name: "मराठी", dir: "ltr", status: "complete" },
    { code: "gu", name: "Gujarati", native_name: "ગુજરાતી", dir: "ltr", status: "complete" },
    { code: "bn", name: "Bengali", native_name: "বাংলা", dir: "ltr", status: "complete" },
    { code: "ta", name: "Tamil", native_name: "தமிழ்", dir: "ltr", status: "complete" },
    { code: "te", name: "Telugu", native_name: "తెలుగు", dir: "ltr", status: "complete" },
    { code: "kn", name: "Kannada", native_name: "ಕನ್ನಡ", dir: "ltr", status: "complete" },
    { code: "pa", name: "Punjabi", native_name: "ਪੰਜਾਬੀ", dir: "ltr", status: "complete" },
    { code: "ur", name: "Urdu", native_name: "اردو", dir: "rtl", status: "complete" },
    { code: "or", name: "Odia", native_name: "ଓଡ଼ିଆ", dir: "ltr", status: "partial" },
    { code: "ml", name: "Malayalam", native_name: "മലയാളം", dir: "ltr", status: "partial" },
    { code: "as", name: "Assamese", native_name: "অসমীয়া", dir: "ltr", status: "partial" },
    { code: "mai", name: "Maithili", native_name: "मैथिली", dir: "ltr", status: "partial" },
    { code: "sa", name: "Sanskrit", native_name: "संस्कृतम्", dir: "ltr", status: "partial" },
    { code: "ne", name: "Nepali", native_name: "नेपाली", dir: "ltr", status: "partial" },
    { code: "sat", name: "Santali", native_name: "ᱥᱟᱱᱛᱟᱲᱤ", dir: "ltr", status: "staged" },
    { code: "ks", name: "Kashmiri", native_name: "کٲشُر", dir: "rtl", status: "staged" },
    { code: "sd", name: "Sindhi", native_name: "سنڌي", dir: "rtl", status: "staged" },
    { code: "kok", name: "Konkani", native_name: "कोंकणी", dir: "ltr", status: "staged" },
    { code: "mni", name: "Manipuri", native_name: "ꯃꯤꯇꯩꯂꯣꯟ", dir: "ltr", status: "staged" },
    { code: "br", name: "Bodo", native_name: "बड़ो", dir: "ltr", status: "staged" },
    { code: "doi", name: "Dogri", native_name: "डोगरी", dir: "ltr", status: "staged" }
  ];

  const STORAGE_KEY = "thrivehub_language";
  const LEGACY_STORAGE_KEY = "udyamsetu_language";
  const RTL_LANGUAGES = ["ur", "ks", "sd"];

  class I18nEngine {
    constructor() {
      this.supportedLanguages = SUPPORTED_LANGUAGES;
      this.translations = {}; // langCode -> translationsObject
      this.currentLanguage = this.detectInitialLanguage();
      this.isInitialized = false;
      this._initPromise = null;
    }

    detectInitialLanguage() {
      try {
        const stored = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_STORAGE_KEY);
        if (stored && this.isSupported(stored)) {
          return stored;
        }
      } catch (e) {}

      // Fallback to English
      return "en";
    }

    isSupported(code) {
      return this.supportedLanguages.some(l => l.code === code);
    }

    getLanguageInfo(code) {
      return this.supportedLanguages.find(l => l.code === (code || this.currentLanguage)) || this.supportedLanguages[0];
    }

    isRTL(code) {
      const info = this.getLanguageInfo(code);
      return info && info.dir === "rtl";
    }

    async init() {
      if (this.isInitialized) return true;
      if (this._initPromise) return this._initPromise;

      this._initPromise = (async () => {
        // Ensure base English dictionary is always loaded for fallback
        await this.loadLocale("en");
        if (this.currentLanguage !== "en") {
          await this.loadLocale(this.currentLanguage);
        }

        this.applyDirectionAndLang(this.currentLanguage);
        this.isInitialized = true;
        this.translatePage();

        return true;
      })();

      return this._initPromise;
    }

    async loadLocale(code) {
      if (this.translations[code]) return this.translations[code];

      try {
        const res = await fetch(`/locales/${code}.json`);
        if (!res.ok) {
          throw new Error(`Failed to load locale ${code}: ${res.status}`);
        }
        const data = await res.json();
        this.translations[code] = data;
        return data;
      } catch (err) {
        console.warn(`[i18n] Warning: could not load ${code}.json, falling back to English.`, err);
        return null;
      }
    }

    applyDirectionAndLang(code) {
      const info = this.getLanguageInfo(code);
      const dir = (info && info.dir) || "ltr";
      document.documentElement.setAttribute("lang", code);
      document.documentElement.setAttribute("dir", dir);
      if (dir === "rtl") {
        document.documentElement.classList.add("rtl-mode");
      } else {
        document.documentElement.classList.remove("rtl-mode");
      }
    }

    // Translation Key Lookup with Nested Dot Notation & English Fallback
    t(key, params, fallback) {
      if (!key) return "";
      const path = key.split(".");

      // 1. Try in current language
      let val = this._lookupKey(this.translations[this.currentLanguage], path);

      // Check if translation is missing in current language for audit reporting
      if ((val === undefined || val === null || val === "") && this.currentLanguage !== "en") {
        const langInfo = this.getLanguageInfo(this.currentLanguage);
        if (langInfo && langInfo.status === "complete") {
          if (!this._missingKeys) this._missingKeys = new Set();
          const reportKey = `${this.currentLanguage}:${key}`;
          if (!this._missingKeys.has(reportKey)) {
            this._missingKeys.add(reportKey);
            console.warn(`[i18n AUDIT] Missing translation for required interface key "${key}" in complete language "${this.currentLanguage}" (${langInfo.name})`);
          }
        }
      }

      // 2. Fallback to English if missing, empty, or equal to key
      if (val === undefined || val === null || val === "") {
        val = this._lookupKey(this.translations["en"], path);
      }

      // 3. Fallback string if still not found
      if (val === undefined || val === null || val === "") {
        val = fallback !== undefined ? fallback : key;
      }

      // String interpolation if params provided
      if (typeof val === "string" && params && typeof params === "object") {
        Object.keys(params).forEach(p => {
          val = val.replace(new RegExp(`\\{${p}\\}`, "g"), params[p]);
        });
      }

      return val;
    }

    getMissingKeys() {
      return Array.from(this._missingKeys || []);
    }

    // Localize Indian location string (e.g. "Varanasi, Uttar Pradesh" -> "Varanasi, उत्तर प्रदेश")
    // Preserves district/city/local names while localizing recognized state names
    localizeLocation(locStr, stateStr) {
      if (!locStr && !stateStr) return "";
      if (this.currentLanguage === "en") return locStr || stateStr || "";

      // Case 1: locStr is "District, State"
      if (locStr && locStr.includes(",")) {
        const parts = locStr.split(",").map(s => s.trim());
        const district = parts[0];
        const state = parts[1];
        const stateTrans = this.t("states." + state, {}, state);
        return `${district}, ${stateTrans}`;
      }

      // Case 2: stateStr provided explicitly
      if (stateStr) {
        const stateTrans = this.t("states." + stateStr, {}, stateStr);
        if (locStr && locStr !== stateStr) {
          return `${locStr}, ${stateTrans}`;
        }
        return stateTrans;
      }

      // Case 3: locStr alone matches state name
      if (locStr) {
        return this.t("states." + locStr, {}, locStr);
      }

      return locStr || "";
    }

    _lookupKey(dict, path) {
      if (!dict) return undefined;
      let curr = dict;
      for (const segment of path) {
        if (curr && typeof curr === "object" && segment in curr) {
          curr = curr[segment];
        } else {
          return undefined;
        }
      }
      return curr;
    }

    async setLanguage(newCode, syncToUser = true) {
      if (!this.isSupported(newCode)) {
        console.error(`[i18n] Unsupported language: ${newCode}`);
        return false;
      }

      const previousLanguage = this.currentLanguage;
      this.currentLanguage = newCode;

      try {
        localStorage.setItem(STORAGE_KEY, newCode);
        localStorage.setItem(LEGACY_STORAGE_KEY, newCode);
      } catch (e) {}

      // Load dictionary if needed
      await this.loadLocale(newCode);

      // Update DOM direction and lang attributes
      this.applyDirectionAndLang(newCode);

      // Translate all marked elements on page
      this.translatePage();

      // Sync with user's backend profile if authenticated
      if (syncToUser && window.CURRENT_USER) {
        this.syncLanguageWithBackend(newCode);
      }

      // Dispatch event for UI listeners
      const event = new CustomEvent("i18n:languageChanged", {
        detail: {
          previousLanguage,
          language: newCode,
          info: this.getLanguageInfo(newCode)
        }
      });
      window.dispatchEvent(event);

      return true;
    }

    syncLanguageWithBackend(code) {
      fetch("/api/user/language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: code })
      }).catch(err => {
        console.warn("[i18n] Failed to sync language with backend account:", err);
      });
    }

    // Translates all elements with data-i18n* attributes
    translatePage(rootElement = document) {
      // 1. Text & HTML content
      const elements = rootElement.querySelectorAll("[data-i18n]");
      elements.forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (!key) return;
        const translated = this.t(key);
        // Only set textContent to prevent HTML injection in translated strings
        el.textContent = translated;
      });

      // 2. Placeholders
      const placeholders = rootElement.querySelectorAll("[data-i18n-placeholder]");
      placeholders.forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (!key) return;
        el.placeholder = this.t(key);
      });

      // 3. Titles / tooltips
      const titles = rootElement.querySelectorAll("[data-i18n-title]");
      titles.forEach(el => {
        const key = el.getAttribute("data-i18n-title");
        if (!key) return;
        el.title = this.t(key);
      });

      // 4. ARIA labels
      const ariaLabels = rootElement.querySelectorAll("[data-i18n-aria]");
      ariaLabels.forEach(el => {
        const key = el.getAttribute("data-i18n-aria");
        if (!key) return;
        el.setAttribute("aria-label", this.t(key));
      });

      // 5. Update any language selector labels on page
      this.updateLanguageSelectors();
    }

    // Creates the HTML string for a language dropdown selector
    renderLanguageSelectorHTML(id = "headerLangSelector", extraClasses = "") {
      const current = this.getLanguageInfo(this.currentLanguage);
      return `
        <div class="lang-selector-wrapper ${extraClasses}" id="${id}Wrapper">
          <button type="button" class="lang-selector-btn" id="${id}Btn" aria-label="Select Language" title="Select Language / भाषा चुनें">
            <svg class="lang-globe-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
            <span class="lang-current-label">${current.native_name}</span>
            <svg class="lang-chevron-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
          <div class="lang-dropdown-menu" id="${id}Menu" style="display: none;">
            <div class="lang-dropdown-header">
              <span class="lang-dropdown-title" data-i18n="nav.switch_language">Switch Language / भाषा</span>
            </div>
            <div class="lang-dropdown-list">
              ${this.supportedLanguages.map(l => `
                <button type="button" class="lang-option-btn ${l.code === this.currentLanguage ? 'active' : ''}" data-lang="${l.code}">
                  <span class="lang-opt-native">${l.native_name}</span>
                  <span class="lang-opt-name">${l.name}</span>
                  ${l.dir === 'rtl' ? '<span class="lang-opt-badge">RTL</span>' : ''}
                </button>
              `).join("")}
            </div>
          </div>
        </div>
      `;
    }

    // Attach click events to all language selector instances
    bindLanguageSelectors() {
      document.querySelectorAll(".lang-selector-wrapper").forEach(wrapper => {
        const btn = wrapper.querySelector(".lang-selector-btn");
        const menu = wrapper.querySelector(".lang-dropdown-menu");
        if (!btn || !menu) return;

        // Toggle dropdown
        btn.onclick = (e) => {
          e.stopPropagation();
          const isVisible = menu.style.display === "block";
          // Close any other open lang menus
          document.querySelectorAll(".lang-dropdown-menu").forEach(m => m.style.display = "none");
          menu.style.display = isVisible ? "none" : "block";
        };

        // Select option
        menu.querySelectorAll(".lang-option-btn").forEach(opt => {
          opt.onclick = (e) => {
            e.stopPropagation();
            const langCode = opt.getAttribute("data-lang");
            menu.style.display = "none";
            this.setLanguage(langCode);
          };
        });
      });

      // Close dropdowns on outside click
      if (!window._langOutsideClickBound) {
        document.addEventListener("click", () => {
          document.querySelectorAll(".lang-dropdown-menu").forEach(m => m.style.display = "none");
        });
        window._langOutsideClickBound = true;
      }
    }

    updateLanguageSelectors() {
      const current = this.getLanguageInfo(this.currentLanguage);
      document.querySelectorAll(".lang-selector-wrapper").forEach(wrapper => {
        const label = wrapper.querySelector(".lang-current-label");
        if (label) label.textContent = current.native_name;
        wrapper.querySelectorAll(".lang-option-btn").forEach(opt => {
          if (opt.getAttribute("data-lang") === this.currentLanguage) {
            opt.classList.add("active");
          } else {
            opt.classList.remove("active");
          }
        });
      });
    }

    // User-Generated Content (UGC) Translation Toggle Helper
    // Displays translated preview while preserving original text
    setupUGCTranslateToggle(containerEl, originalText, sourceLang = "auto") {
      if (!containerEl || !originalText) return;

      const toggleWrapper = document.createElement("div");
      toggleWrapper.className = "ugc-translate-wrap";

      const currentLangInfo = this.getLanguageInfo(this.currentLanguage);
      const targetLangName = currentLangInfo.native_name;

      toggleWrapper.innerHTML = `
        <button type="button" class="ugc-translate-btn" title="Translate content preview">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 8l6 6"></path><path d="M4 14l6-6 2-3"></path><path d="M2 5h12"></path><path d="M7 2h1"></path><path d="M22 22l-5-10-5 10"></path><path d="M14 18h6"></path>
          </svg>
          <span class="ugc-btn-text">${this.t("common.translate_toggle", { lang: targetLangName }, `Translate to ${targetLangName}`)}</span>
        </button>
        <div class="ugc-translated-box" style="display: none;"></div>
      `;

      const btn = toggleWrapper.querySelector(".ugc-translate-btn");
      const box = toggleWrapper.querySelector(".ugc-translated-box");
      let isTranslated = false;

      btn.onclick = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (isTranslated) {
          // Revert to original
          box.style.display = "none";
          btn.querySelector(".ugc-btn-text").textContent = this.t("common.translate_toggle", { lang: targetLangName }, `Translate to ${targetLangName}`);
          isTranslated = false;
        } else {
          // Request translated preview
          btn.querySelector(".ugc-btn-text").textContent = this.t("common.loading", {}, "Loading...");
          try {
            const res = await fetch("/api/translate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                text: originalText,
                source_lang: sourceLang,
                target_lang: this.currentLanguage
              })
            });
            const data = await res.json();
            if (data.success) {
              box.innerHTML = `
                <div class="ugc-translated-text">${data.translated_text}</div>
                <div class="ugc-translated-note">${this.t("common.translated_notice", {}, "Machine-translated preview. Original content remains unchanged.")}</div>
              `;
              box.style.display = "block";
              btn.querySelector(".ugc-btn-text").textContent = this.t("common.show_original", { origLang: "Original" }, "Show original");
              isTranslated = true;
            } else {
              throw new Error(data.error || "Failed");
            }
          } catch (err) {
            box.innerHTML = `<div class="ugc-translated-error">${this.t("common.translation_unavailable", {}, "Translation service preview unavailable.")}</div>`;
            box.style.display = "block";
            btn.querySelector(".ugc-btn-text").textContent = this.t("common.retry", {}, "Retry");
          }
        }
      };

      containerEl.appendChild(toggleWrapper);
    }
  }

  // Create global instance
  window.i18n = new I18nEngine();

  // Auto-init as soon as DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => window.i18n.init());
  } else {
    window.i18n.init();
  }

})(window);
