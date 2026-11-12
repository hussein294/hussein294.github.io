// Light and dark mode. Follows the system setting until the visitor picks one.
(function () {
  var button = document.getElementById("theme-toggle");
  if (!button) return;
  var root = document.documentElement;
  button.addEventListener("click", function () {
    var current = root.getAttribute("data-theme");
    if (!current) {
      current = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    var next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch (e) {}
  });
})();
