// ---------- Theme toggle ----------
// The initial theme is set by the inline <head> script before first paint
// (priority: ?theme= URL override > saved choice > system preference).
// This module only reacts to clicks and OS theme changes — it never
// re-decides the theme on load, so it can't overwrite the head script.
(function () {
  const root = document.documentElement;
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  const toggle = document.getElementById("theme-toggle");

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    toggle.setAttribute("aria-pressed", String(theme === "dark"));
  }

  toggle.setAttribute("aria-pressed", String(root.getAttribute("data-theme") === "dark"));

  toggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
    try {
      localStorage.setItem("biryani-theme", next);
    } catch (e) {
      /* private browsing / blocked storage — theme still toggles for this visit */
    }
  });

  // Keep following the OS until the user picks a theme manually
  media.addEventListener("change", (e) => {
    let saved = null;
    try {
      saved = localStorage.getItem("biryani-theme");
    } catch (err) {}
    if (!saved) apply(e.matches ? "dark" : "light");
  });
})();

// ---------- Scroll-reveal for cards and sections ----------
(function () {
  const targets = document.querySelectorAll(
    ".feature-card, .duo-card, .step, .roadmap li, .privacy-list li, .duo-hero, .section-title, .section-sub, .section-eyebrow"
  );

  if (!("IntersectionObserver" in window)) return;

  targets.forEach((el) => el.classList.add("reveal"));

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
  );

  targets.forEach((el) => observer.observe(el));
})();
