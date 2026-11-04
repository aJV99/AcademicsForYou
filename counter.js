// The About page's counters counted up from 0 on Weebly. This does the same.
document.querySelectorAll(".counter-number").forEach((el) => {
  const to = Number(el.dataset.to);
  const start = performance.now();
  const duration = 2000;
  const tick = (now) => {
    const t = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(to * (1 - Math.pow(1 - t, 3)));
    if (t < 1) requestAnimationFrame(tick);
  };
  el.textContent = "0";
  requestAnimationFrame(tick);
});
