(function () {
  // Day tabs
  document.querySelectorAll(".plan").forEach(function (plan) {
    plan.addEventListener("click", function (e) {
      var btn = e.target.closest(".daybtn");
      if (!btn) return;
      plan.querySelectorAll(".daybtn").forEach(function (b) { b.setAttribute("aria-selected", b === btn ? "true" : "false"); });
      plan.querySelectorAll(".daypanel").forEach(function (p) { p.hidden = p.dataset.panel !== btn.dataset.day; });
    });
  });

  // Updated / original toggle
  document.querySelectorAll('input[name="ver"]').forEach(function (r) {
    r.addEventListener("change", function () {
      document.querySelectorAll(".plan").forEach(function (p) { p.hidden = p.dataset.version !== r.value; });
    });
  });

  // Feedback chips
  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var ta = chip.closest("form").querySelector("textarea");
      ta.value = ta.value ? ta.value.replace(/[.\s]*$/, "") + ", " + chip.dataset.fill.toLowerCase() : chip.dataset.fill;
      ta.focus();
    });
  });

  // Loading state while Gemini works
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector("#submitBtn"), hint = form.querySelector("#waitHint");
      if (btn && form.checkValidity()) { btn.disabled = true; btn.textContent = "Working..."; }
      if (hint && form.checkValidity()) hint.hidden = false;
    });
  });

  // Admin table filter
  var f = document.getElementById("filter");
  if (f) f.addEventListener("input", function () {
    var q = f.value.toLowerCase();
    document.querySelectorAll("#usersTable tbody tr").forEach(function (tr) {
      var cells = tr.children, text = (cells[0].textContent + " " + cells[1].textContent + " " + cells[4].textContent).toLowerCase();
      tr.hidden = q && text.indexOf(q) === -1;
    });
  });
})();
