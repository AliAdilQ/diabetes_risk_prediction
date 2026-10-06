"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const predictionForm = document.getElementById("prediction-form");
  document.getElementById("fill-example")?.addEventListener("click", () => {
    predictionForm.querySelectorAll("[data-example]").forEach((input) => {
      input.value = input.dataset.example;
      input.classList.remove("is-invalid");
      input.setAttribute("aria-invalid", "false");
    });
  });
  predictionForm?.addEventListener("submit", () => {
    const button = predictionForm.querySelector('button[type="submit"]');
    button.disabled = true;
    button.querySelector(".submit-label").classList.add("d-none");
    button.querySelector(".loading-label").classList.remove("d-none");
  });
  document.getElementById("toggle-password")?.addEventListener("click", (event) => {
    const password = document.getElementById("password");
    const show = password.type === "password";
    password.type = show ? "text" : "password";
    event.currentTarget.setAttribute("aria-label", show ? "Hide password" : "Show password");
    event.currentTarget.setAttribute("aria-pressed", String(show));
    event.currentTarget.querySelector("i").className = show ? "bi bi-eye-slash" : "bi bi-eye";
  });
  document.querySelector(".sidebar-toggle")?.addEventListener("click", (event) => {
    const open = document.body.classList.toggle("sidebar-open");
    event.currentTarget.setAttribute("aria-expanded", String(open));
  });
  document.querySelector(".admin-content")?.addEventListener("click", () => {
    document.body.classList.remove("sidebar-open");
    document.querySelector(".sidebar-toggle")?.setAttribute("aria-expanded", "false");
  });
});

// Re-enable submission when navigating back from a result through the browser cache.
window.addEventListener("pageshow", () => {
  const button = document.querySelector('#prediction-form button[type="submit"]');
  if (button && button.querySelector(".submit-label").classList.contains("d-none")) {
    button.disabled = false;
    button.querySelector(".submit-label").classList.remove("d-none");
    button.querySelector(".loading-label").classList.add("d-none");
  }
});
