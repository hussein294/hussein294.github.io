// Workshops catalogue: filters and the slide-in preview panel.
// Without this script the page still works: every card links to the workshop's own page.
(function () {
  var grid = document.getElementById("ws-grid");
  if (!grid) return;

  // ---- Preview panel ----
  var canPreview = typeof HTMLDialogElement === "function";
  if (canPreview) {
    grid.addEventListener("click", function (event) {
      var link = event.target.closest("a[data-preview]");
      if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
      var panel = document.getElementById(link.getAttribute("data-preview"));
      if (!panel) return;
      event.preventDefault();
      panel.showModal();
      panel.scrollTop = 0;
    });
    // A click on the dimmed area outside the panel closes it.
    document.querySelectorAll("dialog.ws-panel").forEach(function (panel) {
      panel.addEventListener("click", function (event) {
        if (event.target === panel) panel.close();
      });
    });
  }

  // ---- Filters ----
  var filters = document.getElementById("ws-filters");
  var chips = filters ? filters.querySelectorAll(".ws-chip") : [];
  if (!chips.length) return;
  var items = grid.querySelectorAll(".ws-item");
  var count = document.getElementById("ws-count");
  var empty = document.getElementById("ws-empty");
  var active = { category: "", level: "" };
  filters.hidden = false;

  function apply() {
    var shown = 0;
    items.forEach(function (item) {
      var match =
        (!active.category || item.getAttribute("data-category") === active.category) &&
        (!active.level || item.getAttribute("data-level") === active.level);
      item.hidden = !match;
      if (match) shown += 1;
    });
    if (count) count.textContent = shown + (shown === 1 ? " workshop" : " workshops");
    if (empty) empty.hidden = shown !== 0;
  }

  filters.addEventListener("click", function (event) {
    var chip = event.target.closest(".ws-chip");
    if (!chip) return;
    var group = chip.getAttribute("data-filter");
    active[group] = chip.getAttribute("data-value");
    chips.forEach(function (other) {
      if (other.getAttribute("data-filter") === group) {
        other.setAttribute("aria-pressed", other === chip ? "true" : "false");
      }
    });
    apply();
  });
})();
