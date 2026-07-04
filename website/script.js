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

  toggle.setAttribute(
    "aria-pressed",
    String(root.getAttribute("data-theme") === "dark"),
  );

  toggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    // Enable transitions only for this deliberate switch — never on page load.
    root.classList.add("is-transitioning");
    setTimeout(() => root.classList.remove("is-transitioning"), 400);
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

// ---------- Settings UI carousel ----------
(function () {
  const dots = document.querySelectorAll(".duo-dot");
  const arrows = document.querySelectorAll(".duo-arrow");
  const slides = document.querySelectorAll(".duo-slide");
  if (!dots.length || !slides.length) return;

  const totalSlides = slides.length;
  let currentSlide = 0;

  function goToSlide(index) {
    currentSlide = (index + totalSlides) % totalSlides;

    dots.forEach((d, i) => {
      d.classList.toggle("active", i === currentSlide);
    });
    slides.forEach((s, i) => {
      s.classList.toggle("active", i === currentSlide);
    });
  }

  // Dots
  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      goToSlide(parseInt(dot.dataset.slide, 10));
    });
  });

  // Arrows
  arrows.forEach((arrow) => {
    arrow.addEventListener("click", () => {
      const isLeft = arrow.classList.contains("duo-arrow-left");
      goToSlide(currentSlide + (isLeft ? -1 : 1));
    });
  });

  // Click on left/right side of carousel
  const track = document.querySelector(".duo-carousel-track");
  if (track) {
    track.addEventListener("click", (e) => {
      if (e.target.closest(".duo-arrow")) return;
      const rect = track.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const isRight = x > rect.width / 2;
      goToSlide(currentSlide + (isRight ? 1 : -1));
    });
  }

  // Swipe gestures for mobile
  let touchStartX = 0;
  let touchEndX = 0;
  const carousel = document.querySelector(".duo-carousel");
  if (carousel) {
    carousel.addEventListener(
      "touchstart",
      (e) => {
        touchStartX = e.changedTouches[0].screenX;
      },
      { passive: true },
    );
    carousel.addEventListener(
      "touchend",
      (e) => {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
          goToSlide(currentSlide + (diff > 0 ? 1 : -1));
        }
      },
      { passive: true },
    );
  }

  // Show/hide arrows based on carousel visibility in viewport
  const carouselEl = document.querySelector(".duo-carousel");
  if (carouselEl && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          entry.target.classList.toggle("in-view", entry.isIntersecting);
        });
      },
      { threshold: 0.1 },
    );
    observer.observe(carouselEl);
  }
})();

// ---------- Scroll-reveal for cards and sections
(function () {
  const targets = document.querySelectorAll(
    ".feature-card, .duo-card, .step, .roadmap li, .privacy-list li, .duo-hero, .section-title, .section-sub, .section-eyebrow, .toast-marquee, .ui-showcase",
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
    { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
  );

  targets.forEach((el) => observer.observe(el));
})();

import { inject } from "@vercel/analytics";
inject();
