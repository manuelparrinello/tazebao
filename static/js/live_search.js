(function () {
  "use strict";

  var input = document.getElementById("global-search-input");
  if (!input) return;

  var form = document.getElementById("global-search");
  var dropdown = document.getElementById("search-dropdown");
  var results = document.getElementById("search-results");
  var footer = document.getElementById("search-full-link");

  var timer = null;
  var controller = null;

  function escHtml(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function close() {
    dropdown.style.display = "none";
  }

  function open() {
    dropdown.style.display = "block";
  }

  function render(response) {
    var data = response && response.data;
    if (!data || !data.categories || data.categories.length === 0) {
      results.innerHTML =
        '<div class="search-dropdown-empty">Nessun risultato</div>';
      footer.style.display = "none";
      open();
      return;
    }
    var html = "";
    for (var ci = 0; ci < data.categories.length; ci++) {
      var cat = data.categories[ci];
      html +=
        '<div class="search-dropdown-category">' +
        '<div class="search-dropdown-category-header">' +
        '<i class="bi ' + escHtml(cat.icon) + '"></i>' +
        "<span>" + escHtml(cat.label) + "</span>" +
        '<span class="search-dropdown-category-count">' +
        cat.results.length +
        "</span>" +
        "</div>";
      for (var ri = 0; ri < cat.results.length; ri++) {
        var r = cat.results[ri];
        html +=
          '<a href="' +
          escHtml(r.url) +
          '" class="search-dropdown-item">' +
          '<div class="search-dropdown-item-icon"><i class="bi ' +
          escHtml(r.icon || cat.icon) +
          '"></i></div>' +
          '<div class="search-dropdown-item-body">' +
          '<div class="search-dropdown-item-title">' +
          escHtml(r.label) +
          "</div>";
        if (r.subtitle) {
          html +=
            '<div class="search-dropdown-item-subtitle">' +
            escHtml(r.subtitle) +
            "</div>";
        }
        html += "</div>";
        html += '<span class="search-dropdown-item-badge">' + escHtml(cat.label) + "</span>";
        html += "</a>";
      }
      html += "</div>";
    }
    results.innerHTML = html;
    footer.href = "/search?q=" + encodeURIComponent(input.value);
    footer.style.display = "block";
    open();
  }

  function search(term) {
    if (controller) controller.abort();
    controller = new AbortController();

    results.innerHTML =
      '<div class="search-dropdown-loading"><div class="spinner-border spinner-border-sm me-1" role="status"></div> Ricerca...</div>';
    footer.style.display = "none";
    open();

    fetch("/api/search?q=" + encodeURIComponent(term), {
      signal: controller.signal,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(render)
      .catch(function (err) {
        if (err.name === "AbortError") return;
        results.innerHTML =
          '<div class="search-dropdown-empty">Errore durante la ricerca</div>';
        open();
      });
  }

  input.addEventListener("input", function () {
    var term = this.value.trim();
    clearTimeout(timer);
    if (term.length < 2) {
      close();
      return;
    }
    timer = setTimeout(function () {
      search(term);
    }, 300);
  });

  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      close();
      this.blur();
    }
  });

  document.addEventListener("click", function (e) {
    if (!form.contains(e.target)) {
      close();
    }
  });
})();
