// ThriveHub Main Interactive Logic with Flask & SQLite Backend Integration

window.CURRENT_USER = null;
window.CSRF_TOKEN = null;

// Wrap window.fetch to automatically include CSRF token for state-changing requests
const _originalFetch = window.fetch;
window.fetch = function (url, options = {}) {
  options = options || {};
  if (options.method && ["POST", "PUT", "DELETE"].includes(options.method.toUpperCase())) {
    if (!options.headers) {
      options.headers = {};
    }
    if (!(options.headers instanceof Headers)) {
      if (window.CSRF_TOKEN && !options.headers["X-CSRF-Token"]) {
        options.headers["X-CSRF-Token"] = window.CSRF_TOKEN;
      }
    }
  }
  return _originalFetch(url, options);
};

document.addEventListener("DOMContentLoaded", function () {
  initMobileNav();
  initGlobalModals();

  // Initialize session first, then initialize page-specific logic
  initAuthSession().then(() => {
    initDirectoryPage();
    initDashboardFeed();
    initProfilePage();
    initCollaborationsPage();
    initCreateCollabPage();
    initDiscussionPage();
    initLearnPage();
    initAuthPage();
    initMessagesPage();
    initNotificationsPage();
  });
});

// -----------------------------------------------------------------------------
// Toast Notification Utility
// -----------------------------------------------------------------------------
function showToast(message) {
  let toast = document.getElementById("toastNotice");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toastNotice";
    toast.className = "toast-notice";
    document.body.appendChild(toast);
  }
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
      <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
    <span>${message}</span>
  `;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3200);
}

function getInitials(name) {
  if (!name) return "US";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// -----------------------------------------------------------------------------
// Mobile Nav Toggle
// -----------------------------------------------------------------------------
function initMobileNav() {
  const toggleBtn = document.querySelector(".mobile-menu-btn");
  const navMenu = document.querySelector(".nav-menu");
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener("click", function () {
      let drawer = document.querySelector(".mobile-drawer");
      if (!drawer) {
        drawer = document.createElement("div");
        drawer.className = "mobile-drawer";
        drawer.innerHTML = navMenu.innerHTML;
        document.querySelector(".site-header").appendChild(drawer);
      } else {
        drawer.style.display = drawer.style.display === "none" ? "flex" : "none";
      }
    });
  }
}

// -----------------------------------------------------------------------------
// Global Authentication State & Dynamic Navigation
// -----------------------------------------------------------------------------
function initAuthSession() {
  // 1. Check Supabase Auth session if client is available
  if (window.supabaseClient && window.UdyamAuth) {
    return window.supabaseClient.auth.getSession()
      .then(async ({ data: { session } }) => {
        if (session && session.user) {
          const profile = await window.UdyamAuth.getProfile(session.user.id);
          window.CURRENT_USER = profile || {
            id: session.user.id,
            user_id: session.user.user_metadata?.slug || session.user.id,
            slug: session.user.user_metadata?.slug || session.user.id,
            name: session.user.user_metadata?.name || session.user.email.split("@")[0],
            email: session.user.email,
            account_type: session.user.user_metadata?.account_type || "entrepreneur",
            avatar: session.user.user_metadata?.avatar || "assets/images/digital_rahul.jpg"
          };
          if (window.CURRENT_USER.preferred_language && window.i18n) {
            if (window.i18n.currentLanguage !== window.CURRENT_USER.preferred_language) {
              window.i18n.setLanguage(window.CURRENT_USER.preferred_language, false);
            }
          }
          updateGlobalNavigation(window.CURRENT_USER);
          return window.CURRENT_USER;
        }
        return checkFlaskSession();
      })
      .catch(() => checkFlaskSession());
  }

  return checkFlaskSession();
}

function checkFlaskSession() {
  return fetch("/api/me")
    .then(r => r.json())
    .then(data => {
      if (data && data.csrf_token) {
        window.CSRF_TOKEN = data.csrf_token;
      }
      if (data && data.authenticated && data.user) {
        window.CURRENT_USER = data.user;
        if (window.CURRENT_USER.preferred_language && window.i18n) {
          if (window.i18n.currentLanguage !== window.CURRENT_USER.preferred_language) {
            window.i18n.setLanguage(window.CURRENT_USER.preferred_language, false);
          }
        }
      } else {
        window.CURRENT_USER = null;
      }
      updateGlobalNavigation(window.CURRENT_USER);
    })
    .catch(() => {
      window.CURRENT_USER = null;
      updateGlobalNavigation(null);
    });
}

function updateGlobalNavigation(user) {
  const headerActions = document.getElementById("globalHeaderActions");
  if (!headerActions) return;

  const currentPath = window.location.pathname.toLowerCase();
  const isDirectoryPage = currentPath.includes("directory");
  const langHtml = window.i18n ? window.i18n.renderLanguageSelectorHTML("headerLangSelector") : "";

  if (user) {
    // Authenticated Navigation
    const initials = getInitials(user.name);
    headerActions.innerHTML = `
      ${!isDirectoryPage ? `
        <a href="directory.html" class="header-icon-btn" title="Search Directory" data-i18n-title="nav.search_directory">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </a>
      ` : ''}
      <a href="messages.html" class="header-icon-btn" title="Messages" data-i18n-title="nav.messages" style="position: relative;">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
        <span class="notif-badge" id="globalMsgBadge" style="display: none;"></span>
      </a>
      <div class="notifications-wrapper" style="position: relative;">
        <button class="header-icon-btn" id="notifBellBtn" title="Notifications" data-i18n-title="nav.notifications" aria-label="Notifications" onclick="window.toggleNotificationsDropdown(event)">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
          <span class="notif-badge" id="globalNotifBadge" style="display: none;"></span>
        </button>
        <div id="notifDropdown" class="notif-dropdown" style="display: none;">
          <div class="notif-dropdown-header">
            <div class="notif-dropdown-title">
              <span data-i18n="nav.notifications">Notifications</span>
              <span class="notif-unread-count-pill" id="notifDropdownUnreadCount" style="display: none;">0 unread</span>
            </div>
            <button type="button" class="notif-mark-all-btn" onclick="window.markAllNotificationsRead(event)" title="Mark all as read" data-i18n="notif.mark_all_read">
              Mark all read
            </button>
          </div>
          <div class="notif-tabs">
            <button type="button" class="notif-tab active" data-tab="all" onclick="window.switchNotifTab('all')" data-i18n="notif.all">All</button>
            <button type="button" class="notif-tab" data-tab="unread" onclick="window.switchNotifTab('unread')" data-i18n="notif.unread_tab">Unread</button>
          </div>
          <div class="notif-dropdown-body" id="notifDropdownList">
            <div class="notif-loading-state">
              <div class="spinner"></div>
              <span style="font-size: 13px; color: var(--text-muted); margin-top: 6px;" data-i18n="common.loading">Loading notifications...</span>
            </div>
          </div>
          <div class="notif-dropdown-footer">
            <a href="notifications.html" class="notif-see-all-link" data-i18n="notif.view_all">View all activity &rarr;</a>
          </div>
        </div>
      </div>
      ${langHtml}
      <a href="profile.html" class="user-avatar-btn" title="My Profile (${user.name})" data-i18n-title="nav.my_profile">
        ${initials}
      </a>
      <button class="btn btn-outline btn-sm" onclick="window.handleLogout(event)" style="font-size: 13px; padding: 6px 12px; margin-left: 2px;" data-i18n="nav.logout">
        ${window.i18n ? window.i18n.t("nav.logout") : "Logout"}
      </button>
      <button class="mobile-menu-btn" aria-label="Toggle navigation menu">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
    `;

    // Fetch initial unread badges
    window.refreshGlobalUnreadBadges();

    // Start periodic background polling for unread badges (every 20s)
    if (!window._globalUnreadPoller) {
      window._globalUnreadPoller = setInterval(() => {
        if (window.CURRENT_USER) {
          window.refreshGlobalUnreadBadges();
        }
      }, 20000);
    }

    // Ensure desktop nav menu has Messages link
    const navMenu = document.querySelector(".nav-menu");
    if (navMenu && !navMenu.querySelector('a[href*="messages"]')) {
      const collabItem = navMenu.querySelector('a[href*="collaborations"]')?.parentElement;
      const msgLi = document.createElement("li");
      msgLi.innerHTML = `<a href="messages.html" class="nav-link ${currentPath.includes("messages") ? 'active' : ''}" data-i18n="nav.messages">${window.i18n ? window.i18n.t("nav.messages") : "Messages"}</a>`;
      if (collabItem && collabItem.nextSibling) {
        navMenu.insertBefore(msgLi, collabItem.nextSibling);
      } else {
        navMenu.appendChild(msgLi);
      }
    }

    // Update Dashboard user avatar if present
    const dashAvatar = document.getElementById("dashboardUserAvatar");
    if (dashAvatar) {
      dashAvatar.innerHTML = `<span>${initials}</span>`;
    }

    const logoutLink = document.getElementById("sidebarLogoutBtn");
    if (logoutLink) {
      logoutLink.style.display = "flex";
    }

  } else {
    // Unauthenticated Navigation
    headerActions.innerHTML = `
      ${!isDirectoryPage ? `
        <a href="directory.html" class="header-icon-btn" title="Search Directory" data-i18n-title="nav.search_directory">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </a>
      ` : ''}
      ${langHtml}
      <a href="register.html?mode=login" class="btn btn-outline btn-sm" data-i18n="nav.login">${window.i18n ? window.i18n.t("nav.login") : "Login"}</a>
      <a href="register.html" class="btn btn-primary btn-sm" data-i18n="nav.signup">${window.i18n ? window.i18n.t("nav.signup") : "Sign Up"}</a>
      <button class="mobile-menu-btn" aria-label="Toggle navigation menu">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
    `;

    const dashAvatar = document.getElementById("dashboardUserAvatar");
    if (dashAvatar) {
      dashAvatar.innerHTML = `<span>?</span>`;
    }

    const logoutLink = document.getElementById("sidebarLogoutBtn");
    if (logoutLink) {
      logoutLink.style.display = "none";
    }
  }

  // Bind language selector and mobile menu after dynamic injection
  if (window.i18n) {
    window.i18n.bindLanguageSelectors();
    window.i18n.translatePage();
  }
  initMobileNav();
}

// Re-render navigation and active page dynamic elements when language changes
window.addEventListener("i18n:languageChanged", function () {
  updateGlobalNavigation(window.CURRENT_USER);
  if (typeof window.refreshDirectoryPage === "function") window.refreshDirectoryPage();
  if (typeof window.refreshDashboardFeed === "function") window.refreshDashboardFeed();
  if (typeof window.refreshProfilePage === "function") window.refreshProfilePage();
  if (typeof window.refreshCollaborationsPage === "function") window.refreshCollaborationsPage();
  if (typeof window.refreshMessagesPage === "function") window.refreshMessagesPage();
  if (typeof window.refreshNotificationsPage === "function") window.refreshNotificationsPage();
  if (typeof window.refreshLearnPage === "function") window.refreshLearnPage();
  if (typeof window.refreshGlobalUnreadBadges === "function") window.refreshGlobalUnreadBadges();
});

window.handleLogout = function (e) {
  if (e) e.preventDefault();
  if (window.UdyamAuth) {
    window.UdyamAuth.signOut().catch(() => {});
  }
  fetch("/api/logout", { method: "POST" })
    .then(r => r.json())
    .catch(() => ({ success: true }))
    .then(() => {
      window.CURRENT_USER = null;
      showToast("Logged out successfully.");
      setTimeout(() => {
        // If on private page like profile with no id, redirect to home
        const currentPath = window.location.pathname.toLowerCase();
        if (currentPath.includes("create-collaboration")) {
          window.location.href = "collaborations.html";
        } else {
          window.location.reload();
        }
      }, 500);
    });
};

// -----------------------------------------------------------------------------
// Notifications Modal (Collaboration Requests)
// -----------------------------------------------------------------------------
window.openNotificationsModal = function () {
  if (!window.CURRENT_USER) {
    showToast("Please log in to view partnership requests.");
    return;
  }

  fetch("/api/collaborations/requests")
    .then(r => r.json())
    .then(data => {
      const received = data.received || [];
      const pending = received.filter(r => r.status === "pending");

      let modal = document.getElementById("notifModal");
      if (!modal) {
        modal = document.createElement("div");
        modal.id = "notifModal";
        modal.className = "modal-backdrop";
        document.body.appendChild(modal);
      }

      let contentHtml = "";
      const tNoPending = window.i18n ? window.i18n.t("collab.no_requests", {}, "You have no pending partnership requests.") : "You have no pending partnership requests.";
      const tDecline = window.i18n ? window.i18n.t("collab.decline", {}, "Decline") : "Decline";
      const tAccept = window.i18n ? window.i18n.t("collab.accept", {}, "Accept Collaboration") : "Accept Collaboration";
      const tRegarding = window.i18n ? window.i18n.t("collab.regarding", {}, "Regarding") : "Regarding";
      const tRequestsTitle = window.i18n ? window.i18n.t("collab.received_requests_title", {}, "Partnership Requests") : "Partnership Requests";
      const tClose = window.i18n ? window.i18n.t("common.close", {}, "Close") : "Close";

      if (pending.length === 0) {
        contentHtml = `
          <div style="text-align: center; padding: 30px 10px;">
            <p style="color: var(--text-muted); font-size: 14.5px;">${escapeHtml(tNoPending)}</p>
          </div>
        `;
      } else {
        contentHtml = pending.map(req => {
          const cat = window.i18n && req.sender_category ? window.i18n.t("categories." + req.sender_category, {}, req.sender_category) : (req.sender_category || "");
          const loc = window.i18n ? window.i18n.localizeLocation(req.sender_location) : req.sender_location;
          return `
          <div class="card" style="padding: 14px; margin-bottom: 12px; border: 1px solid var(--border-color);">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
              <div class="avatar-circle" style="width: 36px; height: 36px;">
                <img src="${req.sender_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(req.sender_name)}">
              </div>
              <div>
                <div style="font-weight: 600; font-size: 14px;">${escapeHtml(req.sender_name)}</div>
                <div style="font-size: 12px; color: var(--text-muted);">${escapeHtml(cat)} • ${escapeHtml(loc)}</div>
              </div>
            </div>
            ${req.collab_title ? `<div style="font-size: 12px; font-weight: 600; color: var(--primary); margin-bottom: 6px;">${escapeHtml(tRegarding)}: ${escapeHtml(req.collab_title)}</div>` : ''}
            <p style="font-size: 13.5px; line-height: 1.5; color: var(--text-main); margin-bottom: 12px; background: #f8fafc; padding: 10px; border-radius: 6px;">
              “${escapeHtml(req.message)}”
            </p>
            <div style="display: flex; justify-content: flex-end; gap: 8px;">
              <button class="btn btn-outline btn-sm" onclick="window.respondToRequest(${req.id}, 'reject')">${escapeHtml(tDecline)}</button>
              <button class="btn btn-primary btn-sm" onclick="window.respondToRequest(${req.id}, 'accept')">${escapeHtml(tAccept)}</button>
            </div>
          </div>
        `;
        }).join("");
      }

      modal.innerHTML = `
        <div class="modal-dialog">
          <div class="modal-header">
            <h3 class="modal-title">${escapeHtml(tRequestsTitle)} (${pending.length})</h3>
            <button class="modal-close-btn" onclick="document.getElementById('notifModal').classList.remove('active')">&times;</button>
          </div>
          <div class="modal-body">
            ${contentHtml}
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary btn-sm" onclick="document.getElementById('notifModal').classList.remove('active')">${escapeHtml(tClose)}</button>
          </div>
        </div>
      `;

      modal.classList.add("active");
    });
};

window.respondToRequest = function (reqId, action) {
  fetch(`/api/collaborations/requests/${reqId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: action })
  })
  .then(r => r.json())
  .then(res => {
    if (res.success) {
      showToast(action === "accept" ? "Collaboration accepted! Added to your joint projects." : "Collaboration request declined.");
      const modal = document.getElementById("notifModal");
      if (modal) modal.classList.remove("active");
      initAuthSession();
    } else {
      showToast(res.error || "Failed to respond to request.");
    }
  })
  .catch(() => showToast("Network error. Please try again."));
};

// -----------------------------------------------------------------------------
// In-App Notification System & Dropdown
// -----------------------------------------------------------------------------
window.CURRENT_NOTIF_TAB = "all";

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return window.i18n ? window.i18n.t("common.just_now", {}, "Just now") : "Just now";
  let parsed = new Date(dateStr.endsWith("Z") ? dateStr : dateStr.replace(" ", "T") + "Z");
  if (isNaN(parsed.getTime())) {
    parsed = new Date(dateStr);
  }
  if (isNaN(parsed.getTime())) return window.i18n ? window.i18n.t("common.recently", {}, "Recently") : "Recently";

  const now = new Date();
  const diffSec = Math.floor((now.getTime() - parsed.getTime()) / 1000);
  if (diffSec < 60) return window.i18n ? window.i18n.t("common.just_now", {}, "Just now") : "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return window.i18n ? window.i18n.t("common.minutes_ago", { count: diffMin }, `${diffMin}m ago`) : `${diffMin}m ago`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return window.i18n ? window.i18n.t("common.hours_ago", { count: diffHour }, `${diffHour}h ago`) : `${diffHour}h ago`;
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay === 1) return window.i18n ? window.i18n.t("common.yesterday", {}, "Yesterday") : "Yesterday";
  if (diffDay < 7) return window.i18n ? window.i18n.t("common.days_ago", { count: diffDay }, `${diffDay}d ago`) : `${diffDay}d ago`;
  return parsed.toLocaleDateString(window.i18n ? window.i18n.currentLanguage : undefined, { month: "short", day: "numeric" });
}

function getEventBadgeIcon(eventType) {
  switch (eventType) {
    case "new_message":
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>`;
    case "collab_request_received":
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`;
    case "collab_request_accepted":
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    case "collab_request_rejected":
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    case "new_comment":
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;
    case "new_connection":
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>`;
    default:
      return `<svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle></svg>`;
  }
}

function renderNotificationItem(n) {
  const avatar = n.actor_avatar || "assets/images/digital_rahul.jpg";
  const actorName = n.actor_name || (window.i18n ? window.i18n.t("notif.community_member", "Community Member") : "Community Member");
  const timeAgo = formatTimeAgo(n.created_at);
  const isUnread = !n.is_read;
  const badgeIcon = getEventBadgeIcon(n.event_type);
  const linkUrl = n.link_url || "#";
  const markReadTitle = window.i18n ? window.i18n.t("notif.mark_read", "Mark as read") : "Mark as read";

  return `
    <div class="notif-item ${isUnread ? 'unread' : ''}" id="notif-item-${n.id}" onclick="window.clickNotification(${n.id}, '${escapeHtml(linkUrl)}', event)">
      <div class="notif-item-avatar-wrap">
        <img class="notif-avatar" src="${avatar}" alt="${escapeHtml(actorName)}" onerror="this.src='assets/images/digital_rahul.jpg'">
        <div class="notif-type-icon-badge">${badgeIcon}</div>
      </div>
      <div class="notif-content">
        <div class="notif-title-row">
          <span class="notif-title" title="${escapeHtml(n.title || actorName)}">${escapeHtml(n.title || actorName)}</span>
          <span class="notif-time">${timeAgo}</span>
        </div>
        <p class="notif-message">${escapeHtml(n.message)}</p>
      </div>
      <div class="notif-item-actions">
        ${isUnread ? `
          <button type="button" class="notif-quick-read-btn" title="${markReadTitle}" onclick="window.markSingleNotificationRead(${n.id}, event)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </button>
          <div class="notif-unread-dot"></div>
        ` : ''}
      </div>
    </div>
  `;
}

window.refreshGlobalUnreadBadges = function () {
  if (!window.CURRENT_USER) return;

  // 1. In-App Notifications count
  fetch("/api/notifications/unread-count")
    .then(r => r.json())
    .then(data => {
      if (data && data.success) {
        const count = data.unread_count || 0;
        const badge = document.getElementById("globalNotifBadge");
        if (badge) {
          if (count > 0) {
            badge.style.display = "flex";
            badge.textContent = count > 99 ? "99+" : count;
          } else {
            badge.style.display = "none";
            badge.textContent = "";
          }
        }
        const pill = document.getElementById("notifDropdownUnreadCount");
        if (pill) {
          if (count > 0) {
            pill.style.display = "inline-block";
            const unreadTxt = window.i18n ? window.i18n.t("notif.unread", "unread") : "unread";
            pill.textContent = `${count} ${unreadTxt}`;
          } else {
            pill.style.display = "none";
          }
        }
      }
    })
    .catch(() => {});

  // 2. Messages unread count
  fetch("/api/conversations/unread-count")
    .then(r => r.json())
    .then(data => {
      if (data && data.success) {
        const count = data.unread_count || 0;
        const msgBadge = document.getElementById("globalMsgBadge");
        if (msgBadge) {
          if (count > 0) {
            msgBadge.style.display = "flex";
            msgBadge.textContent = count > 99 ? "99+" : count;
          } else {
            msgBadge.style.display = "none";
            msgBadge.textContent = "";
          }
        }
        const sideMsgBadge = document.getElementById("sidebarMsgBadge");
        if (sideMsgBadge) {
          if (count > 0) {
            sideMsgBadge.style.display = "inline-block";
            sideMsgBadge.textContent = count;
          } else {
            sideMsgBadge.style.display = "none";
          }
        }
      }
    })
    .catch(() => {});
};

window.toggleNotificationsDropdown = function (event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  const dropdown = document.getElementById("notifDropdown");
  if (!dropdown) return;

  const isVisible = dropdown.style.display === "flex" || dropdown.style.display === "block";
  if (isVisible) {
    dropdown.style.display = "none";
  } else {
    dropdown.style.display = "flex";
    window.loadNotificationsDropdown();
  }
};

// Close dropdown on outside click
document.addEventListener("click", function (e) {
  const dropdown = document.getElementById("notifDropdown");
  const bellBtn = document.getElementById("notifBellBtn");
  if (!dropdown) return;
  if (!dropdown.contains(e.target) && !bellBtn?.contains(e.target)) {
    dropdown.style.display = "none";
  }
});

// Close dropdown on Escape
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    const dropdown = document.getElementById("notifDropdown");
    if (dropdown) dropdown.style.display = "none";
  }
});

window.switchNotifTab = function (tabName) {
  window.CURRENT_NOTIF_TAB = tabName;
  document.querySelectorAll(".notif-tab").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabName);
  });
  window.loadNotificationsDropdown();
};

window.loadNotificationsDropdown = function () {
  const listEl = document.getElementById("notifDropdownList");
  if (!listEl) return;

  const loadingTxt = window.i18n ? window.i18n.t("notif.loading", "Loading notifications...") : "Loading notifications...";
  const errorTxt = window.i18n ? window.i18n.t("notif.error_load", "Failed to load notifications.") : "Failed to load notifications.";
  const retryTxt = window.i18n ? window.i18n.t("notif.retry", "Retry") : "Retry";

  listEl.innerHTML = `
    <div class="notif-loading-state">
      <div class="spinner"></div>
      <span style="font-size: 13px; color: var(--text-muted); margin-top: 6px;">${loadingTxt}</span>
    </div>
  `;

  const unreadOnly = window.CURRENT_NOTIF_TAB === "unread" ? "?unread=1&limit=20" : "?limit=20";
  fetch(`/api/notifications${unreadOnly}`)
    .then(r => r.json())
    .then(data => {
      if (!data || !data.success) {
        listEl.innerHTML = `
          <div class="notif-error-state">
            <p style="color: var(--text-muted); font-size: 13px; margin: 0;">${errorTxt}</p>
            <button class="btn btn-outline btn-sm" onclick="window.loadNotificationsDropdown()" style="font-size: 12px; margin-top: 8px;">${retryTxt}</button>
          </div>
        `;
        return;
      }

      const notifs = data.notifications || [];
      if (notifs.length === 0) {
        const msg = window.CURRENT_NOTIF_TAB === "unread"
          ? (window.i18n ? window.i18n.t("notif.no_notifications", "No unread notifications.") : "No unread notifications.")
          : (window.i18n ? window.i18n.t("notif.empty_desc", "You have no notifications yet.") : "You have no notifications yet.");
        const caughtUpTitle = window.i18n ? window.i18n.t("notif.all_caught_up", "All caught up!") : "All caught up!";
        listEl.innerHTML = `
          <div class="notif-empty-state">
            <div class="notif-empty-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <p class="notif-empty-title">${caughtUpTitle}</p>
            <p class="notif-empty-subtitle">${msg}</p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = notifs.map(n => renderNotificationItem(n)).join("");
    })
    .catch(() => {
      listEl.innerHTML = `
        <div class="notif-error-state">
          <p style="color: var(--text-muted); font-size: 13px; margin: 0;">${errorTxt}</p>
          <button class="btn btn-outline btn-sm" onclick="window.loadNotificationsDropdown()" style="font-size: 12px; margin-top: 8px;">${retryTxt}</button>
        </div>
      `;
    });
};

window.clickNotification = function (notifId, linkUrl, event) {
  if (event) event.stopPropagation();

  // Optimistic UI update
  const item = document.getElementById(`notif-item-${notifId}`);
  if (item) {
    item.classList.remove("unread");
    const dot = item.querySelector(".notif-unread-dot");
    if (dot) dot.remove();
    const btn = item.querySelector(".notif-quick-read-btn");
    if (btn) btn.remove();
  }

  fetch(`/api/notifications/${notifId}/read`, { method: "POST" })
    .then(r => r.json())
    .catch(() => {})
    .then(() => {
      window.refreshGlobalUnreadBadges();
      if (linkUrl && linkUrl !== "#") {
        window.location.href = linkUrl;
      }
    });
};

window.markSingleNotificationRead = function (notifId, event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }

  const item = document.getElementById(`notif-item-${notifId}`);
  if (item) {
    item.classList.remove("unread");
    const dot = item.querySelector(".notif-unread-dot");
    if (dot) dot.remove();
    const btn = item.querySelector(".notif-quick-read-btn");
    if (btn) btn.remove();
  }

  fetch(`/api/notifications/${notifId}/read`, { method: "POST" })
    .then(r => r.json())
    .then(() => {
      window.refreshGlobalUnreadBadges();
      if (window.CURRENT_NOTIF_TAB === "unread") {
        window.loadNotificationsDropdown();
      }
    })
    .catch(() => {});
};

window.markAllNotificationsRead = function (event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }

  fetch("/api/notifications/read-all", { method: "POST" })
    .then(r => r.json())
    .then(res => {
      if (res && res.success) {
        showToast("All notifications marked as read.");
        window.refreshGlobalUnreadBadges();
        // Update any open dropdown or page
        const dropdown = document.getElementById("notifDropdown");
        if (dropdown && dropdown.style.display !== "none") {
          window.loadNotificationsDropdown();
        }
        if (typeof window.loadNotificationsPage === "function") {
          window.loadNotificationsPage(false);
        }
      }
    })
    .catch(() => {
      showToast("Failed to mark notifications as read.");
    });
};

// -----------------------------------------------------------------------------
// Dedicated Notifications Page Logic (notifications.html)
// -----------------------------------------------------------------------------
window.PAGE_NOTIF_FILTER = "all";
window.PAGE_NOTIF_OFFSET = 0;
const PAGE_NOTIF_LIMIT = 20;

window.initNotificationsPage = function () {
  const pageList = document.getElementById("notificationsPageList");
  if (!pageList) return;

  window.PAGE_NOTIF_OFFSET = 0;
  window.loadNotificationsPage(false);
};

window.filterNotificationsPage = function (filterName) {
  window.PAGE_NOTIF_FILTER = filterName;
  window.PAGE_NOTIF_OFFSET = 0;

  document.querySelectorAll(".notif-page-filter-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-filter") === filterName);
  });

  window.loadNotificationsPage(false);
};

window.loadNotificationsPage = function (append = false) {
  const pageList = document.getElementById("notificationsPageList");
  if (!pageList) return;

  const loadMoreContainer = document.getElementById("notifPageLoadMoreContainer");
  const loadMoreBtn = document.getElementById("notifPageLoadMoreBtn");

  const loadingTxt = window.i18n ? window.i18n.t("notif.loading", "Loading notifications...") : "Loading notifications...";
  const errorTxt = window.i18n ? window.i18n.t("notif.error_load", "Failed to load notifications.") : "Failed to load notifications.";
  const retryTxt = window.i18n ? window.i18n.t("notif.retry", "Try Again") : "Try Again";

  if (!append) {
    pageList.innerHTML = `
      <div class="notif-loading-state" id="notifPageLoading">
        <div class="spinner"></div>
        <span style="font-size: 13.5px; color: var(--text-muted); margin-top: 8px;">${loadingTxt}</span>
      </div>
    `;
    if (loadMoreContainer) loadMoreContainer.style.display = "none";
  } else if (loadMoreBtn) {
    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = loadingTxt;
  }

  let query = `?limit=${PAGE_NOTIF_LIMIT}&offset=${window.PAGE_NOTIF_OFFSET}`;
  if (window.PAGE_NOTIF_FILTER === "unread") {
    query += "&unread=1";
  } else if (window.PAGE_NOTIF_FILTER === "messages") {
    query += "&type=new_message";
  }

  fetch(`/api/notifications${query}`)
    .then(r => r.json())
    .then(data => {
      if (!data || !data.success) {
        if (!append) {
          pageList.innerHTML = `
            <div class="notif-error-state">
              <p style="color: var(--text-muted); font-size: 14px;">${errorTxt}</p>
              <button class="btn btn-outline btn-sm" onclick="window.loadNotificationsPage(false)">${retryTxt}</button>
            </div>
          `;
        }
        return;
      }

      let notifs = data.notifications || [];
      if (window.PAGE_NOTIF_FILTER === "collaborations") {
        notifs = notifs.filter(n => n.event_type.startsWith("collab_"));
      }

      if (notifs.length === 0 && !append) {
        const noNotifsTitle = window.i18n ? window.i18n.t("notif.no_notifications", "No notifications found") : "No notifications found";
        const emptyDesc = window.i18n ? window.i18n.t("notif.empty_desc", "You have no matching activity or notifications at this time.") : "You have no matching activity or notifications at this time.";
        pageList.innerHTML = `
          <div class="notif-empty-state">
            <div class="notif-empty-icon" style="width: 48px; height: 48px;">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <p class="notif-empty-title">${noNotifsTitle}</p>
            <p class="notif-empty-subtitle">${emptyDesc}</p>
          </div>
        `;
        if (loadMoreContainer) loadMoreContainer.style.display = "none";
        return;
      }

      const html = notifs.map(n => renderNotificationItem(n)).join("");
      if (append) {
        const loading = document.getElementById("notifPageLoading");
        if (loading) loading.remove();
        pageList.insertAdjacentHTML("beforeend", html);
      } else {
        pageList.innerHTML = html;
      }

      // Check load more
      if (loadMoreContainer && loadMoreBtn) {
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = window.i18n ? window.i18n.t("notif.load_more", "Load More Notifications") : "Load More Notifications";
        if (data.total_count > window.PAGE_NOTIF_OFFSET + notifs.length) {
          loadMoreContainer.style.display = "block";
        } else {
          loadMoreContainer.style.display = "none";
        }
      }
    })
    .catch(() => {
      if (!append) {
        pageList.innerHTML = `
          <div class="notif-error-state">
            <p style="color: var(--text-muted); font-size: 14px;">${errorTxt}</p>
            <button class="btn btn-outline btn-sm" onclick="window.loadNotificationsPage(false)">${retryTxt}</button>
          </div>
        `;
      }
    });
};

window.loadMorePageNotifications = function () {
  window.PAGE_NOTIF_OFFSET += PAGE_NOTIF_LIMIT;
  window.loadNotificationsPage(true);
};

window.refreshNotificationsPage = function () {
  if (typeof window.loadNotificationsPage === "function" && document.getElementById("notificationsPageList")) {
    window.loadNotificationsPage(false);
  }
};

// -----------------------------------------------------------------------------
// Global Modals & Connect Button Listener
// -----------------------------------------------------------------------------
function initGlobalModals() {
  document.querySelectorAll("[data-close-modal]").forEach(btn => {
    btn.addEventListener("click", function () {
      const modal = btn.closest(".modal-backdrop");
      if (modal) modal.classList.remove("active");
    });
  });

  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-connect");
    if (btn) {
      e.preventDefault();
      if (!window.CURRENT_USER) {
        showToast("Please log in to connect with rural entrepreneurs.");
        setTimeout(() => {
          window.location.href = "register.html?mode=login";
        }, 1200);
        return;
      }

      const targetId = btn.getAttribute("data-user-id");
      if (!targetId || targetId === window.CURRENT_USER.user_id) {
        showToast("You cannot connect with your own profile.");
        return;
      }

      fetch("/api/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_id: targetId })
      })
      .then(r => r.json())
      .then(res => {
        if (res.status === "connected") {
          btn.classList.add("connected");
          btn.textContent = "Connected ✓";
          btn.classList.remove("btn-primary");
          btn.classList.add("btn-outline");
          showToast("Connected! Saved to SQLite database.");
        } else {
          btn.classList.remove("connected");
          btn.textContent = "Connect";
          btn.classList.remove("btn-outline");
          btn.classList.add("btn-primary");
          showToast("Connection removed.");
        }
      })
      .catch(() => showToast("Connection updated."));
    }
  });
}

// -----------------------------------------------------------------------------
// Directory Page: Search & SQLite Filtering (Screen 4)
// -----------------------------------------------------------------------------
function initDirectoryPage() {
  const directoryContainer = document.getElementById("directoryList");
  const searchInput = document.getElementById("dirSearchInput");
  const industrySelect = document.getElementById("filterIndustry");
  const locationSelect = document.getElementById("filterLocation");
  const filterBtn = document.getElementById("applyFiltersBtn");

  if (!directoryContainer) return;

  let cachedStates = [];

  function renderDirectory(items) {
    if (!items || items.length === 0) {
      const emptyMsg = window.i18n ? window.i18n.t("directory.no_results", {}, "No entrepreneurs match your search criteria.") : "No entrepreneurs match your search criteria.";
      const resetText = window.i18n ? window.i18n.t("directory.reset_filters", {}, "Reset Filters") : "Reset Filters";
      directoryContainer.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <p style="color: var(--text-muted); font-size: 15px;">${escapeHtml(emptyMsg)}</p>
          <button class="btn btn-secondary btn-sm" style="margin-top: 12px;" onclick="window.resetDirectoryFilters()">${escapeHtml(resetText)}</button>
        </div>
      `;
      return;
    }

    const tVerified = window.i18n ? window.i18n.t("profile.verified_badge", {}, "Verified") : "Verified";
    const tViewProfile = window.i18n ? window.i18n.t("directory.view_profile", {}, "View Profile") : "View Profile";
    const tConnect = window.i18n ? window.i18n.t("directory.connect", {}, "Connect") : "Connect";
    const tConnected = window.i18n ? window.i18n.t("directory.connected", {}, "Connected ✓") : "Connected ✓";

    directoryContainer.innerHTML = items.map(ent => {
      const catDisplay = window.i18n ? window.i18n.t("categories." + ent.category, {}, ent.category) : ent.category;
      const locDisplay = window.i18n ? window.i18n.localizeLocation(ent.location, ent.state) : ent.location;
      const isConn = ent.is_connected || false;

      return `
        <div class="directory-card">
          <div class="directory-card-left">
            <div class="directory-avatar">
              <img src="${ent.avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(ent.name)}">
            </div>
            <div class="directory-card-info">
              <div class="directory-card-name-row">
                <span class="directory-card-name">${escapeHtml(ent.name)}</span>
                ${ent.verified ? `
                  <span class="badge badge-verified">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    ${escapeHtml(tVerified)}
                  </span>
                ` : ''}
              </div>
              <div class="directory-card-sub">${escapeHtml(catDisplay)} • ${escapeHtml(locDisplay)}</div>
              <p class="directory-card-desc">${escapeHtml(ent.description || ent.quote || '')}</p>
            </div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <a href="profile.html?id=${encodeURIComponent(ent.user_id)}" class="btn btn-outline btn-sm">${escapeHtml(tViewProfile)}</a>
            ${window.CURRENT_USER && window.CURRENT_USER.user_id !== ent.user_id ? `
              <button class="btn ${isConn ? 'btn-outline connected' : 'btn-outline'} btn-sm btn-connect" data-user-id="${escapeHtml(ent.user_id)}">
                ${escapeHtml(isConn ? tConnected : tConnect)}
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join("");
  }

  function populateLocationSelect() {
    if (!locationSelect) return;
    const currentVal = locationSelect.value || "All";
    const allLocationsLabel = window.i18n ? window.i18n.t("directory.all_locations", {}, "All Locations / States") : "All Locations / States";
    locationSelect.innerHTML = `<option value="All" data-i18n="directory.all_locations">${escapeHtml(allLocationsLabel)}</option>`;

    cachedStates.forEach(st => {
      const opt = document.createElement("option");
      opt.value = st;
      opt.setAttribute("data-i18n", "states." + st);
      opt.textContent = window.i18n ? window.i18n.t("states." + st, {}, st) : st;
      if (st === currentVal) opt.selected = true;
      locationSelect.appendChild(opt);
    });
  }

  function updateIndustrySelectLabels() {
    if (!industrySelect) return;
    Array.from(industrySelect.options).forEach(opt => {
      const key = opt.getAttribute("data-i18n");
      if (key && window.i18n) {
        opt.textContent = window.i18n.t(key, {}, opt.textContent);
      }
    });
  }

  // Populate location dropdown dynamically with Indian states
  if (locationSelect) {
    fetch("/api/locations/states")
      .then(r => r.json())
      .then(data => {
        if (data && data.states && data.states.length > 0) {
          cachedStates = data.states;
          populateLocationSelect();
        }
      })
      .catch(() => {});
  }

  function fetchAndFilter() {
    const query = (searchInput ? searchInput.value : "").trim();
    const ind = industrySelect ? industrySelect.value : "All";
    const loc = locationSelect ? locationSelect.value : "All";

    const params = new URLSearchParams({ q: query, industry: ind, location: loc, state: loc });

    fetch(`/api/entrepreneurs?${params.toString()}`)
      .then(res => {
        if (!res.ok) throw new Error("API unavailable");
        return res.json();
      })
      .then(data => renderDirectory(data))
      .catch(async () => {
        if (window.UdyamAPI && window.supabaseClient) {
          try {
            const supaData = await window.UdyamAPI.getEntrepreneurs({
              search: query,
              category: ind === "All" ? "" : ind,
              state: loc === "All" ? "" : loc
            });
            if (supaData && supaData.length > 0) {
              renderDirectory(supaData);
              return;
            }
          } catch (e) {
            console.warn("Supabase directory fallback error:", e);
          }
        }
        if (window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.entrepreneurs)) {
          let list = window.UDYAM_DATA.entrepreneurs;
          if (query) {
            const q = query.toLowerCase();
            list = list.filter(e =>
              (e.name && e.name.toLowerCase().includes(q)) ||
              (e.description && e.description.toLowerCase().includes(q)) ||
              (e.category && e.category.toLowerCase().includes(q))
            );
          }
          if (ind !== "All") list = list.filter(e => e.category === ind);
          if (loc !== "All") list = list.filter(e => e.location && e.location.includes(loc));
          renderDirectory(list);
          return;
        }
        renderDirectory([]);
      });
  }

  if (searchInput) searchInput.addEventListener("input", fetchAndFilter);
  if (filterBtn) filterBtn.addEventListener("click", fetchAndFilter);
  if (industrySelect) industrySelect.addEventListener("change", fetchAndFilter);
  if (locationSelect) locationSelect.addEventListener("change", fetchAndFilter);

  window.resetDirectoryFilters = function () {
    if (searchInput) searchInput.value = "";
    if (industrySelect) industrySelect.value = "All";
    if (locationSelect) locationSelect.value = "All";
    fetchAndFilter();
  };

  window.refreshDirectoryPage = function () {
    populateLocationSelect();
    updateIndustrySelectLabels();
    fetchAndFilter();
  };

  fetchAndFilter();
}

// -----------------------------------------------------------------------------
// Dashboard Feed & SQLite Posts (Screen 3)
// -----------------------------------------------------------------------------
function initDashboardFeed() {
  const sharePostBtn = document.getElementById("sharePostBtn");
  const shareInput = document.getElementById("shareInput");
  const postsFeed = document.getElementById("postsFeed");
  const feedTabs = document.querySelectorAll(".feed-tab-btn");
  const suggestedList = document.getElementById("suggestedList");

  if (!postsFeed) return;

  function loadFeed(filter = "all") {
    fetch(`/api/feed?type=${filter}`)
      .then(res => res.json())
      .then(posts => {
        if (!posts || posts.length === 0) {
          const noPostsText = window.i18n ? window.i18n.t("dashboard.no_posts", {}, "No posts available yet. Be the first to share an update!") : "No posts available yet. Be the first to share an update!";
          postsFeed.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
              <p style="color: var(--text-muted); font-size: 14.5px;">${escapeHtml(noPostsText)}</p>
            </div>
          `;
          return;
        }

        const tConnect = window.i18n ? window.i18n.t("directory.connect", {}, "Connect") : "Connect";
        const tLike = window.i18n ? window.i18n.t("dashboard.like", {}, "Likes") : "Likes";
        const tComments = window.i18n ? window.i18n.t("dashboard.comments", {}, "Comments") : "Comments";

        postsFeed.innerHTML = posts.map(p => {
          const catDisplay = window.i18n ? window.i18n.t("categories." + p.author_category, {}, p.author_category) : p.author_category;
          const locDisplay = window.i18n ? window.i18n.localizeLocation(p.author_location) : p.author_location;
          const timeDisplay = formatTimeAgo(p.created_at);
          const tagDisplay = p.post_type === 'opportunity'
            ? (window.i18n ? window.i18n.t('collab.opportunity_type', {}, 'Collaboration Opportunity') : 'Collaboration Opportunity')
            : (p.post_type === 'question' ? (window.i18n ? window.i18n.t('disc.ask_question', {}, 'Question') : 'Question') : (window.i18n ? window.i18n.t('profile.our_story', {}, 'Success Story') : 'Success Story'));

          return `
          <div class="post-card" data-post-type="${escapeHtml(p.post_type)}">
            <div class="post-header">
              <div class="post-user">
                <div class="avatar-circle">
                  <img src="${p.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(p.author_name)}">
                </div>
                <div class="post-user-info">
                  <span class="post-author-name">${escapeHtml(p.author_name)}</span>
                  <div class="post-meta">
                    <span>${escapeHtml(catDisplay)}</span> • <span>${escapeHtml(locDisplay)}</span> • <span>${escapeHtml(timeDisplay)}</span>
                  </div>
                </div>
              </div>
              <button class="header-icon-btn" title="Options" onclick="showToast('Post bookmarked.')">•••</button>
            </div>
            <p class="post-content">${escapeHtml(p.content)}</p>
            <div class="ugc-post-translate" data-post-id="${p.id}"></div>
            <div class="post-tags">
              <span class="badge ${p.post_type === 'opportunity' ? 'badge-category' : 'badge-tag'}">${escapeHtml(tagDisplay)}</span>
              ${p.tag ? `<span class="badge badge-tag">${escapeHtml(p.tag)}</span>` : ''}
            </div>
            <div class="post-actions-bar">
              <div class="post-stats">
                <button class="stat-item btn-like ${p.has_liked ? 'active' : ''}" onclick="window.toggleLike(this, ${p.likes || 0}, ${p.id})" data-count="${p.likes || 0}" style="${p.has_liked ? 'color: var(--primary);' : ''}">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="${p.has_liked ? 'var(--primary)' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
                  <span>${p.likes || 0} ${escapeHtml(tLike)}</span>
                </button>
                <a href="${p.post_type === 'opportunity' ? 'collaborations.html' : 'discussion.html'}" class="stat-item">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                  <span>${p.comments_count || 0} ${escapeHtml(tComments)}</span>
                </a>
              </div>
              ${window.CURRENT_USER && window.CURRENT_USER.user_id !== p.author_id ? `
                <button class="btn btn-outline btn-sm btn-connect" data-user-id="${escapeHtml(p.author_id)}">${escapeHtml(tConnect)}</button>
              ` : ''}
            </div>
          </div>
        `;
        }).join("");

        // Wire up UGC translation toggles for community posts
        posts.forEach(p => {
          const container = postsFeed.querySelector(`.ugc-post-translate[data-post-id="${p.id}"]`);
          if (container && window.i18n) {
            window.i18n.setupUGCTranslateToggle(container, p.content, "auto");
          }
        });
      })
      .catch(async () => {
        let fallbackPosts = [];
        if (window.UdyamAPI && window.supabaseClient) {
          try {
            const spPosts = await window.UdyamAPI.getFeedPosts();
            if (spPosts && spPosts.length > 0) {
              fallbackPosts = filter === "all" ? spPosts : spPosts.filter(p => p.post_type === filter);
            }
          } catch (_) {}
        }
        if (fallbackPosts.length === 0 && window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.feedPosts)) {
          fallbackPosts = window.UDYAM_DATA.feedPosts.map(p => ({
            id: p.id,
            author_id: p.authorId || "asha-devi",
            author_name: p.author || "Asha Devi",
            author_category: p.category || "Handicrafts",
            author_location: p.location || "Uttar Pradesh",
            author_avatar: p.avatar || "assets/images/artisan_asha.jpg",
            content: p.content,
            post_type: p.type || "story",
            tag: p.tag || "",
            likes: p.likes || 0,
            comments_count: p.commentsCount || 0,
            created_at: p.time || new Date().toISOString()
          }));
          if (filter !== "all") fallbackPosts = fallbackPosts.filter(p => p.post_type === filter);
        }
        if (fallbackPosts.length > 0) {
          renderFeedPosts(fallbackPosts);
        }
      });
  }

  function renderFeedPosts(posts) {
    const tConnect = window.i18n ? window.i18n.t("directory.connect", {}, "Connect") : "Connect";
    const tLike = window.i18n ? window.i18n.t("dashboard.like", {}, "Likes") : "Likes";
    const tComments = window.i18n ? window.i18n.t("dashboard.comments", {}, "Comments") : "Comments";

    postsFeed.innerHTML = posts.map(p => {
      const catDisplay = window.i18n ? window.i18n.t("categories." + p.author_category, {}, p.author_category) : p.author_category;
      const locDisplay = window.i18n ? window.i18n.localizeLocation(p.author_location) : p.author_location;
      const timeDisplay = formatTimeAgo(p.created_at);
      const tagDisplay = p.post_type === 'opportunity'
        ? (window.i18n ? window.i18n.t('collab.opportunity_type', {}, 'Collaboration Opportunity') : 'Collaboration Opportunity')
        : (p.post_type === 'question' ? (window.i18n ? window.i18n.t('disc.ask_question', {}, 'Question') : 'Question') : (window.i18n ? window.i18n.t('profile.our_story', {}, 'Success Story') : 'Success Story'));

      return `
      <div class="post-card" data-post-type="${escapeHtml(p.post_type)}">
        <div class="post-header">
          <div class="post-user">
            <div class="avatar-circle">
              <img src="${p.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(p.author_name)}">
            </div>
            <div class="post-user-info">
              <span class="post-author-name">${escapeHtml(p.author_name)}</span>
              <div class="post-meta">
                <span>${escapeHtml(catDisplay)}</span> • <span>${escapeHtml(locDisplay)}</span> • <span>${escapeHtml(timeDisplay)}</span>
              </div>
            </div>
          </div>
          <button class="header-icon-btn" title="Options" onclick="showToast('Post bookmarked.')">•••</button>
        </div>
        <p class="post-content">${escapeHtml(p.content)}</p>
        <div class="ugc-post-translate" data-post-id="${p.id}"></div>
        <div class="post-tags">
          <span class="badge ${p.post_type === 'opportunity' ? 'badge-category' : 'badge-tag'}">${escapeHtml(tagDisplay)}</span>
          ${p.tag ? `<span class="badge badge-tag">${escapeHtml(p.tag)}</span>` : ''}
        </div>
        <div class="post-actions-bar">
          <div class="post-stats">
            <button class="stat-item btn-like ${p.has_liked ? 'active' : ''}" onclick="window.toggleLike(this, ${p.likes || 0}, ${p.id})" data-count="${p.likes || 0}" style="${p.has_liked ? 'color: var(--primary);' : ''}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="${p.has_liked ? 'var(--primary)' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
              <span>${p.likes || 0} ${escapeHtml(tLike)}</span>
            </button>
            <a href="${p.post_type === 'opportunity' ? 'collaborations.html' : 'discussion.html'}" class="stat-item">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
              <span>${p.comments_count || 0} ${escapeHtml(tComments)}</span>
            </a>
          </div>
          ${window.CURRENT_USER && window.CURRENT_USER.user_id !== p.author_id ? `
            <button class="btn btn-outline btn-sm btn-connect" data-user-id="${escapeHtml(p.author_id)}">${escapeHtml(tConnect)}</button>
          ` : ''}
        </div>
      </div>
    `;
    }).join("");
  }

  function loadSuggestedEntrepreneurs() {
    if (!suggestedList) return;
    const tConnect = window.i18n ? window.i18n.t("directory.connect", {}, "Connect") : "Connect";
    fetch("/api/entrepreneurs")
      .then(r => {
        if (!r.ok) throw new Error("API unavailable");
        return r.json();
      })
      .then(users => {
        const myUid = window.CURRENT_USER ? window.CURRENT_USER.user_id : null;
        const filtered = users.filter(u => u.user_id !== myUid).slice(0, 3);
        suggestedList.innerHTML = filtered.map(u => {
          const uCat = window.i18n ? window.i18n.t("categories." + u.category, {}, u.category) : u.category;
          const uLoc = window.i18n ? window.i18n.localizeLocation(u.location, u.state) : u.location;
          return `
          <div class="suggested-item">
            <div class="suggested-profile">
              <div class="avatar-circle">
                <img src="${u.avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(u.name)}">
              </div>
              <div class="suggested-meta">
                <a href="profile.html?id=${u.user_id}" class="suggested-name" style="color: inherit;">${escapeHtml(u.name)}</a>
                <span class="suggested-category">${escapeHtml(uCat)} • ${escapeHtml(uLoc)}</span>
              </div>
            </div>
            <button class="btn btn-outline btn-sm btn-connect" data-user-id="${u.user_id}">${escapeHtml(tConnect)}</button>
          </div>
        `;
        }).join("");
      })
      .catch(async () => {
        let fallbackUsers = [];
        if (window.UdyamAPI && window.supabaseClient) {
          try {
            fallbackUsers = await window.UdyamAPI.getEntrepreneurs();
          } catch (_) {}
        }
        if (fallbackUsers.length === 0 && window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.entrepreneurs)) {
          fallbackUsers = window.UDYAM_DATA.entrepreneurs.map(e => ({
            user_id: e.id,
            name: e.name,
            category: e.category,
            location: e.location,
            avatar: e.avatar
          }));
        }
        const myUid = window.CURRENT_USER ? window.CURRENT_USER.user_id : null;
        const filtered = fallbackUsers.filter(u => u.user_id !== myUid).slice(0, 3);
        suggestedList.innerHTML = filtered.map(u => {
          const uCat = window.i18n ? window.i18n.t("categories." + u.category, {}, u.category) : u.category;
          const uLoc = window.i18n ? window.i18n.localizeLocation(u.location, u.state) : u.location;
          return `
          <div class="suggested-item">
            <div class="suggested-profile">
              <div class="avatar-circle">
                <img src="${u.avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(u.name)}">
              </div>
              <div class="suggested-meta">
                <a href="profile.html?id=${u.user_id}" class="suggested-name" style="color: inherit;">${escapeHtml(u.name)}</a>
                <span class="suggested-category">${escapeHtml(uCat)} • ${escapeHtml(uLoc)}</span>
              </div>
            </div>
            <button class="btn btn-outline btn-sm btn-connect" data-user-id="${u.user_id}">${escapeHtml(tConnect)}</button>
          </div>
        `;
        }).join("");
      });
  }

  if (sharePostBtn && shareInput) {
    sharePostBtn.addEventListener("click", function () {
      if (!window.CURRENT_USER) {
        showToast("Please log in to share an update with the community.");
        setTimeout(() => {
          window.location.href = "register.html?mode=login";
        }, 1000);
        return;
      }

      const text = shareInput.value.trim();
      if (!text) {
        showToast("Please enter an update or question.");
        return;
      }

      fetch("/api/feed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text, post_type: "story", tag: "Community Update" })
      })
      .then(res => res.json())
      .then(res => {
        if (res.success) {
          shareInput.value = "";
          showToast("Your update was posted and saved to SQLite!");
          loadFeed();
        } else {
          showToast(res.error || "Failed to post.");
        }
      })
      .catch(() => showToast("Network error. Please try again."));
    });
  }

  feedTabs.forEach(tab => {
    tab.addEventListener("click", function () {
      feedTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const filter = tab.getAttribute("data-filter") || "all";
      loadFeed(filter);
    });
  });

  window.toggleLike = function (btn, initialCount, postId) {
    if (!window.CURRENT_USER) {
      showToast("Please log in to like posts.");
      return;
    }

    if (postId) {
      fetch(`/api/posts/${postId}/like`, { method: "POST" })
        .then(r => r.json())
        .then(res => {
          if (res.success) {
            const countSpan = btn.querySelector("span");
            const svg = btn.querySelector("svg");
            const tLike = window.i18n ? window.i18n.t("dashboard.like", {}, "Likes") : "Likes";
            countSpan.textContent = `${res.likes} ${tLike}`;
            if (res.liked) {
              btn.classList.add("active");
              btn.style.color = "var(--primary)";
              svg.setAttribute("fill", "var(--primary)");
            } else {
              btn.classList.remove("active");
              btn.style.color = "inherit";
              svg.setAttribute("fill", "none");
            }
          }
        })
        .catch(() => {});
    }
  };

  window.refreshDashboardFeed = function () {
    const activeTab = document.querySelector(".feed-tab-btn.active");
    const filter = activeTab ? (activeTab.getAttribute("data-filter") || "all") : "all";
    loadFeed(filter);
    loadSuggestedEntrepreneurs();
  };

  loadFeed("all");
  loadSuggestedEntrepreneurs();
}

// -----------------------------------------------------------------------------
// Profile Page Tabs & Dynamic Loading (Screen 5)
// -----------------------------------------------------------------------------
function initProfilePage() {
  const profileContainer = document.getElementById("profileMainContainer");
  if (!profileContainer) return;

  // Setup Tabs
  const profileTabs = document.querySelectorAll(".profile-tab-btn");
  const tabPanes = document.querySelectorAll(".profile-tab-pane");

  profileTabs.forEach(tab => {
    tab.addEventListener("click", function () {
      const targetId = tab.getAttribute("data-target");
      profileTabs.forEach(t => t.classList.remove("active"));
      tabPanes.forEach(p => (p.style.display = "none"));

      tab.classList.add("active");
      const activePane = document.getElementById(targetId);
      if (activePane) activePane.style.display = "block";
    });
  });

  const urlParams = new URLSearchParams(window.location.search);
  const profileId = urlParams.get("id");

  let fetchUrl = "";
  if (profileId) {
    fetchUrl = `/api/entrepreneurs/${profileId}`;
  } else if (window.CURRENT_USER) {
    fetchUrl = `/api/profile`;
  } else {
    // Unauthenticated user attempting to view "My Profile" with no ID
    profileContainer.innerHTML = `
      <div class="card" style="text-align: center; padding: 60px 20px; max-width: 600px; margin: 40px auto;">
        <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 10px;">Login Required</h2>
        <p style="color: var(--text-muted); font-size: 14.5px; line-height: 1.6; margin-bottom: 24px;">
          You are viewing this page as a visitor. Please log in to manage your entrepreneur profile, or discover local business profiles in our directory.
        </p>
        <div style="display: flex; justify-content: center; gap: 12px;">
          <a href="register.html?mode=login" class="btn btn-primary">Login to My Account</a>
          <a href="directory.html" class="btn btn-outline">Explore Directory</a>
        </div>
      </div>
    `;
    return;
  }

  fetch(fetchUrl)
    .then(r => {
      if (!r.ok) throw new Error("Profile not found");
      return r.json();
    })
    .then(user => {
      renderProfileData(user);
    })
    .catch(async () => {
      const targetId = profileId || (window.CURRENT_USER ? (window.CURRENT_USER.slug || window.CURRENT_USER.id || window.CURRENT_USER.user_id) : null);
      if (window.UdyamAPI && window.supabaseClient && targetId) {
        try {
          const detail = await window.UdyamAPI.getEntrepreneurDetail(targetId);
          if (detail) {
            renderProfileData(detail);
            return;
          }
        } catch (_) {}
      }
      if (window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.entrepreneurs) && targetId) {
        const found = window.UDYAM_DATA.entrepreneurs.find(e => e.id === targetId || e.user_id === targetId || e.slug === targetId);
        if (found) {
          renderProfileData(found);
          return;
        }
      }
      profileContainer.innerHTML = `
        <div class="card" style="text-align: center; padding: 60px 20px; max-width: 600px; margin: 40px auto;">
          <h2 style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">Profile Not Found</h2>
          <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">The entrepreneur profile you are looking for does not exist.</p>
          <a href="directory.html" class="btn btn-primary btn-sm">Browse Directory</a>
        </div>
      `;
    });
}

function localizeLookingForItem(item) {
  if (!item || !window.i18n) return item;
  const key = String(item).toLowerCase().trim();
  const map = {
    "partners": "directory.partners",
    "partner": "directory.partners",
    "suppliers": "directory.suppliers",
    "supplier": "directory.suppliers",
    "distributors": "directory.distributors",
    "distributor": "directory.distributors",
    "mentors": "directory.mentors",
    "mentor": "directory.mentors",
    "customers": "directory.customers",
    "customer": "directory.customers"
  };
  if (map[key]) {
    return window.i18n.t(map[key], {}, item);
  }
  return item;
}

function renderProfileData(user) {
  window.ACTIVE_PROFILE_USER = user;
  const isOwner = window.CURRENT_USER && window.CURRENT_USER.user_id === user.user_id;
  const isCommunity = user.account_type === "community_member";
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);

  const tCommunity = t("profile.community_member", "Community Member");
  const tEntrepreneur = t("profile.rural_entrepreneur", "Rural Entrepreneur");
  const tVerified = t("profile.verified_badge", "Verified");
  const locDisplay = window.i18n ? window.i18n.localizeLocation(user.location, user.state) : (user.location || "India");

  // Header info - preserve user.name (proper name)
  document.getElementById("profileMainName").textContent = user.name || (isCommunity ? tCommunity : tEntrepreneur);
  
  if (isCommunity) {
    document.getElementById("profileMainSub").textContent = `${tCommunity} • ${locDisplay}`;
  } else {
    const catDisplay = user.category ? t("categories." + user.category, user.category) : t("categories.General Enterprise", "General Enterprise");
    document.getElementById("profileMainSub").textContent = `${catDisplay} • ${locDisplay}`;
  }

  document.getElementById("profileQuote").textContent = user.quote ? `“${user.quote}”` : "";
  document.getElementById("profileLocationText").textContent = locDisplay;

  const verifiedBadge = document.getElementById("profileVerifiedBadge");
  if (verifiedBadge) {
    if (isCommunity) {
      verifiedBadge.style.display = "inline-flex";
      verifiedBadge.className = "badge";
      verifiedBadge.style.background = "#e0f2fe";
      verifiedBadge.style.color = "#0369a1";
      verifiedBadge.style.border = "1px solid #bae6fd";
      verifiedBadge.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right: 4px;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
        ${escapeHtml(tCommunity)}
      `;
    } else if (user.verified) {
      verifiedBadge.style.display = "inline-flex";
      verifiedBadge.className = "badge badge-verified";
      verifiedBadge.style.background = "";
      verifiedBadge.style.color = "";
      verifiedBadge.style.border = "";
      verifiedBadge.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        ${escapeHtml(tVerified)}
      `;
    } else {
      verifiedBadge.style.display = "none";
    }
  }

  const avatarContainer = document.getElementById("profileAvatarLarge");
  if (avatarContainer) {
    if (user.avatar) {
      avatarContainer.innerHTML = `<img src="${user.avatar}" alt="${escapeHtml(user.name)}">`;
    } else {
      avatarContainer.innerHTML = `<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: var(--primary); color: #fff; font-size: 28px; font-weight: 700;">${getInitials(user.name)}</div>`;
    }
  }

  // Header action buttons
  const headerActions = document.getElementById("profileHeaderActions");
  if (headerActions) {
    if (isOwner) {
      headerActions.innerHTML = `
        <button class="btn btn-primary" onclick="window.openEditProfileModal()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          ${escapeHtml(t("profile.edit_profile", "Edit Profile"))}
        </button>
      `;
    } else {
      const isConn = user.is_connected || false;
      const tConn = isConn ? t("directory.connected", "Connected ✓") : t("directory.connect", "Connect");
      headerActions.innerHTML = `
        <button class="btn ${isConn ? 'btn-outline connected' : 'btn-primary'} btn-connect" data-user-id="${user.user_id}">
          ${escapeHtml(tConn)}
        </button>
        <a href="messages.html?user=${user.user_id}" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 6px;">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          ${escapeHtml(t("profile.message", "Message"))}
        </a>
        <button class="btn btn-outline" onclick="window.openProposeModal('${user.user_id}', '${escapeHtml(user.name)}')">
          ${escapeHtml(t("profile.collaborate", "Collaborate"))}
        </button>
      `;
    }
  }

  // About pane
  const defaultDesc = isCommunity
    ? t("profile.community_desc", "Community supporter discovering and networking with rural entrepreneurs across India.")
    : t("profile.default_desc", "Building sustainable rural enterprise and supporting local livelihoods.");
  const defaultStory = isCommunity
    ? t("profile.community_story", "Active member participating in discussions and discovering authentic rural artisanal crafts and organic produce.")
    : t("profile.default_story", "Founded with a mission to bring authentic rural craft and produce to national recognition.");

  document.getElementById("profileAboutDesc").textContent = user.description || defaultDesc;
  document.getElementById("profileAboutStory").textContent = user.full_story || defaultStory;

  // Products pane
  const productsGrid = document.getElementById("profileProductsGrid");
  const addProdBtn = document.getElementById("btnAddProductBtn");
  
  if (addProdBtn) {
    addProdBtn.style.display = (isOwner && !isCommunity) ? "inline-flex" : "none";
    addProdBtn.textContent = t("profile.add_product", "+ Add Product");
  }

  if (productsGrid) {
    if (isCommunity) {
      productsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 36px 20px; text-align: center; color: var(--text-muted); background: #f8fafc; border-radius: 6px; border: 1px dashed var(--border-color);">
          <p style="font-size: 14px; margin-bottom: 12px;">${escapeHtml(t("profile.community_no_products", "This is a Community Member profile. Product showcasing is reserved for registered Entrepreneurs."))}</p>
          <a href="directory.html" class="btn btn-outline btn-sm">${escapeHtml(t("profile.explore_products", "Explore Entrepreneur Products"))}</a>
        </div>
      `;
    } else {
      const products = user.products || [];
      if (products.length === 0) {
        productsGrid.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 30px; text-align: center; color: var(--text-muted); background: #f8fafc; border-radius: 6px;">
            <p>${escapeHtml(t("profile.no_products", "No products or catalog items listed yet."))}</p>
            ${isOwner ? `<button class="btn btn-primary btn-sm" style="margin-top: 10px;" onclick="window.openAddProductModal()">${escapeHtml(t("profile.add_first_product", "+ Add Your First Product"))}</button>` : ''}
          </div>
        `;
      } else {
        const tRemove = t("profile.remove_product", "Remove Product");
        const tInquire = t("profile.inquire_catalog", "Inquire Catalog");
        productsGrid.innerHTML = products.map(p => `
          <div class="card" style="padding: 12px;">
            <div style="height: 140px; border-radius: 6px; overflow: hidden; margin-bottom: 10px;">
              <img src="${p.image || 'assets/images/hero_entrepreneur.jpg'}" alt="${escapeHtml(p.name)}" style="width: 100%; height: 100%; object-fit: cover;">
            </div>
            <h3 style="font-size: 14px; font-weight: 600;">${escapeHtml(p.name)}</h3>
            <div style="font-size: 13px; color: var(--primary); font-weight: 600; margin-bottom: 8px;">${escapeHtml(p.price)}</div>
            ${isOwner ? `
              <button class="btn btn-outline btn-sm btn-block" style="color: #b91c1c; border-color: #fecaca;" onclick="window.deleteProduct(${p.id})">${escapeHtml(tRemove)}</button>
            ` : `
              <button class="btn btn-outline btn-sm btn-block" onclick="showToast('${escapeHtml(tInquire)}')">${escapeHtml(tInquire)}</button>
            `}
          </div>
        `).join("");
      }
    }
  }

  // Collaboration priorities
  const collabList = document.getElementById("profileCollabList");
  if (collabList) {
    if (isCommunity) {
      collabList.innerHTML = `<p style="color: var(--text-muted); font-size: 13.5px;">${escapeHtml(t("profile.community_collab_desc", "Community members explore and support collaborations in the Collaborations section."))}</p>`;
    } else {
      const lookingFor = Array.isArray(user.looking_for) ? user.looking_for : [];
      if (lookingFor.length === 0) {
        collabList.innerHTML = `<p style="color: var(--text-muted); font-size: 13.5px;">${escapeHtml(t("profile.no_collabs", "No active collaboration priorities listed yet."))}</p>`;
      } else {
        const tPriorityDesc = t("profile.collab_priority_desc", "Collaborate to expand market reach and strengthen operations.");
        collabList.innerHTML = lookingFor.map((item, idx) => `
          <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border: 1px solid var(--border-color);">
            <h3 style="font-size: 13.5px; font-weight: 600; color: var(--primary-dark);">${idx + 1}. ${escapeHtml(localizeLookingForItem(item))}</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">${escapeHtml(tPriorityDesc)}</p>
          </div>
        `).join("");
      }
    }
  }

  // Social & Contact links
  const socialList = document.getElementById("profileSocialList");
  if (socialList) {
    const rawWeb = user.website ? String(user.website).trim() : "";
    const isSafeWeb = rawWeb && (rawWeb.startsWith("http://") || rawWeb.startsWith("https://") || (!rawWeb.includes(":") && rawWeb.includes(".")));
    const webHref = isSafeWeb ? (rawWeb.startsWith("http") ? rawWeb : `https://${rawWeb}`) : null;

    const tRole = t("profile.role", "Role");
    const tEnterprise = t("profile.enterprise", "Enterprise");
    const tPhone = t("profile.phone", "WhatsApp / Phone");
    const tContact = t("profile.contact_details", "Contact");
    const tContactMutual = t("profile.contact_mutual", "Available upon mutual connection");
    const tWebsite = t("profile.website", "Website");
    const tRegMember = t("profile.registered_member", "Registered Member");
    const tVerifiedPrefix = t("profile.verified_prefix", "ThriveHub Verified");

    socialList.innerHTML = `
      <div><strong>${escapeHtml(tRole)}:</strong> ${escapeHtml(isCommunity ? tCommunity : tEntrepreneur)}</div>
      ${user.business_name ? `<div><strong>${escapeHtml(tEnterprise)}:</strong> ${escapeHtml(user.business_name)}</div>` : ''}
      ${user.phone ? `<div><strong>${escapeHtml(tPhone)}:</strong> <a href="tel:${escapeHtml(user.phone)}">${escapeHtml(user.phone)}</a></div>` : `<div><strong>${escapeHtml(tContact)}:</strong> ${escapeHtml(tContactMutual)}</div>`}
      ${webHref ? `<div><strong>${escapeHtml(tWebsite)}:</strong> <a href="${escapeHtml(webHref)}" target="_blank" rel="noopener noreferrer">${escapeHtml(rawWeb)}</a></div>` : ''}
      <div><strong>${escapeHtml(tRegMember)}:</strong> ${escapeHtml(tVerifiedPrefix)} ${escapeHtml(isCommunity ? tCommunity : tVerified)}</div>
    `;
  }

  // Looking for aside widget
  const lookingForList = document.getElementById("profileLookingForList");
  if (lookingForList) {
    if (isCommunity) {
      lookingForList.innerHTML = `<span style="font-size: 13px; color: var(--text-muted);">• ${escapeHtml(t("profile.community_support_networking", "Community support & networking"))}</span>`;
    } else {
      const lookingFor = Array.isArray(user.looking_for) ? user.looking_for : [];
      lookingForList.innerHTML = lookingFor.length > 0
        ? lookingFor.map(item => `<span style="font-size: 13px; color: var(--text-main);">• ${escapeHtml(localizeLookingForItem(item))}</span>`).join("")
        : `<span style="font-size: 13px; color: var(--text-muted);">• ${escapeHtml(t("profile.open_partnerships", "Open to partnerships"))}</span>`;
    }
  }
}

window.refreshProfilePage = function () {
  if (window.ACTIVE_PROFILE_USER) {
    renderProfileData(window.ACTIVE_PROFILE_USER);
  }
};

// -----------------------------------------------------------------------------
// Edit Profile Modal & Logic with Location Dataset
// -----------------------------------------------------------------------------
window.openEditProfileModal = function () {
  const u = window.ACTIVE_PROFILE_USER || window.CURRENT_USER;
  if (!u) return;

  let modal = document.getElementById("editProfileModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "editProfileModal";
    modal.className = "modal-backdrop";
    document.body.appendChild(modal);
  }

  const lookingForStr = Array.isArray(u.looking_for) ? u.looking_for.join(", ") : (u.looking_for || "");
  const isCommunity = u.account_type === "community_member";
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);

  const modalTitle = isCommunity ? t("profile.edit_community_title", "Edit Community Member Profile") : t("profile.edit_profile", "Edit Enterprise Profile");

  modal.innerHTML = `
    <div class="modal-dialog" style="max-width: 640px;">
      <div class="modal-header">
        <h3 class="modal-title">${escapeHtml(modalTitle)}</h3>
        <button class="modal-close-btn" onclick="document.getElementById('editProfileModal').classList.remove('active')">&times;</button>
      </div>
      <div class="modal-body" style="max-height: 78vh; overflow-y: auto;">
        <div id="editProfileAlert" style="display: none; background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 10px; font-size: 13px; border-radius: 6px; margin-bottom: 12px;"></div>
        <form id="editProfileForm">
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.edit_name", "Full Name"))} *</label>
            <input type="text" id="editName" class="form-input" value="${escapeHtml(u.name || '')}" required>
          </div>
          ${!isCommunity ? `
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.edit_business", "Business / Enterprise Name"))}</label>
            <input type="text" id="editBizName" class="form-input" value="${escapeHtml(u.business_name || '')}">
          </div>
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.edit_category", "Category"))}</label>
            <select id="editCategory" class="form-select">
              <option value="Handicrafts" ${u.category === 'Handicrafts' ? 'selected' : ''}>${escapeHtml(t("categories.Handicrafts", "Handicrafts"))}</option>
              <option value="Agriculture" ${u.category === 'Agriculture' ? 'selected' : ''}>${escapeHtml(t("categories.Agriculture", "Agriculture"))}</option>
              <option value="Food Products" ${u.category === 'Food Products' ? 'selected' : ''}>${escapeHtml(t("categories.Food Products", "Food Products"))}</option>
              <option value="Organic Products" ${u.category === 'Organic Products' ? 'selected' : ''}>${escapeHtml(t("categories.Organic Products", "Organic Products"))}</option>
              <option value="Digital Services" ${u.category === 'Digital Services' ? 'selected' : ''}>${escapeHtml(t("categories.Digital Services", "Digital Services"))}</option>
              <option value="Textiles & Handlooms" ${u.category === 'Textiles & Handlooms' ? 'selected' : ''}>${escapeHtml(t("categories.Textiles & Handlooms", "Textiles & Handlooms"))}</option>
              <option value="General Enterprise" ${u.category === 'General Enterprise' ? 'selected' : ''}>${escapeHtml(t("categories.General Enterprise", "General Enterprise"))}</option>
            </select>
          </div>
          ` : ''}

          <!-- Location Fields (State, District, Village, Pincode, Landmark) -->
          <div style="font-weight: 600; font-size: 13.5px; color: var(--primary-dark); margin: 16px 0 8px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px;">
            ${escapeHtml(t("profile.location_details", "Location & Address (Indian Dataset)"))}
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label">${escapeHtml(t("profile.state_ut", "State / UT"))}</label>
              <select id="editState" class="form-select">
                <option value="">${escapeHtml(t("profile.select_state", "Select State"))}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">${escapeHtml(t("profile.district", "District"))}</label>
              <select id="editDistrict" class="form-select" disabled>
                <option value="">${escapeHtml(t("profile.select_district", "Select District"))}</option>
              </select>
            </div>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label">${escapeHtml(t("profile.town_city", "Village / Town / City"))}</label>
              <input type="text" id="editTown" class="form-input" value="${escapeHtml(u.subdistrict_or_town || '')}">
            </div>
            <div class="form-group">
              <label class="form-label">${escapeHtml(t("profile.pincode", "6-Digit PIN Code"))}</label>
              <input type="text" id="editPincode" class="form-input" maxlength="6" value="${escapeHtml(u.pincode || '')}" placeholder="e.g. 412803">
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.landmark", "Address / Landmark (Private by Default)"))}</label>
            <input type="text" id="editLandmark" class="form-input" value="${escapeHtml(u.address_landmark || '')}" placeholder="${escapeHtml(t("profile.landmark", "Street, post office, or landmark"))}">
          </div>
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.location_preference", "Public Location Display Preference"))}</label>
            <select id="editLocPref" class="form-select">
              <option value="district_state" ${u.location_display_preference === 'district_state' ? 'selected' : ''}>${escapeHtml(t("profile_setup.loc_pref_district", "District, State (e.g. Satara, Maharashtra - Private Address)"))}</option>
              <option value="village_district_state" ${u.location_display_preference === 'village_district_state' ? 'selected' : ''}>${escapeHtml(t("profile_setup.loc_pref_village", "Village, District, State"))}</option>
              <option value="state_only" ${u.location_display_preference === 'state_only' ? 'selected' : ''}>${escapeHtml(t("profile_setup.loc_pref_state", "State Only"))}</option>
            </select>
          </div>

          ${!isCommunity ? `
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.edit_quote", "Short Quote / Tagline"))}</label>
            <input type="text" id="editQuote" class="form-input" value="${escapeHtml(u.quote || '')}">
          </div>
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.about", "About Enterprise"))}</label>
            <textarea id="editDesc" class="form-textarea" rows="2">${escapeHtml(u.description || '')}</textarea>
          </div>
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.our_story", "Our Story & Vision"))}</label>
            <textarea id="editStory" class="form-textarea" rows="3">${escapeHtml(u.full_story || '')}</textarea>
          </div>
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.looking_for", "Collaboration Priorities (comma-separated)"))}</label>
            <input type="text" id="editLookingFor" class="form-input" value="${escapeHtml(lookingForStr)}" placeholder="e.g. Eco packaging, Interstate buyers">
          </div>
          ` : `
          <div class="form-group">
            <label class="form-label">${escapeHtml(t("profile.about", "About You / Bio"))}</label>
            <textarea id="editDesc" class="form-textarea" rows="2">${escapeHtml(u.description || '')}</textarea>
          </div>
          `}
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label">${escapeHtml(t("profile.website", "Website"))}</label>
              <input type="text" id="editWebsite" class="form-input" value="${escapeHtml(u.website || '')}" placeholder="https://...">
            </div>
            <div class="form-group">
              <label class="form-label">${escapeHtml(t("profile.phone", "Phone / WhatsApp"))}</label>
              <input type="text" id="editPhone" class="form-input" value="${escapeHtml(u.phone || '')}">
            </div>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary btn-sm" onclick="document.getElementById('editProfileModal').classList.remove('active')">${escapeHtml(t("common.cancel", "Cancel"))}</button>
        <button class="btn btn-primary btn-sm" onclick="window.saveProfileEdits()">${escapeHtml(t("profile.save_changes", "Save Profile"))}</button>
      </div>
    </div>
  `;

  // Dynamic dropdown logic backed by /api/locations
  const stateSelect = document.getElementById("editState");
  const districtSelect = document.getElementById("editDistrict");

  fetch("/api/locations")
    .then(r => r.json())
    .then(data => {
      if (data && data.locations) {
        window.LOCATIONS_DATA = data.locations;
        const states = data.states || Object.keys(data.locations).sort();
        states.forEach(st => {
          const opt = document.createElement("option");
          opt.value = st;
          opt.textContent = window.i18n ? window.i18n.localizeLocation(st, st) : st;
          if (u.state === st) opt.selected = true;
          stateSelect.appendChild(opt);
        });

        function updateDistricts(selectedState, selectedDistrict) {
          const selectDistPlaceholder = window.i18n ? window.i18n.t("profile.select_district", {}, "Select District") : "Select District";
          districtSelect.innerHTML = `<option value="">${escapeHtml(selectDistPlaceholder)}</option>`;
          if (selectedState && window.LOCATIONS_DATA[selectedState]) {
            window.LOCATIONS_DATA[selectedState].forEach(dist => {
              const opt = document.createElement("option");
              opt.value = dist;
              opt.textContent = dist;
              if (selectedDistrict === dist) opt.selected = true;
              districtSelect.appendChild(opt);
            });
            districtSelect.disabled = false;
          } else {
            districtSelect.disabled = true;
          }
        }

        updateDistricts(u.state, u.district);

        stateSelect.addEventListener("change", function () {
          updateDistricts(stateSelect.value, "");
        });
      }
    })
    .catch(() => {});

  modal.classList.add("active");
};

window.saveProfileEdits = function () {
  const alertBox = document.getElementById("editProfileAlert");
  if (alertBox) alertBox.style.display = "none";
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);

  const pincode = document.getElementById("editPincode") ? document.getElementById("editPincode").value.trim() : "";
  if (pincode && !/^[1-9][0-9]{5}$/.test(pincode)) {
    const pinErr = t("profile_setup.pincode_invalid", "Please enter a valid 6-digit Indian PIN code.");
    if (alertBox) {
      alertBox.textContent = pinErr;
      alertBox.style.display = "block";
    } else {
      showToast(pinErr);
    }
    return;
  }

  const payload = {
    name: document.getElementById("editName").value.trim(),
    business_name: document.getElementById("editBizName") ? document.getElementById("editBizName").value.trim() : "",
    category: document.getElementById("editCategory") ? document.getElementById("editCategory").value : "",
    state: document.getElementById("editState") ? document.getElementById("editState").value.trim() : "",
    district: document.getElementById("editDistrict") ? document.getElementById("editDistrict").value.trim() : "",
    subdistrict_or_town: document.getElementById("editTown") ? document.getElementById("editTown").value.trim() : "",
    pincode: pincode,
    address_landmark: document.getElementById("editLandmark") ? document.getElementById("editLandmark").value.trim() : "",
    location_display_preference: document.getElementById("editLocPref") ? document.getElementById("editLocPref").value : "district_state",
    quote: document.getElementById("editQuote") ? document.getElementById("editQuote").value.trim() : "",
    description: document.getElementById("editDesc") ? document.getElementById("editDesc").value.trim() : "",
    full_story: document.getElementById("editStory") ? document.getElementById("editStory").value.trim() : "",
    looking_for: document.getElementById("editLookingFor") ? document.getElementById("editLookingFor").value.trim() : "",
    website: document.getElementById("editWebsite") ? document.getElementById("editWebsite").value.trim() : "",
    phone: document.getElementById("editPhone") ? document.getElementById("editPhone").value.trim() : ""
  };

  fetch("/api/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(async r => {
    const res = await r.json();
    if (r.ok && res.success && res.user) {
      document.getElementById("editProfileModal").classList.remove("active");
      showToast(t("profile.profile_updated", "Profile updated and persisted successfully!"));
      window.CURRENT_USER = res.user;
      initAuthSession();
      renderProfileData(res.user);
    } else {
      const errTxt = res.error || t("profile_setup.save_error", "Failed to save profile.");
      if (alertBox) {
        alertBox.textContent = errTxt;
        alertBox.style.display = "block";
      } else {
        showToast(errTxt);
      }
    }
  })
  .catch(() => showToast(t("profile_setup.network_error", "Network error saving profile.")));
};

// -----------------------------------------------------------------------------
// Add / Delete Product Logic
// -----------------------------------------------------------------------------
window.openAddProductModal = function () {
  let modal = document.getElementById("addProductModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "addProductModal";
    modal.className = "modal-backdrop";
    document.body.appendChild(modal);
  }
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);

  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-header">
        <h3 class="modal-title">${escapeHtml(t("profile.add_product", "Add a Product or Catalog Item"))}</h3>
        <button class="modal-close-btn" onclick="document.getElementById('addProductModal').classList.remove('active')">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">${escapeHtml(t("profile.product_name", "Product Name"))} <span class="required">*</span></label>
          <input type="text" id="newProdName" class="form-input" placeholder="e.g. Handwoven Moonj Basket" required>
        </div>
        <div class="form-group">
          <label class="form-label">${escapeHtml(t("profile.price_unit", "Price Range / Unit Price"))} <span class="required">*</span></label>
          <input type="text" id="newProdPrice" class="form-input" placeholder="e.g. ₹450 - ₹1,200" required>
        </div>
        <div class="form-group">
          <label class="form-label">${escapeHtml(t("profile.image_url", "Sample Image Option"))}</label>
          <select id="newProdImage" class="form-select">
            <option value="assets/images/hero_entrepreneur.jpg">Handicraft Weaving</option>
            <option value="assets/images/potter_artisan.jpg">Terracotta Vessels</option>
            <option value="assets/images/packaging_spices.jpg">Spice & Food Packaging</option>
            <option value="assets/images/farmer_greenharvest.jpg">Organic Pulses / Harvest</option>
            <option value="assets/images/crafts_banner.jpg">Artisan Textiles</option>
          </select>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary btn-sm" onclick="document.getElementById('addProductModal').classList.remove('active')">${escapeHtml(t("common.cancel", "Cancel"))}</button>
        <button class="btn btn-primary btn-sm" onclick="window.saveNewProduct()">${escapeHtml(t("profile.save_product", "Add to Profile"))}</button>
      </div>
    </div>
  `;

  modal.classList.add("active");
};

window.saveNewProduct = function () {
  const name = document.getElementById("newProdName").value.trim();
  const price = document.getElementById("newProdPrice").value.trim();
  const image = document.getElementById("newProdImage").value;
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);

  if (!name || !price) {
    showToast(t("profile.product_name_price_required", "Please provide a product name and price."));
    return;
  }

  fetch("/api/profile/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, price, image })
  })
  .then(r => r.json())
  .then(res => {
    if (res.success) {
      document.getElementById("addProductModal").classList.remove("active");
      showToast(t("profile.product_added", "Product added to your catalog!"));
      initProfilePage();
    } else {
      showToast(res.error || t("profile.product_add_failed", "Failed to add product."));
    }
  })
  .catch(() => showToast(t("common.network_error", "Network error.")));
};

window.deleteProduct = function (prodId) {
  const confirmMsg = window.i18n ? window.i18n.t("profile.confirm_remove_product", {}, "Are you sure you want to remove this product?") : "Are you sure you want to remove this product?";
  if (!confirm(confirmMsg)) return;

  fetch(`/api/profile/products/${prodId}`, { method: "DELETE" })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        showToast(window.i18n ? window.i18n.t("profile.remove_product", {}, "Product removed.") : "Product removed.");
        initProfilePage();
      } else {
        showToast(res.error || "Failed to remove product.");
      }
    })
    .catch(() => showToast("Network error."));
};

// -----------------------------------------------------------------------------
// Propose Collaboration / Message Modal (Direct to Entrepreneur)
// -----------------------------------------------------------------------------
window.openProposeModal = function (targetUserId, targetName) {
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
  if (!window.CURRENT_USER) {
    showToast(t("collab.login_submit_proposal", "Please log in to send collaboration proposals."));
    setTimeout(() => {
      window.location.href = "register.html?mode=login";
    }, 1000);
    return;
  }

  let modal = document.getElementById("directProposeModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "directProposeModal";
    modal.className = "modal-backdrop";
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-header">
        <h3 class="modal-title">${escapeHtml(t("collab.collaborate", "Collaborate"))}: ${escapeHtml(targetName)}</h3>
        <button class="modal-close-btn" onclick="document.getElementById('directProposeModal').classList.remove('active')">&times;</button>
      </div>
      <div class="modal-body">
        <p style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 14px;">
          ${escapeHtml(t("collab.send_proposal", "Send a partnership inquiry or collaboration proposal directly to"))} ${escapeHtml(targetName)}.
        </p>
        <div class="form-group">
          <label class="form-label">${escapeHtml(t("collab.proposal_message_label", "Your Proposal Message"))} <span class="required">*</span></label>
          <textarea id="directProposalMsg" class="form-textarea" rows="4" placeholder="${escapeHtml(t("collab.proposal_placeholder", "Describe your business and how you would like to partner together..."))}"></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary btn-sm" onclick="document.getElementById('directProposeModal').classList.remove('active')">${escapeHtml(t("common.cancel", "Cancel"))}</button>
        <button class="btn btn-primary btn-sm" onclick="window.sendDirectProposal('${targetUserId}')">${escapeHtml(t("collab.submit_proposal", "Send Proposal"))}</button>
      </div>
    </div>
  `;

  modal.classList.add("active");
};

window.sendDirectProposal = function (targetUserId) {
  const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
  const msg = document.getElementById("directProposalMsg") ? document.getElementById("directProposalMsg").value.trim() : "";
  if (!msg) {
    showToast(t("collab.msg_required", "Please enter a message for your proposal."));
    return;
  }

  fetch("/api/collaborations/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ receiver_id: targetUserId, message: msg })
  })
  .then(r => r.json())
  .then(res => {
    if (res.success) {
      document.getElementById("directProposeModal").classList.remove("active");
      showToast(t("collab.sent_success", "Collaboration proposal recorded and sent!"));
    } else {
      showToast(res.error || t("collab.proposal_failed", "Failed to send proposal."));
    }
  })
  .catch(() => showToast(t("common.network_error", "Network error.")));
};

// -----------------------------------------------------------------------------
// Collaborations Page (Screen 6)
// -----------------------------------------------------------------------------
function initCollaborationsPage() {
  const collabTabs = document.querySelectorAll(".collab-tab-btn");
  const collabContainer = document.getElementById("collabList");
  if (!collabContainer) return;

  window.CURRENT_COLLAB_FILTER = window.CURRENT_COLLAB_FILTER || "Seeking Partners";

  function loadCollaborations(filterType = "Seeking Partners") {
    window.CURRENT_COLLAB_FILTER = filterType;
    const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);

    if (filterType === "My Requests") {
      loadMyRequests();
      return;
    }

    if (filterType === "Joint Projects") {
      loadJointProjects();
      return;
    }

    fetch(`/api/collaborations?type=${filterType}`)
      .then(res => res.json())
      .then(items => {
        if (!items || items.length === 0) {
          collabContainer.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
              <p style="color: var(--text-muted); font-size: 15px;">${escapeHtml(t("collab.no_opportunities", "No collaboration posts found under this category."))}</p>
            </div>
          `;
          return;
        }

        const tViewDetails = t("collab.view_details", "View Details");
        const tAllIndia = t("collab.all_india", "All India");

        collabContainer.innerHTML = items.map(c => {
          const catDisplay = t("categories." + c.category, c.category);
          const tagDisplay = t("collab." + c.tag, c.tag || c.category);
          const locDisplay = window.i18n ? window.i18n.localizeLocation(c.location) : (c.location || tAllIndia);
          const timeDisplay = c.time_ago || t("common.recently", "Recently");

          return `
            <div class="collab-card">
              <div class="collab-card-left">
                <div class="collab-thumb">
                  <img src="${c.thumb || 'assets/images/packaging_spices.jpg'}" alt="${escapeHtml(c.title)}">
                </div>
                <div class="collab-details">
                  <h3 class="collab-card-title">${escapeHtml(c.title)}</h3>
                  <p class="collab-card-desc">${escapeHtml(c.subtitle || c.full_description.substring(0, 100))}</p>
                  <div class="collab-badges">
                    <span class="badge badge-category">${escapeHtml(catDisplay)}</span>
                    <span class="badge badge-tag">${escapeHtml(tagDisplay)}</span>
                    <span class="badge badge-tag">${escapeHtml(locDisplay)}</span>
                  </div>
                </div>
              </div>
              <div class="collab-card-right">
                <div class="collab-author-preview">
                  <div class="avatar-circle" style="width: 32px; height: 32px;">
                    <img src="${c.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(c.author_name)}">
                  </div>
                  <div class="collab-author-info">
                    <span class="collab-author-name">${escapeHtml(c.author_name)}</span>
                    <span class="collab-time">${escapeHtml(timeDisplay)}</span>
                  </div>
                </div>
                <button class="btn btn-outline btn-sm" onclick="window.openCollabModal('${escapeHtml(c.collab_id)}')">${escapeHtml(tViewDetails)}</button>
              </div>
            </div>
          `;
        }).join("");
      })
      .catch(async () => {
        let fallbackCollabs = [];
        if (window.UdyamAPI && window.supabaseClient) {
          try {
            fallbackCollabs = await window.UdyamAPI.getCollaborations();
          } catch (_) {}
        }
        if (fallbackCollabs.length === 0 && window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.collaborations)) {
          fallbackCollabs = window.UDYAM_DATA.collaborations.map(c => ({
            collab_id: c.id,
            author_id: c.authorId || "asha-devi",
            author_name: c.author || "Asha Devi",
            author_avatar: c.avatar || "assets/images/crafts_banner.jpg",
            title: c.title,
            subtitle: c.description || c.fullDescription,
            full_description: c.fullDescription || c.description,
            category: c.category,
            collab_type: c.type,
            tag: c.tag || c.type,
            location: c.location || "Uttar Pradesh",
            thumb: c.image || "assets/images/crafts_banner.jpg",
            time_ago: c.time || "Recently"
          }));
        }
        if (filterType !== "All Opportunities" && filterType !== "all") {
          fallbackCollabs = fallbackCollabs.filter(c =>
            (c.category && c.category.toLowerCase() === filterType.toLowerCase()) ||
            (c.collab_type && c.collab_type.toLowerCase() === filterType.toLowerCase()) ||
            (c.tag && c.tag.toLowerCase() === filterType.toLowerCase())
          );
        }
        if (fallbackCollabs.length > 0) {
          renderCollabCards(fallbackCollabs);
        }
      });
  }

  function renderCollabCards(items) {
    const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
    const tViewDetails = t("collab.view_details", "View Details");
    const tAllIndia = t("collab.all_india", "All India");

    collabContainer.innerHTML = items.map(c => {
      const catDisplay = t("categories." + c.category, c.category);
      const tagDisplay = t("collab." + c.tag, c.tag || c.category);
      const locDisplay = window.i18n ? window.i18n.localizeLocation(c.location) : (c.location || tAllIndia);
      const timeDisplay = c.time_ago || t("common.recently", "Recently");

      return `
        <div class="collab-card">
          <div class="collab-card-left">
            <div class="collab-thumb">
              <img src="${c.thumb || 'assets/images/packaging_spices.jpg'}" alt="${escapeHtml(c.title)}">
            </div>
            <div class="collab-details">
              <h3 class="collab-card-title">${escapeHtml(c.title)}</h3>
              <p class="collab-card-desc">${escapeHtml(c.subtitle || (c.full_description ? c.full_description.substring(0, 100) : ''))}</p>
              <div class="collab-badges">
                <span class="badge badge-category">${escapeHtml(catDisplay)}</span>
                <span class="badge badge-tag">${escapeHtml(tagDisplay)}</span>
                <span class="badge badge-tag">${escapeHtml(locDisplay)}</span>
              </div>
            </div>
          </div>
          <div class="collab-card-right">
            <div class="collab-author-preview">
              <div class="avatar-circle" style="width: 32px; height: 32px;">
                <img src="${c.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(c.author_name)}">
              </div>
              <div class="collab-author-info">
                <span class="collab-author-name">${escapeHtml(c.author_name)}</span>
                <span class="collab-time">${escapeHtml(timeDisplay)}</span>
              </div>
            </div>
            <button class="btn btn-outline btn-sm" onclick="window.openCollabModal('${escapeHtml(c.collab_id)}')">${escapeHtml(tViewDetails)}</button>
          </div>
        </div>
      `;
    }).join("");
  }

  function loadMyRequests() {
    const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
    if (!window.CURRENT_USER) {
      collabContainer.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <p style="color: var(--text-muted); font-size: 15px; margin-bottom: 14px;">${escapeHtml(t("collab.login_view_requests", "Please log in to view your partnership requests."))}</p>
          <a href="register.html?mode=login" class="btn btn-primary btn-sm">${escapeHtml(t("nav.login", "Login"))}</a>
        </div>
      `;
      return;
    }

    fetch("/api/collaborations/requests")
      .then(r => r.json())
      .then(data => {
        const received = data.received || [];
        const sent = data.sent || [];

        if (received.length === 0 && sent.length === 0) {
          collabContainer.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
              <p style="color: var(--text-muted); font-size: 15px;">${escapeHtml(t("collab.no_requests", "You have no active partnership requests."))}</p>
            </div>
          `;
          return;
        }

        let html = "";
        if (received.length > 0) {
          html += `<h2 style="font-size: 16px; font-weight: 700; margin-bottom: 12px;">${escapeHtml(t("collab.received_requests_title", "Received Partnership Requests"))}</h2>`;
          html += received.map(req => {
            const senderCat = t("categories." + req.sender_category, req.sender_category);
            const senderLoc = window.i18n ? window.i18n.localizeLocation(req.sender_location) : req.sender_location;
            const statusLabel = req.status === 'pending'
              ? t("collab.status_pending", "Pending")
              : (req.status === 'accepted' ? t("collab.status_accepted", "Accepted") : t("collab.status_rejected", "Rejected"));

            return `
              <div class="card" style="padding: 18px; margin-bottom: 14px; border: 1px solid var(--border-color);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px;">
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="avatar-circle" style="width: 38px; height: 38px;">
                      <img src="${req.sender_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(req.sender_name)}">
                    </div>
                    <div>
                      <span style="font-weight: 600; font-size: 14.5px;">${escapeHtml(req.sender_name)}</span>
                      <div style="font-size: 12px; color: var(--text-muted);">${escapeHtml(senderCat)} • ${escapeHtml(senderLoc)}</div>
                    </div>
                  </div>
                  <span class="badge badge-${req.status}">${escapeHtml(statusLabel)}</span>
                </div>
                ${req.collab_title ? `<div style="font-size: 13px; font-weight: 600; color: var(--primary); margin-bottom: 8px;">${escapeHtml(t("collab.regarding", "Regarding"))}: ${escapeHtml(req.collab_title)}</div>` : ''}
                <p style="font-size: 13.5px; line-height: 1.6; color: var(--text-main); background: #f8fafc; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                  “${escapeHtml(req.message)}”
                </p>
                ${req.status === 'pending' ? `
                  <div style="display: flex; justify-content: flex-end; gap: 8px;">
                    <button class="btn btn-outline btn-sm" onclick="window.respondToRequest(${req.id}, 'reject')">${escapeHtml(t("collab.decline", "Decline"))}</button>
                    <button class="btn btn-primary btn-sm" onclick="window.respondToRequest(${req.id}, 'accept')">${escapeHtml(t("collab.accept", "Accept Collaboration"))}</button>
                  </div>
                ` : ''}
              </div>
            `;
          }).join("");
        }

        if (sent.length > 0) {
          html += `<h2 style="font-size: 16px; font-weight: 700; margin: 24px 0 12px;">${escapeHtml(t("collab.sent_proposals_title", "Sent Proposals"))}</h2>`;
          html += sent.map(req => {
            const receiverCat = t("categories." + req.receiver_category, req.receiver_category);
            const statusLabel = req.status === 'pending'
              ? t("collab.status_pending", "Pending")
              : (req.status === 'accepted' ? t("collab.status_accepted", "Accepted") : t("collab.status_rejected", "Rejected"));

            return `
              <div class="card" style="padding: 16px; margin-bottom: 12px; border: 1px solid var(--border-color);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <div style="font-weight: 600; font-size: 14px;">${escapeHtml(t("collab.sent_to", "Sent to"))}: ${escapeHtml(req.receiver_name)} (${escapeHtml(receiverCat)})</div>
                  <span class="badge badge-${req.status}">${escapeHtml(statusLabel)}</span>
                </div>
                <p style="font-size: 13px; color: var(--text-muted);">“${escapeHtml(req.message)}”</p>
              </div>
            `;
          }).join("");
        }

        collabContainer.innerHTML = html;
      });
  }

  function loadJointProjects() {
    const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
    fetch("/api/collaborations/projects")
      .then(r => r.json())
      .then(projects => {
        if (!projects || projects.length === 0) {
          collabContainer.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
              <p style="color: var(--text-muted); font-size: 15px;">${escapeHtml(t("collab.no_projects", "No collaborative projects formed yet. Partner with other entrepreneurs to get started!"))}</p>
            </div>
          `;
          return;
        }

        collabContainer.innerHTML = projects.map(p => {
          const catDisplay = t("categories." + p.category, p.category || t("collab.joint_projects", "Joint Project"));
          const statusDisplay = t("collab.open", "Active");
          const tPartners = t("collab.partners_label", "Partners:");
          const tChat = t("collab.project_chat", "Project Chat");

          return `
            <div class="collab-card">
              <div class="collab-card-left">
                <div class="collab-thumb">
                  <img src="assets/images/crafts_banner.jpg" alt="${escapeHtml(p.title)}">
                </div>
                <div class="collab-details">
                  <h3 class="collab-card-title">${escapeHtml(p.title)}</h3>
                  <p class="collab-card-desc">${escapeHtml(p.description)}</p>
                  <div class="collab-badges">
                    <span class="badge badge-category">${escapeHtml(catDisplay)}</span>
                    <span class="badge badge-tag" style="background: #dcfce7; color: #166534;">${escapeHtml(statusDisplay)}</span>
                  </div>
                </div>
              </div>
              <div class="collab-card-right">
                <div style="font-size: 12px; color: var(--text-muted); text-align: right;">
                  <div>${escapeHtml(tPartners)}</div>
                  <div style="font-weight: 600; color: var(--text-main);">${escapeHtml(p.partner1_name)} & ${escapeHtml(p.partner2_name)}</div>
                </div>
                ${(window.CURRENT_USER && (window.CURRENT_USER.user_id === p.partner1_id || window.CURRENT_USER.user_id === p.partner2_id)) ? `
                  <a href="messages.html?project=${p.id}" class="btn btn-primary btn-sm" style="margin-top: 8px; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                    ${escapeHtml(tChat)}
                  </a>
                ` : ''}
              </div>
            </div>
          `;
        }).join("");
      });
  }

  collabTabs.forEach(tab => {
    tab.addEventListener("click", function () {
      collabTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.getAttribute("data-filter") || "All";
      loadCollaborations(target);
    });
  });

  window.openCollabModal = function (collabId) {
    const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
    fetch("/api/collaborations")
      .then(r => r.json())
      .then(items => {
        const item = items.find(c => c.collab_id === collabId || c.id == collabId);
        if (!item) return;

        let modal = document.getElementById("collabModal");
        if (!modal) {
          modal = document.createElement("div");
          modal.id = "collabModal";
          modal.className = "modal-backdrop";
          document.body.appendChild(modal);
        }

        const isAuthor = window.CURRENT_USER && window.CURRENT_USER.user_id === item.author_id;
        const catDisplay = t("categories." + item.category, item.category);
        const tagDisplay = t("collab." + item.tag, item.tag || item.category);
        const locDisplay = window.i18n ? window.i18n.localizeLocation(item.location) : item.location;
        const timeDisplay = item.time_ago || t("common.recently", "Recently");

        modal.innerHTML = `
          <div class="modal-dialog">
            <div class="modal-header">
              <h3 class="modal-title">${escapeHtml(item.title)}</h3>
              <button class="modal-close-btn" onclick="document.getElementById('collabModal').classList.remove('active')">&times;</button>
            </div>
            <div class="modal-body">
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <div class="avatar-circle" style="width: 38px; height: 38px;">
                  <img src="${item.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(item.author_name)}">
                </div>
                <div>
                  <div style="font-weight: 600;">${escapeHtml(item.author_name)}</div>
                  <div style="font-size: 12px; color: var(--text-muted);">${escapeHtml(catDisplay)} • ${escapeHtml(locDisplay)} • ${escapeHtml(timeDisplay)}</div>
                </div>
              </div>
              <div style="margin-bottom: 14px;">
                <span class="badge badge-category">${escapeHtml(catDisplay)}</span>
                <span class="badge badge-tag">${escapeHtml(tagDisplay)}</span>
              </div>
              <p style="margin-bottom: 16px; font-size: 14px; line-height: 1.6; color: var(--text-main);">${escapeHtml(item.full_description)}</p>
              ${!isAuthor ? `
                <div class="form-group" style="margin-top: 18px;">
                  <label class="form-label">${escapeHtml(t("collab.send_proposal", "Send a Collaboration Proposal"))}</label>
                  <textarea id="proposalMessage" class="form-textarea" rows="3" placeholder="${escapeHtml(t("collab.proposal_placeholder", "Explain how your enterprise can partner or provide support..."))}"></textarea>
                </div>
              ` : `
                <div class="card" style="background: #f8fafc; padding: 12px; margin-top: 16px; font-size: 13px; color: var(--text-muted);">
                  ${escapeHtml(t("collab.authored_notice", "You authored this collaboration opportunity."))}
                </div>
              `}
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary btn-sm" onclick="document.getElementById('collabModal').classList.remove('active')">${escapeHtml(t("common.close", "Close"))}</button>
              ${!isAuthor ? `
                <button class="btn btn-primary btn-sm" onclick="window.sendProposal('${escapeHtml(item.collab_id)}', '${escapeHtml(item.author_id)}')">${escapeHtml(t("collab.submit_proposal", "Submit Proposal"))}</button>
              ` : ''}
            </div>
          </div>
        `;

        modal.classList.add("active");
      });
  };

  window.sendProposal = function (collabId, authorId) {
    const t = (k, fb) => window.i18n ? window.i18n.t(k, {}, fb !== undefined ? fb : k) : (fb !== undefined ? fb : k);
    if (!window.CURRENT_USER) {
      showToast(t("collab.login_submit_proposal", "Please log in to submit a proposal."));
      setTimeout(() => {
        window.location.href = "register.html?mode=login";
      }, 1000);
      return;
    }

    const msg = document.getElementById("proposalMessage") ? document.getElementById("proposalMessage").value.trim() : "";
    if (!msg) {
      showToast(t("collab.msg_required", "Please write a message for your proposal."));
      return;
    }

    fetch("/api/collaborations/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ collab_id: collabId, receiver_id: authorId, message: msg })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        const modal = document.getElementById("collabModal");
        if (modal) modal.classList.remove("active");
        showToast(t("collab.proposal_sent", "Collaboration proposal recorded and sent!"));
      } else {
        showToast(res.error || t("collab.proposal_failed", "Failed to send proposal."));
      }
    })
    .catch(() => showToast(t("common.network_error", "Network error.")));
  };

  window.refreshCollaborationsPage = function () {
    loadCollaborations(window.CURRENT_COLLAB_FILTER || "Seeking Partners");
  };

  loadCollaborations("Seeking Partners");
}

// -----------------------------------------------------------------------------
// Create Collaboration Form (Screen 7)
// -----------------------------------------------------------------------------
function initCreateCollabPage() {
  const form = document.getElementById("createCollabForm");
  if (!form) return;

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!window.CURRENT_USER) {
      showToast("Please log in to post a collaboration opportunity.");
      setTimeout(() => {
        window.location.href = "register.html?mode=login";
      }, 1000);
      return;
    }

    const title = document.getElementById("collabTitle").value.trim();
    const description = document.getElementById("collabDesc").value.trim();
    const category = document.getElementById("collabCategory").value;
    const location = document.getElementById("collabLocation").value;

    if (!title || !description || !category) {
      showToast("Please fill in the required fields (Title, Description, Category).");
      return;
    }

    fetch("/api/collaborations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, category, location, collab_type: "Seeking Partners" })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        showToast("Opportunity posted and stored in SQLite! Redirecting...");
        setTimeout(() => {
          window.location.href = "collaborations.html";
        }, 800);
      } else {
        showToast(res.error || "Failed to create collaboration.");
      }
    })
    .catch(() => showToast("Network error."));
  });
}

// -----------------------------------------------------------------------------
// Community Discussion Page (Screen 8)
// -----------------------------------------------------------------------------
function initDiscussionPage() {
  const commentInput = document.getElementById("discussionCommentInput");
  const postCommentBtn = document.getElementById("postCommentBtn");
  const threadContainer = document.getElementById("commentsThread");
  const commentsCountSpan = document.getElementById("discCommentsCount");

  if (!postCommentBtn || !commentInput || !threadContainer) return;

  const discId = new URLSearchParams(window.location.search).get("id") || "disc-1";

  // Load discussion thread dynamically from SQLite
  fetch(`/api/discussions/${encodeURIComponent(discId)}`)
    .then(r => r.json())
    .then(disc => {
      if (disc.error) return;

      const titleEl = document.querySelector(".discussion-question-title");
      if (titleEl && disc.title) titleEl.textContent = disc.title;

      const bodyEl = document.querySelector(".discussion-question-body");
      if (bodyEl && disc.body) bodyEl.textContent = disc.body;

      const authorEl = document.querySelector(".discussion-main-card .post-author-name");
      if (authorEl && disc.author_name) authorEl.textContent = disc.author_name;

      const avatarEl = document.querySelector(".discussion-main-card .avatar-circle img");
      if (avatarEl && disc.author_avatar) {
        avatarEl.src = disc.author_avatar;
        avatarEl.alt = disc.author_name || "Author";
      }

      const metaEl = document.querySelector(".discussion-main-card .post-meta");
      if (metaEl) {
        const cat = disc.author_category || "General";
        const loc = disc.author_location || "India";
        const timeAgo = disc.created_at ? new Date(disc.created_at).toLocaleDateString() : "Recently";
        metaEl.innerHTML = `<span>${escapeHtml(cat)}</span> • <span>${escapeHtml(loc)}</span> • <span>${escapeHtml(timeAgo)}</span>`;
      }

      const tagEl = document.querySelector(".discussion-main-card .badge");
      if (tagEl && disc.tag) tagEl.textContent = disc.tag;

      const likeBtn = document.querySelector(".discussion-main-card .btn-like");
      if (likeBtn && disc.likes !== undefined) {
        likeBtn.setAttribute("data-count", disc.likes);
        const span = likeBtn.querySelector("span");
        if (span) span.textContent = `${disc.likes} Likes`;
      }

      if (commentsCountSpan && disc.comments) {
        commentsCountSpan.textContent = `${disc.comments.length} Comments`;
      }
      if (disc.comments && disc.comments.length > 0) {
        threadContainer.innerHTML = disc.comments.map(c => `
          <div class="comment-item">
            <div class="avatar-circle" style="width: 36px; height: 36px;">
              <img src="${c.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(c.author_name)}">
            </div>
            <div class="comment-body-area">
              <div class="comment-header">
                <span class="comment-author">${escapeHtml(c.author_name)}</span>
                <span class="comment-time">${escapeHtml(c.time_ago || 'Recently')}</span>
              </div>
              <p class="comment-text">${escapeHtml(c.text)}</p>
            </div>
          </div>
        `).join("");
      }
    })
    .catch(async () => {
      let disc = null;
      if (window.UdyamAPI && window.supabaseClient) {
        try {
          disc = await window.UdyamAPI.getDiscussion(discId);
        } catch (_) {}
      }
      if (!disc && window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.discussions)) {
        disc = window.UDYAM_DATA.discussions.find(d => d.id === discId || d.disc_id === discId) || window.UDYAM_DATA.discussions[0];
      }
      if (disc) {
        const titleEl = document.querySelector(".discussion-question-title");
        if (titleEl && disc.title) titleEl.textContent = disc.title;
        const bodyEl = document.querySelector(".discussion-question-body");
        if (bodyEl && (disc.body || disc.content)) bodyEl.textContent = disc.body || disc.content;
        const authorEl = document.querySelector(".discussion-main-card .post-author-name");
        if (authorEl && (disc.author_name || disc.author)) authorEl.textContent = disc.author_name || disc.author;
        const avatarEl = document.querySelector(".discussion-main-card .avatar-circle img");
        if (avatarEl && (disc.author_avatar || disc.avatar)) avatarEl.src = disc.author_avatar || disc.avatar;
        const tagEl = document.querySelector(".discussion-main-card .badge");
        if (tagEl && disc.tag) tagEl.textContent = disc.tag;
        if (commentsCountSpan && disc.comments) {
          commentsCountSpan.textContent = `${disc.comments.length} Comments`;
        }
        if (disc.comments && disc.comments.length > 0) {
          threadContainer.innerHTML = disc.comments.map(c => `
            <div class="comment-item">
              <div class="avatar-circle" style="width: 36px; height: 36px;">
                <img src="${c.author_avatar || c.avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(c.author_name || c.author || 'Member')}">
              </div>
              <div class="comment-body-area">
                <div class="comment-header">
                  <span class="comment-author">${escapeHtml(c.author_name || c.author || 'Member')}</span>
                  <span class="comment-time">${escapeHtml(c.time_ago || c.time || 'Recently')}</span>
                </div>
                <p class="comment-text">${escapeHtml(c.text || c.comment || '')}</p>
              </div>
            </div>
          `).join("");
        }
      }
    });

  postCommentBtn.addEventListener("click", function () {
    if (!window.CURRENT_USER) {
      showToast("Please log in to join the community discussion.");
      setTimeout(() => {
        window.location.href = "register.html?mode=login";
      }, 1000);
      return;
    }

    const text = commentInput.value.trim();
    if (!text) {
      showToast("Please write a comment first.");
      return;
    }

    fetch(`/api/discussions/${encodeURIComponent(discId)}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success && res.comment) {
        const c = res.comment;
        const commentItem = document.createElement("div");
        commentItem.className = "comment-item";
        commentItem.innerHTML = `
          <div class="avatar-circle" style="width: 36px; height: 36px;">
            <img src="${c.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(c.author_name)}">
          </div>
          <div class="comment-body-area">
            <div class="comment-header">
              <span class="comment-author">${escapeHtml(c.author_name)}</span>
              <span class="comment-time">${escapeHtml(c.time_ago || 'Just now')}</span>
            </div>
            <p class="comment-text">${escapeHtml(c.text)}</p>
          </div>
        `;

        threadContainer.appendChild(commentItem);
        commentInput.value = "";

        if (commentsCountSpan) {
          let count = parseInt(commentsCountSpan.textContent) || 0;
          commentsCountSpan.textContent = `${count + 1} Comments`;
        }

        showToast("Comment saved to SQLite database!");
      } else {
        showToast(res.error || "Failed to post comment.");
      }
    })
    .catch(() => showToast("Network error."));
  });
}

// -----------------------------------------------------------------------------
// Learn & Share Page (Screen 9)
// -----------------------------------------------------------------------------
function initLearnPage() {
  const pills = document.querySelectorAll(".learn-pill-btn");
  const articlesContainer = document.getElementById("articlesGrid");
  if (!articlesContainer) return;

  function loadArticles(category = "All") {
    window.CURRENT_LEARN_CAT = category;
    fetch(`/api/articles?category=${category}`)
      .then(res => res.json())
      .then(items => {
        if (!items || items.length === 0) return;
        articlesContainer.innerHTML = items.map(a => {
          const catDisplay = window.i18n ? window.i18n.t("categories." + a.author_category, {}, a.author_category) : a.author_category;
          return `
          <div class="article-card" onclick="window.readArticle('${a.article_id}')">
            <div class="article-thumb">
              <img src="${a.image}" alt="${escapeHtml(a.title)}">
            </div>
            <div class="article-body">
              <h2 class="article-title">${escapeHtml(a.title)}</h2>
              <div class="article-author-row">
                <div class="avatar-circle" style="width: 32px; height: 32px;">
                  <img src="${a.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(a.author_name)}">
                </div>
                <div class="article-author-meta">
                  <span class="article-author-name">${escapeHtml(a.author_name)}</span>
                  <div class="article-date-row">
                    <span>${escapeHtml(catDisplay)}</span> • <span>${escapeHtml(a.date_str)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
        }).join("");
      })
      .catch(async () => {
        let fallbackArticles = [];
        if (window.UdyamAPI && window.supabaseClient) {
          try {
            fallbackArticles = await window.UdyamAPI.getArticles(category === "All" ? "all" : category);
          } catch (_) {}
        }
        if (fallbackArticles.length === 0 && window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.articles)) {
          fallbackArticles = window.UDYAM_DATA.articles.map(a => ({
            article_id: a.id,
            title: a.title,
            category: a.category,
            author_id: a.authorId || "asha-devi",
            author_name: a.author || "Asha Devi",
            author_avatar: a.avatar || "assets/images/artisan_asha.jpg",
            author_category: a.category,
            date_str: a.date || "March 2026",
            image: a.image || "assets/images/crafts_banner.jpg",
            summary: a.summary,
            lessons: a.lessons || []
          }));
        }
        if (category !== "All" && category !== "all") {
          fallbackArticles = fallbackArticles.filter(a => a.category && a.category.toLowerCase() === category.toLowerCase());
        }
        if (fallbackArticles.length > 0) {
          renderArticleCards(fallbackArticles);
        }
      });
  }

  function renderArticleCards(items) {
    articlesContainer.innerHTML = items.map(a => {
      const catDisplay = window.i18n ? window.i18n.t("categories." + a.author_category, {}, a.author_category) : a.author_category;
      return `
      <div class="article-card" onclick="window.readArticle('${a.article_id}')">
        <div class="article-thumb">
          <img src="${a.image}" alt="${escapeHtml(a.title)}">
        </div>
        <div class="article-body">
          <h2 class="article-title">${escapeHtml(a.title)}</h2>
          <div class="article-author-row">
            <div class="avatar-circle" style="width: 32px; height: 32px;">
              <img src="${a.author_avatar || 'assets/images/digital_rahul.jpg'}" alt="${escapeHtml(a.author_name)}">
            </div>
            <div class="article-author-meta">
              <span class="article-author-name">${escapeHtml(a.author_name)}</span>
              <div class="article-date-row">
                <span>${escapeHtml(catDisplay)}</span> • <span>${escapeHtml(a.date_str)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    }).join("");
  }

  pills.forEach(pill => {
    pill.addEventListener("click", function () {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const cat = pill.getAttribute("data-category") || "All";
      loadArticles(cat);
    });
  });

  window.readArticle = function (id) {
    fetch("/api/articles")
      .then(r => r.json())
      .then(articles => {
        const art = articles.find(a => a.article_id === id);
        if (!art) return;

        let modal = document.getElementById("articleModal");
        if (!modal) {
          modal = document.createElement("div");
          modal.id = "articleModal";
          modal.className = "modal-backdrop";
          document.body.appendChild(modal);
        }

        const lessons = Array.isArray(art.lessons) ? art.lessons : [];
        const catDisplay = window.i18n ? window.i18n.t("categories." + art.author_category, {}, art.author_category) : art.author_category;
        const tLessons = window.i18n ? window.i18n.t("learn.key_lessons", {}, "Key Lessons for Rural Founders:") : "Key Lessons for Rural Founders:";
        const tClose = window.i18n ? window.i18n.t("common.close", {}, "Close") : "Close";
        const tSaveGuide = window.i18n ? window.i18n.t("learn.save_guide", {}, "Save Guide") : "Save Guide";
        const tSavedToast = window.i18n ? window.i18n.t("learn.saved_bookmark", {}, "Article saved to your bookmarks!") : "Article saved to your bookmarks!";

        modal.innerHTML = `
          <div class="modal-dialog" style="max-width: 600px;">
            <div class="modal-header">
              <h3 class="modal-title">${escapeHtml(art.title)}</h3>
              <button class="modal-close-btn" onclick="document.getElementById('articleModal').classList.remove('active')">&times;</button>
            </div>
            <div class="modal-body">
              <div style="border-radius: 8px; overflow: hidden; margin-bottom: 16px; max-height: 240px;">
                <img src="${art.image}" alt="${escapeHtml(art.title)}" style="width: 100%; height: 240px; object-fit: cover;">
              </div>
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <div class="avatar-circle" style="width: 36px; height: 36px;">
                  <img src="${art.author_avatar}" alt="${escapeHtml(art.author_name)}">
                </div>
                <div>
                  <div style="font-weight: 600;">${escapeHtml(art.author_name)} (${escapeHtml(catDisplay)})</div>
                  <div style="font-size: 11.5px; color: var(--text-muted);">${escapeHtml(art.date_str)}</div>
                </div>
              </div>
              <p style="font-size: 14.5px; line-height: 1.6; color: var(--text-main); margin-bottom: 16px;">
                ${escapeHtml(art.summary)}
              </p>
              ${lessons.length > 0 ? `
                <div class="card" style="background: var(--bg-cream); border: 1px solid var(--bg-cream-border); padding: 14px;">
                  <h4 style="font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--primary-dark);">${escapeHtml(tLessons)}</h4>
                  <ul style="font-size: 12.5px; padding-left: 18px; color: var(--text-main); line-height: 1.5;">
                    ${lessons.map(l => `<li>${escapeHtml(l)}</li>`).join("")}
                  </ul>
                </div>
              ` : ''}
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary btn-sm" onclick="document.getElementById('articleModal').classList.remove('active')">${escapeHtml(tClose)}</button>
              <button class="btn btn-primary btn-sm" onclick="showToast('${escapeHtml(tSavedToast)}'); document.getElementById('articleModal').classList.remove('active');">${escapeHtml(tSaveGuide)}</button>
            </div>
          </div>
        `;

        modal.classList.add("active");
      })
      .catch(async () => {
        let art = null;
        if (window.UdyamAPI && window.supabaseClient) {
          try {
            const articles = await window.UdyamAPI.getArticles("all");
            art = articles.find(a => a.article_id === id);
          } catch (_) {}
        }
        if (!art && window.UDYAM_DATA && Array.isArray(window.UDYAM_DATA.articles)) {
          art = window.UDYAM_DATA.articles.find(a => a.id === id);
        }
        if (!art) return;

        let modal = document.getElementById("articleModal");
        if (!modal) {
          modal = document.createElement("div");
          modal.id = "articleModal";
          modal.className = "modal-backdrop";
          document.body.appendChild(modal);
        }
        const lessons = Array.isArray(art.lessons) ? art.lessons : [];
        const catDisplay = window.i18n ? window.i18n.t("categories." + (art.category || art.author_category), {}, art.category) : (art.category || "General");
        const tLessons = window.i18n ? window.i18n.t("learn.key_lessons", {}, "Key Lessons for Rural Founders:") : "Key Lessons for Rural Founders:";
        const tClose = window.i18n ? window.i18n.t("common.close", {}, "Close") : "Close";
        const tSaveGuide = window.i18n ? window.i18n.t("learn.save_guide", {}, "Save Guide") : "Save Guide";
        const tSavedToast = window.i18n ? window.i18n.t("learn.saved_bookmark", {}, "Article saved to your bookmarks!") : "Article saved to your bookmarks!";

        modal.innerHTML = `
          <div class="modal-dialog" style="max-width: 600px;">
            <div class="modal-header">
              <h3 class="modal-title">${escapeHtml(art.title)}</h3>
              <button class="modal-close-btn" onclick="document.getElementById('articleModal').classList.remove('active')">&times;</button>
            </div>
            <div class="modal-body">
              <div style="border-radius: 8px; overflow: hidden; margin-bottom: 16px; max-height: 240px;">
                <img src="${art.image}" alt="${escapeHtml(art.title)}" style="width: 100%; height: 240px; object-fit: cover;">
              </div>
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <div class="avatar-circle" style="width: 36px; height: 36px;">
                  <img src="${art.author_avatar || art.avatar || 'assets/images/artisan_asha.jpg'}" alt="${escapeHtml(art.author_name || art.author || 'Author')}">
                </div>
                <div>
                  <div style="font-weight: 600;">${escapeHtml(art.author_name || art.author || 'Author')} (${escapeHtml(catDisplay)})</div>
                  <div style="font-size: 11.5px; color: var(--text-muted);">${escapeHtml(art.date_str || art.date || 'March 2026')}</div>
                </div>
              </div>
              <p style="font-size: 14.5px; line-height: 1.6; color: var(--text-main); margin-bottom: 16px;">
                ${escapeHtml(art.summary)}
              </p>
              ${lessons.length > 0 ? `
                <div class="card" style="background: var(--bg-cream); border: 1px solid var(--bg-cream-border); padding: 14px;">
                  <h4 style="font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--primary-dark);">${escapeHtml(tLessons)}</h4>
                  <ul style="font-size: 12.5px; padding-left: 18px; color: var(--text-main); line-height: 1.5;">
                    ${lessons.map(l => `<li>${escapeHtml(l)}</li>`).join("")}
                  </ul>
                </div>
              ` : ''}
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary btn-sm" onclick="document.getElementById('articleModal').classList.remove('active')">${escapeHtml(tClose)}</button>
              <button class="btn btn-primary btn-sm" onclick="showToast('${escapeHtml(tSavedToast)}'); document.getElementById('articleModal').classList.remove('active');">${escapeHtml(tSaveGuide)}</button>
            </div>
          </div>
        `;
        modal.classList.add("active");
      });
  };

  window.refreshLearnPage = function () {
    loadArticles(window.CURRENT_LEARN_CAT || "All");
  };

  loadArticles("All");
}

// -----------------------------------------------------------------------------
// Register & Auth Page (Screen 2)
// -----------------------------------------------------------------------------
function initAuthPage() {
  const authForm = document.getElementById("authForm");
  const authModeToggle = document.getElementById("authModeToggle");
  const authTitle = document.getElementById("authTitle");
  const authSubtitle = document.getElementById("authSubtitle");
  const authSubmitBtn = document.getElementById("authSubmitBtn");
  const authTogglePrompt = document.getElementById("authTogglePrompt");
  const authAlert = document.getElementById("authAlert");

  if (!authForm || !authModeToggle) return;

  const urlParams = new URLSearchParams(window.location.search);
  let isRegisterMode = urlParams.get("mode") !== "login";

  // Account type cards
  const cardEnt = document.getElementById("cardEntrepreneur");
  const cardComm = document.getElementById("cardCommunity");
  if (cardEnt && cardComm) {
    cardEnt.addEventListener("click", () => {
      cardEnt.classList.add("selected");
      cardComm.classList.remove("selected");
      const r = cardEnt.querySelector('input[type="radio"]');
      if (r) r.checked = true;
    });
    cardComm.addEventListener("click", () => {
      cardComm.classList.add("selected");
      cardEnt.classList.remove("selected");
      const r = cardComm.querySelector('input[type="radio"]');
      if (r) r.checked = true;
    });
  }

  // Password strength meter
  const regPass = document.getElementById("regPassword");
  const passWrap = document.getElementById("passwordStrengthWrap");
  const b1 = document.getElementById("bar1");
  const b2 = document.getElementById("bar2");
  const b3 = document.getElementById("bar3");
  const b4 = document.getElementById("bar4");
  const strengthText = document.getElementById("strengthText");

  if (regPass) {
    regPass.addEventListener("input", function () {
      if (!isRegisterMode) {
        if (passWrap) passWrap.style.display = "none";
        return;
      }
      if (passWrap) passWrap.style.display = "block";
      const val = regPass.value;
      let score = 0;
      if (val.length >= 8) score++;
      if (/[a-zA-Z]/.test(val) && /[0-9]/.test(val)) score++;
      if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
      if (/[^a-zA-Z0-9]/.test(val) || val.length >= 12) score++;

      [b1, b2, b3, b4].forEach(b => { if (b) b.style.background = "var(--border-color)"; });

      if (val.length === 0) {
        if (strengthText) strengthText.textContent = window.i18n ? window.i18n.t("auth.pass_min_length", {}, "Must be at least 8 characters long") : "Must be at least 8 characters long";
      } else if (val.length < 8) {
        if (b1) b1.style.background = "#ef4444";
        if (strengthText) strengthText.textContent = window.i18n ? window.i18n.t("auth.pass_weak", {}, "Weak: At least 8 characters required") : "Weak: At least 8 characters required";
      } else if (score <= 2) {
        if (b1) b1.style.background = "#f59e0b";
        if (b2) b2.style.background = "#f59e0b";
        if (strengthText) strengthText.textContent = window.i18n ? window.i18n.t("auth.pass_fair", {}, "Fair: Add numbers and mixed case") : "Fair: Add numbers and mixed case";
      } else if (score === 3) {
        if (b1) b1.style.background = "#18639c";
        if (b2) b2.style.background = "#18639c";
        if (b3) b3.style.background = "#18639c";
        if (strengthText) strengthText.textContent = window.i18n ? window.i18n.t("auth.pass_good", {}, "Good password") : "Good password";
      } else {
        [b1, b2, b3, b4].forEach(b => { if (b) b.style.background = "#22c55e"; });
        if (strengthText) strengthText.textContent = window.i18n ? window.i18n.t("auth.pass_strong", {}, "Strong password ✓") : "Strong password ✓";
      }
    });
  }

  // Password confirmation real-time validator
  const regConfirm = document.getElementById("regConfirmPassword");
  const confirmFeedback = document.getElementById("confirmFeedback");
  if (regConfirm && confirmFeedback) {
    regConfirm.addEventListener("input", function () {
      if (!regConfirm.value) {
        confirmFeedback.style.display = "none";
      } else if (regConfirm.value === regPass.value) {
        confirmFeedback.className = "password-feedback success";
        confirmFeedback.textContent = window.i18n ? window.i18n.t("auth.pass_match", {}, "Passwords match ✓") : "Passwords match ✓";
      } else {
        confirmFeedback.className = "password-feedback error";
        confirmFeedback.textContent = window.i18n ? window.i18n.t("auth.pass_mismatch", {}, "Passwords do not match") : "Passwords do not match";
      }
    });
  }

  // Render registration language selector
  const regLangContainer = document.getElementById("regLanguageSelectorContainer");
  if (regLangContainer && window.i18n) {
    regLangContainer.innerHTML = window.i18n.renderLanguageSelectorHTML("regLangSelector");
    window.i18n.bindLanguageSelectors();
  }

  function setMode(registerMode) {
    isRegisterMode = registerMode;
    const registerFields = document.querySelectorAll(".register-only-field");

    if (authAlert) authAlert.style.display = "none";

    if (isRegisterMode) {
      if (authTitle) authTitle.textContent = window.i18n ? window.i18n.t("auth.create_account") : "Create Your Account";
      if (authSubtitle) authSubtitle.textContent = window.i18n ? window.i18n.t("auth.register_subtitle") : "Join a growing community of rural entrepreneurs and supporters";
      if (authSubmitBtn) authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.register_btn") : "Sign Up";
      if (authTogglePrompt) authTogglePrompt.textContent = (window.i18n ? window.i18n.t("auth.have_account") : "Already have an account?") + " ";
      authModeToggle.textContent = window.i18n ? window.i18n.t("auth.sign_in_link") : "Login";
      registerFields.forEach(f => f.style.display = "block");
      if (passWrap && regPass && regPass.value) passWrap.style.display = "block";
    } else {
      if (authTitle) authTitle.textContent = window.i18n ? window.i18n.t("auth.welcome_back") : "Welcome Back";
      if (authSubtitle) authSubtitle.textContent = window.i18n ? window.i18n.t("auth.login_subtitle") : "Login to connect with your rural enterprise network";
      if (authSubmitBtn) authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.login_btn") : "Login";
      if (authTogglePrompt) authTogglePrompt.textContent = (window.i18n ? window.i18n.t("auth.no_account") : "Don't have an account?") + " ";
      authModeToggle.textContent = window.i18n ? window.i18n.t("auth.sign_up_link") : "Sign Up";
      registerFields.forEach(f => f.style.display = "none");
    }
  }

  setMode(isRegisterMode);

  window.addEventListener("i18n:languageChanged", () => {
    setMode(isRegisterMode);
  });

  authModeToggle.addEventListener("click", function (e) {
    e.preventDefault();
    setMode(!isRegisterMode);
  });

  authForm.addEventListener("submit", function (e) {
    e.preventDefault();
    if (authAlert) authAlert.style.display = "none";

    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;

    if (isRegisterMode) {
      const name = document.getElementById("regFullName") ? document.getElementById("regFullName").value.trim() : "";
      const confirmPass = document.getElementById("regConfirmPassword") ? document.getElementById("regConfirmPassword").value : "";
      const selectedRadio = document.querySelector('input[name="account_type"]:checked');
      const accountType = selectedRadio ? selectedRadio.value : "entrepreneur";
      const preferredLang = window.i18n ? window.i18n.currentLanguage : "en";

      if (!name || name.length < 2) {
        showAuthError(window.i18n ? window.i18n.t("auth.err_name", {}, "Please provide a valid full name (at least 2 characters).") : "Please provide a valid full name (at least 2 characters).");
        return;
      }
      if (password.length < 8) {
        showAuthError(window.i18n ? window.i18n.t("auth.err_password_min", {}, "Password must be at least 8 characters long.") : "Password must be at least 8 characters long.");
        return;
      }
      if (confirmPass && password !== confirmPass) {
        showAuthError(window.i18n ? window.i18n.t("auth.passwords_dont_match", {}, "Passwords do not match.") : "Passwords do not match.");
        return;
      }

      authSubmitBtn.disabled = true;
      authSubmitBtn.textContent = window.i18n ? window.i18n.t("common.loading") : "Creating Account...";

      const performFlaskRegister = () => {
        fetch("/api/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            email: email,
            password: password,
            confirm_password: confirmPass,
            account_type: accountType,
            preferred_language: preferredLang
          })
        })
        .then(async r => {
          const res = await r.json();
          authSubmitBtn.disabled = false;
          authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.register_btn", {}, "Sign Up") : "Sign Up";

          if (r.ok && res.success) {
            window.CURRENT_USER = res.user;
            initAuthSession();

            if (accountType === "entrepreneur") {
              showToast(window.i18n ? window.i18n.t("auth.msg_registered_setup", {}, "Account registered! Opening business profile setup...") : "Account registered! Opening business profile setup...");
              setTimeout(() => {
                window.location.href = "profile-setup.html";
              }, 700);
            } else {
              showToast(window.i18n ? window.i18n.t("auth.msg_welcome", {}, "Welcome to ThriveHub! Entering platform...") : "Welcome to ThriveHub! Entering platform...");
              setTimeout(() => {
                window.location.href = "dashboard.html";
              }, 700);
            }
          } else {
            showAuthError(res.error || (window.i18n ? window.i18n.t("auth.err_registration_failed", {}, "Registration failed.") : "Registration failed."));
          }
        })
        .catch(() => {
          authSubmitBtn.disabled = false;
          authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.register_btn", {}, "Sign Up") : "Sign Up";
          showAuthError(window.i18n ? window.i18n.t("common.network_error", {}, "Network error. Please try again.") : "Network error. Please try again.");
        });
      };

      if (window.UdyamAuth && window.supabaseClient) {
        window.UdyamAuth.signUp(email, password, {
          name: name,
          account_type: accountType,
          preferred_language: preferredLang
        })
        .then(async res => {
          authSubmitBtn.disabled = false;
          authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.register_btn", {}, "Sign Up") : "Sign Up";

          if (res.user) {
            // Check if confirmation email was sent
            if (!res.session && res.user.identities && res.user.identities.length > 0) {
              showToast("Registration successful! Please check your email to confirm your account.");
              showAuthError("Account created! A confirmation email has been sent. Please verify your email before logging in.");
              return;
            }

            window.CURRENT_USER = await window.UdyamAuth.getProfile(res.user.id) || {
              id: res.user.id,
              name: name,
              email: email,
              account_type: accountType
            };
            updateGlobalNavigation(window.CURRENT_USER);

            if (accountType === "entrepreneur") {
              showToast("Account registered! Opening business profile setup...");
              setTimeout(() => { window.location.href = "profile-setup.html"; }, 700);
            } else {
              showToast("Welcome to ThriveHub!");
              setTimeout(() => { window.location.href = "dashboard.html"; }, 700);
            }
          } else {
            performFlaskRegister();
          }
        })
        .catch(err => {
          console.warn("Supabase signup error, attempting fallback:", err);
          performFlaskRegister();
        });
      } else {
        performFlaskRegister();
      }

    } else {
      // Login mode
      authSubmitBtn.disabled = true;
      authSubmitBtn.textContent = window.i18n ? window.i18n.t("common.loading") : "Logging in...";

      const performFlaskLogin = () => {
        fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email, password: password })
        })
        .then(async r => {
          const res = await r.json();
          authSubmitBtn.disabled = false;
          authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.login_btn", {}, "Login") : "Login";

          if (r.ok && res.success) {
            window.CURRENT_USER = res.user;
            initAuthSession();
            showToast(window.i18n ? window.i18n.t("auth.login_success", {}, `Welcome back, ${res.user.name}!`) : `Welcome back, ${res.user.name}!`);
            setTimeout(() => {
              window.location.href = "dashboard.html";
            }, 700);
          } else {
            showAuthError(res.error || (window.i18n ? window.i18n.t("auth.err_invalid_credentials", {}, "Invalid email or password.") : "Invalid email or password."));
          }
        })
        .catch(() => {
          authSubmitBtn.disabled = false;
          authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.login_btn", {}, "Login") : "Login";
          showAuthError(window.i18n ? window.i18n.t("common.network_error", {}, "Network error. Please try again.") : "Network error. Please try again.");
        });
      };

      if (window.UdyamAuth && window.supabaseClient) {
        window.UdyamAuth.signIn(email, password)
        .then(async res => {
          authSubmitBtn.disabled = false;
          authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.login_btn", {}, "Login") : "Login";

          if (res.user) {
            window.CURRENT_USER = await window.UdyamAuth.getProfile(res.user.id) || {
              id: res.user.id,
              name: res.user.user_metadata?.name || res.user.email.split("@")[0],
              email: res.user.email,
              account_type: res.user.user_metadata?.account_type || "entrepreneur"
            };
            updateGlobalNavigation(window.CURRENT_USER);
            showToast(`Welcome back, ${window.CURRENT_USER.name}!`);
            setTimeout(() => { window.location.href = "dashboard.html"; }, 700);
          } else {
            performFlaskLogin();
          }
        })
        .catch(err => {
          const msg = (err && err.message) ? err.message.toLowerCase() : "";
          if (msg.includes("email not confirmed")) {
            authSubmitBtn.disabled = false;
            authSubmitBtn.textContent = window.i18n ? window.i18n.t("auth.login_btn", {}, "Login") : "Login";
            showAuthError("Please verify your email address before logging in, or check your spam/inbox for the verification link.");
            return;
          }
          console.warn("Supabase signin failed, trying fallback:", err);
          performFlaskLogin();
        });
      } else {
        performFlaskLogin();
      }
    }
  });

  function showAuthError(msg) {
    if (authAlert) {
      authAlert.textContent = msg;
      authAlert.style.display = "block";
    } else {
      showToast(msg);
    }
  }
}

// -----------------------------------------------------------------------------
// Messages Page: Database-Backed Real-Time Chat (Phase 2)
// -----------------------------------------------------------------------------
function initMessagesPage() {
  const layout = document.getElementById("messagesLayout");
  if (!layout) return;

  const convsContainer = document.getElementById("conversationsListContainer");
  const searchInput = document.getElementById("convSearchInput");
  const filterBtns = document.querySelectorAll(".conv-filter-btn");

  const emptyState = document.getElementById("chatEmptyState");
  const activeState = document.getElementById("chatActiveState");

  const chatAvatar = document.getElementById("chatHeaderAvatar");
  const chatName = document.getElementById("chatHeaderName");
  const chatBadge = document.getElementById("chatHeaderBadge");
  const chatSub = document.getElementById("chatHeaderSub");
  const chatContextBtn = document.getElementById("chatViewContextBtn");

  const optionsBtn = document.getElementById("chatOptionsBtn");
  const optionsMenu = document.getElementById("chatOptionsMenu");
  const btnBlockUnblock = document.getElementById("btnBlockUnblock");

  const stream = document.getElementById("chatMessagesStream");
  const composer = document.getElementById("chatComposer");
  const chatInput = document.getElementById("chatInput");
  const btnSend = document.getElementById("btnSendMessage");
  const charCounter = document.getElementById("charCounter");

  const blockedBanner = document.getElementById("chatBlockedBanner");
  const blockedText = document.getElementById("chatBlockedText");
  const btnUnblockInBanner = document.getElementById("btnUnblockInBanner");
  const mobileBackBtn = document.getElementById("mobileChatBackBtn");
  const totalUnreadBadge = document.getElementById("sidebarTotalUnreadBadge");

  let conversations = [];
  let activeConv = null;
  let activeFilter = "all";
  let knownMsgIds = new Set();
  let pollInterval = null;
  let listPollInterval = null;

  if (!window.CURRENT_USER) {
    const tLoginReq = window.i18n ? window.i18n.t("msg.login_required", {}, "Please log in to access your direct and project messages.") : "Please log in to access your direct and project messages.";
    const tLogIn = window.i18n ? window.i18n.t("nav.login", {}, "Log In") : "Log In";
    convsContainer.innerHTML = `
      <div style="padding: 40px 20px; text-align: center; color: var(--text-muted);">
        <p style="font-size: 14px; margin-bottom: 12px;">${escapeHtml(tLoginReq)}</p>
        <a href="register.html?mode=login" class="btn btn-primary btn-sm">${escapeHtml(tLogIn)}</a>
      </div>
    `;
    return;
  }

  // Filter Buttons
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.dataset.filter;
      renderConversationsList();
    });
  });

  // Search Input
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderConversationsList();
    });
  }

  // Mobile Back Button
  if (mobileBackBtn) {
    mobileBackBtn.addEventListener("click", () => {
      layout.classList.remove("chat-active");
    });
  }

  // Options Menu Toggle
  if (optionsBtn && optionsMenu) {
    optionsBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      optionsMenu.style.display = optionsMenu.style.display === "block" ? "none" : "block";
    });
    document.addEventListener("click", () => {
      optionsMenu.style.display = "none";
    });
  }

  // Textarea auto-resize and character counter
  if (chatInput) {
    chatInput.addEventListener("input", () => {
      const len = chatInput.value.length;
      if (charCounter) {
        charCounter.textContent = `${len} / 2000`;
        charCounter.style.color = len > 1900 ? "#dc2626" : "var(--text-subtle)";
      }
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    });

    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  if (btnSend) {
    btnSend.addEventListener("click", sendMessage);
  }

  function formatMsgTime(isoStr) {
    if (!isoStr) return "";
    try {
      const d = new Date(isoStr.replace(" ", "T") + (isoStr.includes("Z") ? "" : "Z"));
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return isoStr;
    }
  }

  function formatRelativeDate(isoStr) {
    if (!isoStr) return "";
    try {
      const d = new Date(isoStr.replace(" ", "T") + (isoStr.includes("Z") ? "" : "Z"));
      const now = new Date();
      if (d.toDateString() === now.toDateString()) {
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      }
      return d.toLocaleDateString([], { month: "short", day: "numeric" });
    } catch {
      return "";
    }
  }

  function loadConversations(selectTargetConvId = null) {
    return fetch("/api/conversations")
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          conversations = data.conversations || [];
          renderConversationsList();

          const totalUnread = conversations.reduce((acc, c) => acc + (c.unread_count || 0), 0);
          if (totalUnreadBadge) {
            if (totalUnread > 0) {
              totalUnreadBadge.textContent = totalUnread;
              totalUnreadBadge.style.display = "inline-block";
            } else {
              totalUnreadBadge.style.display = "none";
            }
          }

          if (selectTargetConvId) {
            const target = conversations.find(c => c.conv_id === selectTargetConvId);
            if (target) {
              openConversation(target);
            }
          } else if (!activeConv && conversations.length > 0 && window.innerWidth > 768) {
            openConversation(conversations[0]);
          }
        }
      })
      .catch(() => {});
  }

  function renderConversationsList() {
    const query = (searchInput ? searchInput.value : "").trim().toLowerCase();
    let filtered = conversations.filter(c => {
      if (activeFilter === "direct" && c.conv_type !== "direct") return false;
      if (activeFilter === "collaboration" && c.conv_type !== "collaboration") return false;

      if (!query) return true;
      const title = (c.conv_type === "direct" ? (c.other_participant ? c.other_participant.name : "") : c.title).toLowerCase();
      const snippet = (c.last_message ? c.last_message.body : "").toLowerCase();
      const biz = (c.other_participant && c.other_participant.business_name ? c.other_participant.business_name : "").toLowerCase();
      return title.includes(query) || snippet.includes(query) || biz.includes(query);
    });

    if (filtered.length === 0) {
      const tNoConvs = window.i18n ? window.i18n.t("msg.no_conversations", {}, "No conversations found.") : "No conversations found.";
      const tFindPartners = window.i18n ? window.i18n.t("msg.find_partners", {}, "Find Partners") : "Find Partners";
      convsContainer.innerHTML = `
        <div style="padding: 40px 20px; text-align: center; color: var(--text-muted); font-size: 13px;">
          <p>${escapeHtml(tNoConvs)}</p>
          <a href="directory.html" class="btn btn-outline btn-sm" style="margin-top: 10px;">${escapeHtml(tFindPartners)}</a>
        </div>
      `;
      return;
    }

    convsContainer.innerHTML = filtered.map(c => {
      const isDirect = c.conv_type === "direct";
      const other = c.other_participant || {};
      const name = isDirect ? (other.name || "Entrepreneur") : (c.title || (window.i18n ? window.i18n.t("msg.project", {}, "Collaboration Project") : "Collaboration Project"));
      let sub = "";
      if (isDirect) {
        if (other.business_name) {
          sub = other.business_name;
        } else if (other.account_type === "community_member") {
          sub = window.i18n ? window.i18n.t("auth.community_member", {}, "Community Member") : "Community Member";
        } else if (other.category) {
          sub = window.i18n ? window.i18n.t("categories." + other.category, {}, other.category) : other.category;
        } else {
          sub = window.i18n ? window.i18n.t("auth.entrepreneur", {}, "Rural Enterprise") : "Rural Enterprise";
        }
      } else {
        sub = window.i18n ? window.i18n.t("msg.joint_collab_project", {}, "Joint Collaboration Project") : "Joint Project Collaboration";
      }
      const avatar = isDirect ? (other.avatar || "") : "";
      const initials = getInitials(name);
      const isActive = activeConv && activeConv.conv_id === c.conv_id;
      const unread = c.unread_count || 0;
      const timeStr = c.last_message ? formatRelativeDate(c.last_message.created_at) : "";
      const noMessagesText = window.i18n ? window.i18n.t("msg.no_messages", {}, "No messages yet") : "No messages yet";
      const snippet = c.last_message ? (c.last_message.message_type === 'system' ? `⚙️ ${c.last_message.body}` : c.last_message.body) : noMessagesText;

      return `
        <div class="conversation-item ${isActive ? 'active' : ''}" data-conv-id="${escapeHtml(c.conv_id)}">
          <div class="conv-avatar-circle">
            ${avatar ? `<img src="${avatar}" alt="${escapeHtml(name)}">` : `<span>${escapeHtml(initials)}</span>`}
          </div>
          <div class="conv-item-content">
            <div class="conv-item-top">
              <span class="conv-item-name">${escapeHtml(name)}</span>
              <span class="conv-item-time">${escapeHtml(timeStr)}</span>
            </div>
            <div class="conv-item-sub">${escapeHtml(sub)}</div>
            <div class="conv-item-bottom">
              <span class="conv-item-snippet">${escapeHtml(snippet)}</span>
              ${unread > 0 ? `<span class="conv-item-badge">${unread}</span>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join("");

    convsContainer.querySelectorAll(".conversation-item").forEach(item => {
      item.addEventListener("click", () => {
        const convId = item.dataset.convId;
        const conv = conversations.find(c => c.conv_id === convId);
        if (conv) openConversation(conv);
      });
    });
  }

  function openConversation(conv) {
    activeConv = conv;
    knownMsgIds.clear();

    convsContainer.querySelectorAll(".conversation-item").forEach(el => {
      el.classList.toggle("active", el.dataset.convId === conv.conv_id);
    });

    conv.unread_count = 0;
    const badgeEl = convsContainer.querySelector(`[data-conv-id="${conv.conv_id}"] .conv-item-badge`);
    if (badgeEl) badgeEl.remove();

    layout.classList.add("chat-active");
    emptyState.style.display = "none";
    activeState.style.display = "flex";

    const isDirect = conv.conv_type === "direct";
    const other = conv.other_participant || {};
    const name = isDirect ? (other.name || "Member") : (conv.title || (window.i18n ? window.i18n.t("msg.project", {}, "Joint Project") : "Joint Project"));
    let sub = "";
    if (isDirect) {
      if (other.business_name) {
        const locPart = other.location ? (window.i18n ? window.i18n.localizeLocation(other.location) : other.location) : "India";
        sub = `${other.business_name} • ${locPart}`;
      } else if (other.account_type === "community_member") {
        sub = window.i18n ? window.i18n.t("auth.community_member", {}, "Community Member") : "Community Member";
      } else if (other.category) {
        sub = window.i18n ? window.i18n.t("categories." + other.category, {}, other.category) : other.category;
      } else {
        sub = window.i18n ? window.i18n.t("auth.entrepreneur", {}, "Rural Enterprise") : "Rural Enterprise";
      }
    } else {
      sub = window.i18n ? window.i18n.t("msg.joint_collab_project", {}, "Joint Collaboration Project") : "Joint Collaboration Project";
    }

    chatName.textContent = name;
    chatBadge.textContent = isDirect
      ? (window.i18n ? window.i18n.t("msg.direct", {}, "Direct") : "Direct")
      : (window.i18n ? window.i18n.t("msg.project", {}, "Project") : "Project");
    chatBadge.className = isDirect ? "badge badge-tag" : "badge badge-category";
    chatSub.textContent = sub;

    const initials = getInitials(name);
    if (isDirect && other.avatar) {
      chatAvatar.innerHTML = `<img src="${other.avatar}" alt="${escapeHtml(name)}">`;
    } else {
      chatAvatar.innerHTML = `<span>${escapeHtml(initials)}</span>`;
    }

    if (isDirect && other.user_id) {
      chatContextBtn.textContent = window.i18n ? window.i18n.t("profile.view_profile", {}, "View Profile") : "View Profile";
      chatContextBtn.href = `profile.html?id=${encodeURIComponent(other.user_id)}`;
      chatContextBtn.style.display = "inline-flex";
    } else if (!isDirect && conv.project_id) {
      chatContextBtn.textContent = window.i18n ? window.i18n.t("collab.joint_projects", {}, "View Projects") : "View Projects";
      chatContextBtn.href = "collaborations.html";
      chatContextBtn.style.display = "inline-flex";
    } else {
      chatContextBtn.style.display = "none";
    }

    if (isDirect && other.user_id) {
      optionsBtn.style.display = "inline-flex";
      updateBlockUI(conv.is_blocked, conv.blocked_by_me, other);
    } else {
      optionsBtn.style.display = "none";
      blockedBanner.style.display = "none";
      composer.style.display = "flex";
    }

    const tLoadingMsgs = window.i18n ? window.i18n.t("common.loading", {}, "Loading messages...") : "Loading messages...";
    stream.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 13px; padding: 20px;">${escapeHtml(tLoadingMsgs)}</div>`;

    fetch(`/api/conversations/${conv.conv_id}/messages?limit=50`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          stream.innerHTML = "";
          const msgs = data.messages || [];
          if (msgs.length === 0) {
            const tNoMsgsYet = window.i18n ? window.i18n.t("msg.no_messages", {}, "No messages in this conversation yet.") : "No messages in this conversation yet.";
            const tSayHello = window.i18n ? window.i18n.t("msg.select_conversation", {}, "Say hello to start collaborating!") : "Say hello to start collaborating!";
            stream.innerHTML = `
              <div style="text-align: center; color: var(--text-muted); font-size: 13.5px; padding: 40px 20px;">
                <p>${escapeHtml(tNoMsgsYet)}</p>
                <p style="font-size: 12.5px; margin-top: 4px;">${escapeHtml(tSayHello)}</p>
              </div>
            `;
          } else {
            msgs.forEach(m => {
              appendMessageBubble(m, false);
              knownMsgIds.add(m.msg_id);
            });
            scrollStreamToBottom();
          }

          startActivePolling();
        }
      })
      .catch(() => {
        const tFailedMsgs = window.i18n ? window.i18n.t("common.error", {}, "Failed to load messages. Please try again.") : "Failed to load messages. Please try again.";
        stream.innerHTML = `<div style="text-align: center; color: #b91c1c; font-size: 13px; padding: 20px;">${escapeHtml(tFailedMsgs)}</div>`;
      });
  }

  function updateBlockUI(isBlocked, blockedByMe, other) {
    const otherName = other.name || (window.i18n ? window.i18n.t("auth.community_member", {}, "User") : "User");
    const tBlock = window.i18n ? window.i18n.t("msg.block_user", {}, "Block User") : "Block User";
    const tUnblock = window.i18n ? window.i18n.t("msg.unblock_user", {}, "Unblock User") : "Unblock User";
    const tBlockedNotice = window.i18n ? window.i18n.t("msg.communication_blocked", {}, "Communication is unavailable.") : "Communication is unavailable.";

    if (isBlocked) {
      composer.style.display = "none";
      blockedBanner.style.display = "flex";
      if (blockedByMe) {
        blockedText.textContent = `${tBlockedNotice} (${otherName})`;
        btnUnblockInBanner.style.display = "inline-block";
        btnUnblockInBanner.textContent = tUnblock;
        btnUnblockInBanner.onclick = () => handleUnblock(other.user_id);
        btnBlockUnblock.textContent = `${tUnblock} (${otherName})`;
        btnBlockUnblock.onclick = () => handleUnblock(other.user_id);
      } else {
        blockedText.textContent = tBlockedNotice;
        btnUnblockInBanner.style.display = "none";
        btnBlockUnblock.textContent = `${tBlock} (${otherName})`;
        btnBlockUnblock.onclick = () => handleBlock(other.user_id);
      }
    } else {
      composer.style.display = "flex";
      blockedBanner.style.display = "none";
      btnBlockUnblock.textContent = `${tBlock} (${otherName})`;
      btnBlockUnblock.onclick = () => handleBlock(other.user_id);
    }
  }

  function handleBlock(targetUserId) {
    if (!confirm("Are you sure you want to block this user? They will not be able to message you.")) return;
    fetch(`/api/users/${targetUserId}/block`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        showToast("User blocked.");
        if (activeConv) {
          activeConv.is_blocked = true;
          activeConv.blocked_by_me = true;
          updateBlockUI(true, true, activeConv.other_participant || {});
        }
      } else {
        showToast(res.error || "Failed to block user.");
      }
    });
  }

  function handleUnblock(targetUserId) {
    fetch(`/api/users/${targetUserId}/unblock`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        showToast("User unblocked.");
        if (activeConv) {
          activeConv.is_blocked = false;
          activeConv.blocked_by_me = false;
          updateBlockUI(false, false, activeConv.other_participant || {});
        }
      } else {
        showToast(res.error || "Failed to unblock user.");
      }
    });
  }

  function appendMessageBubble(m, animate = true) {
    const isMe = m.sender_id === window.CURRENT_USER.user_id;
    const isSystem = m.message_type === "system";

    if (isSystem) {
      const sysDiv = document.createElement("div");
      sysDiv.className = "message-bubble system";
      sysDiv.textContent = m.body;
      stream.appendChild(sysDiv);
      return;
    }

    const row = document.createElement("div");
    row.className = `message-bubble-row ${isMe ? 'outgoing' : 'incoming'}`;
    row.dataset.msgId = m.msg_id;

    const timeStr = formatMsgTime(m.created_at);
    const initials = getInitials(m.sender_name);

    row.innerHTML = `
      ${!isMe ? `
        <div class="msg-sender-avatar" title="${m.sender_name}">
          ${m.sender_avatar ? `<img src="${m.sender_avatar}" alt="${m.sender_name}">` : initials}
        </div>
      ` : ''}
      <div class="msg-bubble-content">
        ${!isMe ? `<span class="msg-sender-label">${m.sender_name}</span>` : ''}
        <div class="message-bubble ${isMe ? 'outgoing' : 'incoming'}">
          <div class="msg-body-text" style="white-space: pre-wrap;">${escapeHtml(m.body)}</div>
          <div class="message-time">
            <span>${timeStr}</span>
            ${isMe ? `<span>✓✓</span>` : ''}
          </div>
        </div>
      </div>
    `;

    if (!isMe && window.i18n && m.body) {
      const transWrap = document.createElement("div");
      transWrap.className = "ugc-msg-translate";
      window.i18n.setupUGCTranslateToggle(transWrap, m.body, "auto");
      const bubbleContent = row.querySelector(".msg-bubble-content");
      if (bubbleContent) bubbleContent.appendChild(transWrap);
    }

    stream.appendChild(row);
  }

  function scrollStreamToBottom() {
    stream.scrollTop = stream.scrollHeight;
  }

  function startActivePolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(() => {
      if (!activeConv) return;
      fetch(`/api/conversations/${activeConv.conv_id}/messages?limit=25`)
        .then(r => r.json())
        .then(data => {
          if (data.success && data.messages) {
            let hasNew = false;
            data.messages.forEach(m => {
              if (!knownMsgIds.has(m.msg_id)) {
                knownMsgIds.add(m.msg_id);
                appendMessageBubble(m, true);
                hasNew = true;
              }
            });
            if (hasNew) {
              scrollStreamToBottom();
            }
          }
        })
        .catch(() => {});
    }, 3500);
  }

  if (listPollInterval) clearInterval(listPollInterval);
  listPollInterval = setInterval(() => {
    fetch("/api/conversations")
      .then(r => r.json())
      .then(data => {
        if (data.success && data.conversations) {
          conversations = data.conversations;
          renderConversationsList();
        }
      })
      .catch(() => {});
  }, 10000);

  function sendMessage() {
    if (!activeConv) return;
    const text = (chatInput ? chatInput.value : "").trim();
    if (!text) return;

    if (text.length > 2000) {
      showToast("Message exceeds 2000 character limit.");
      return;
    }

    btnSend.disabled = true;
    chatInput.disabled = true;

    fetch(`/api/conversations/${activeConv.conv_id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body: text })
    })
    .then(r => r.json())
    .then(data => {
      btnSend.disabled = false;
      chatInput.disabled = false;

      if (data.success && data.message) {
        chatInput.value = "";
        chatInput.style.height = "auto";
        if (charCounter) charCounter.textContent = "0 / 2000";

        knownMsgIds.add(data.message.msg_id);
        appendMessageBubble(data.message, true);
        scrollStreamToBottom();

        activeConv.last_message = data.message;
        renderConversationsList();
        chatInput.focus();
      } else {
        showToast(data.error || "Failed to send message.");
      }
    })
    .catch(() => {
      btnSend.disabled = false;
      chatInput.disabled = false;
      showToast("Network error while sending message.");
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  const params = new URLSearchParams(window.location.search);
  const targetUser = params.get("user");
  const targetProject = params.get("project");
  const targetConv = params.get("conversation");

  if (targetUser) {
    fetch("/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient_id: targetUser })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success && res.conversation) {
        loadConversations(res.conversation.conv_id);
      } else {
        showToast(res.error || "Could not open conversation with this user.");
        loadConversations();
      }
    })
    .catch(() => loadConversations());

  } else if (targetProject) {
    fetch("/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: parseInt(targetProject) })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success && res.conversation) {
        loadConversations(res.conversation.conv_id);
      } else {
        showToast(res.error || "Could not access project conversation.");
        loadConversations();
      }
    })
    .catch(() => loadConversations());

  } else if (targetConv) {
    loadConversations(targetConv);
  } else {
    loadConversations();
  }

  window.refreshMessagesPage = function () {
    loadConversations(activeConv ? activeConv.conv_id : null);
  };
}

