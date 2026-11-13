// Theme toggle: Paper (light) and Blackboard (dark). The choice is remembered.
(function () {
  var button = document.getElementById("theme-toggle");
  if (!button) return;
  button.addEventListener("click", function () {
    var d = document.documentElement;
    var t = d.getAttribute("data-theme") === "dark" ? "light" : "dark";
    d.setAttribute("data-theme", t);
    try {
      localStorage.setItem("theme", t);
    } catch (e) {}
  });
})();
