// ---------- Theme: follow system by default, remember manual choice ----------
(function () {
  const root = document.documentElement;
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function apply(theme) {
    root.setAttribute("data-theme", theme);
  }

  const saved = localStorage.getItem("biryani-theme");
  apply(saved || (media.matches ? "dark" : "light"));

  // Keep syncing with the OS until the user picks a theme manually
  media.addEventListener("change", (e) => {
    if (!localStorage.getItem("biryani-theme")) {
      apply(e.matches ? "dark" : "light");
    }
  });

  document.getElementById("theme-toggle").addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
    localStorage.setItem("biryani-theme", next);
  });
})();

// ---------- Scroll-reveal for cards and sections ----------
(function () {
  const targets = document.querySelectorAll(
    ".feature-card, .duo-card, .step, .roadmap li, .privacy-list li, .duo-hero, .section-title, .section-sub, .section-eyebrow"
  );
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
