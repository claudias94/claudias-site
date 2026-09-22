const toggle = document.querySelector(".nav-toggle");
const menu = document.getElementById("nav-menu");
if (toggle && menu) {
  toggle.addEventListener("click", () => {
    const open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

function getCsrfToken() {
  const input = document.querySelector('input[name="csrf_token"]');
  return input ? input.value : "";
}

function sendEvent(event, label) {
  try {
    fetch("/api/event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event: event, label: label || "", csrf_token: getCsrfToken() }),
      keepalive: true,
    }).catch(() => {});
  } catch (e) { /* analytics must never break the page */ }
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-event]");
  if (el) sendEvent(el.dataset.event, el.dataset.label || "");
});

const projectForm = document.querySelector("form.form[action*='/contact']");
if (projectForm) {
  let started = false;
  projectForm.addEventListener("input", () => {
    if (!started) { started = true; sendEvent("project_form_started", ""); }
  }, { once: false });
}
