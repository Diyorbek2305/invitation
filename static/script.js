// ---------- countdown ----------
(function () {
  const el = document.querySelector(".countdown");
  if (!el) return;
  const target = new Date(el.dataset.target).getTime();

  const days = el.querySelector('[data-unit="days"]');
  const hours = el.querySelector('[data-unit="hours"]');
  const minutes = el.querySelector('[data-unit="minutes"]');
  const seconds = el.querySelector('[data-unit="seconds"]');

  function pad(n) { return String(n).padStart(2, "0"); }

  function tick() {
    const diff = target - Date.now();
    if (diff <= 0) {
      days.textContent = hours.textContent = minutes.textContent = seconds.textContent = "00";
      return;
    }
    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const m = Math.floor((diff / (1000 * 60)) % 60);
    const s = Math.floor((diff / 1000) % 60);
    days.textContent = pad(d);
    hours.textContent = pad(h);
    minutes.textContent = pad(m);
    seconds.textContent = pad(s);
  }
  tick();
  setInterval(tick, 1000);
})();

// ---------- scroll reveal ----------
(function () {
  const items = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || items.length === 0) {
    items.forEach((i) => i.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  items.forEach((i) => observer.observe(i));
})();

// ---------- background music ----------
(function () {
  const audio = document.getElementById("bg-music");
  const btn = document.getElementById("music-toggle");
  if (!audio || !btn) return;

  audio.volume = 0.55;

  btn.addEventListener("click", () => {
    if (audio.paused) {
      audio.play().catch(() => {
        // Файл ещё не добавлен (background-music.mp3) или браузер заблокировал звук
      });
      btn.classList.add("is-playing");
      btn.setAttribute("aria-pressed", "true");
      btn.setAttribute("aria-label", "Выключить музыку");
    } else {
      audio.pause();
      btn.classList.remove("is-playing");
      btn.setAttribute("aria-pressed", "false");
      btn.setAttribute("aria-label", "Включить музыку");
    }
  });
})();

// ---------- guests field toggle ----------
(function () {
  const radios = document.querySelectorAll('input[name="attending"]');
  const guestsField = document.getElementById("guests-field");
  radios.forEach((r) =>
    r.addEventListener("change", (e) => {
      guestsField.classList.toggle("is-visible", e.target.value === "yes");
    })
  );
})();

// ---------- RSVP submit ----------
(function () {
  const form = document.getElementById("rsvp-form");
  if (!form) return;
  const msg = document.getElementById("form-msg");
  const thanks = document.getElementById("thanks-block");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.textContent = "";
    msg.className = "form-msg";

    const payload = {
      name: form.name.value,
      attending: form.attending.value,
      guests: form.guests.value,
      wish: form.wish.value,
    };

    try {
      const res = await fetch("/rsvp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.ok) {
        form.style.display = "none";
        thanks.style.display = "block";
      } else {
        msg.textContent = data.error || "Что-то пошло не так. Попробуйте ещё раз.";
        msg.classList.add("error");
      }
    } catch (err) {
      msg.textContent = "Не удалось отправить ответ. Проверьте соединение.";
      msg.classList.add("error");
    }
  });
})();
