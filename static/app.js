(() => {
  const bg = document.querySelector('.bg-reactive');
  const grid = document.querySelector('.bg-grid');
  const root = document.documentElement;

  document.addEventListener('mousemove', (event) => {
    const x = event.clientX / window.innerWidth;
    const y = event.clientY / window.innerHeight;

    if (bg) {
      bg.style.setProperty('--x', `${x * 100}%`);
      bg.style.setProperty('--y', `${y * 100}%`);
    }

    if (grid) {
      const tiltX = (y - 0.5) * 10;
      const tiltY = (x - 0.5) * -10;
      grid.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg)`;
    }

    root.style.setProperty('--mx', `${x * 100}%`);
    root.style.setProperty('--my', `${y * 100}%`);
  });

  document.querySelectorAll('button, .link-btn').forEach((element) => {
    element.addEventListener('click', () => {
      element.classList.remove('pulse');
      void element.offsetWidth;
      element.classList.add('pulse');
    });
  });

  const searchInput = document.getElementById('file-search');
  const rows = Array.from(document.querySelectorAll('.file-row'));

  if (searchInput && rows.length) {
    searchInput.addEventListener('input', () => {
      const value = searchInput.value.trim().toLowerCase();
      rows.forEach((row) => {
        const name = row.dataset.filename ?? '';
        row.style.display = name.includes(value) ? '' : 'none';
      });
    });
  }
})();
