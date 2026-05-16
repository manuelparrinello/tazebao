(function () {
  var container = document.getElementById("notif-container");
  if (!container) return;

  function loadNotifications() {
    fetch("/api/dashboard/summary", {
      headers: { Accept: "application/json" },
    })
      .then(function (r) {
        var ct = r.headers.get("content-type") || "";
        if (!ct.includes("application/json")) {
          renderNotifications([]);
          return null;
        }
        return r.json();
      })
      .then(function (payload) {
        if (!payload) return;
        if (!payload.success) return;
        renderNotifications(payload.data.notifications || []);
      })
      .catch(function () {});
  }

  function renderNotifications(notifs) {
    var count = notifs.length;
    var badge = document.getElementById("notif-badge");
    var list = document.getElementById("notif-list");
    if (badge) {
      badge.textContent = count > 99 ? "99+" : count;
      badge.style.display = count > 0 ? "inline-flex" : "none";
    }
    if (!list) return;
    if (count === 0) {
      list.innerHTML =
        '<span class="text-muted small">Nessuna notifica</span>';
      return;
    }
    list.innerHTML = notifs
      .map(function (n) {
        var iconHtml = n.icon
          ? '<i class="bi ' + n.icon + ' notif-icon"></i>'
          : "";
        return (
          '<a class="dropdown-item notif-item" href="' +
          n.url +
          '"><div class="d-flex align-items-start gap-2">' +
          iconHtml +
          '<div class="min-w-0 overflow-hidden"><div class="notif-title text-truncate">' +
          escHtml(n.title) +
          '</div><div class="notif-desc text-truncate">' +
          escHtml(n.description || "") +
          "</div></div></div></a>"
        );
      })
      .join("");
  }

  function escHtml(s) {
    var d = document.createElement("div");
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadNotifications);
  } else {
    loadNotifications();
  }
  setInterval(loadNotifications, 60000);
})();
