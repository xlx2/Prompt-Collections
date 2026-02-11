const root = document.documentElement;
const buttons = document.querySelectorAll('[data-theme-btn]');

function applyTheme(theme) {
  if (!theme) {
    root.setAttribute('data-theme', 'system');
    return;
  }
  root.setAttribute('data-theme', theme);
}

function setActive(theme) {
  buttons.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.themeBtn === theme);
  });
}

const savedTheme = localStorage.getItem('theme') || 'system';
applyTheme(savedTheme);
setActive(savedTheme);

buttons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const theme = btn.dataset.themeBtn;
    localStorage.setItem('theme', theme);
    applyTheme(theme);
    setActive(theme);
  });
});

document.querySelectorAll('.card[data-href]').forEach((card) => {
  card.addEventListener('click', (event) => {
    if (event.target.closest('[data-copy]')) {
      return;
    }
    window.location.href = card.dataset.href;
  });
});

document.querySelectorAll('[data-copy]').forEach((btn) => {
  btn.addEventListener('click', async (event) => {
    event.stopPropagation();
    const text = btn.dataset.copy || '';
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      const original = btn.textContent;
      btn.textContent = '已复制';
      setTimeout(() => {
        btn.textContent = original;
      }, 1200);
    } catch (err) {
      console.error(err);
    }
  });
});

document.querySelectorAll('button, .primary, .ghost, .danger, .nav-pill').forEach((el) => {
  el.classList.add('magnet');
  const resetMagnet = () => {
    el.style.transform = 'translate(0, 0)';
    el.style.removeProperty('--mx');
    el.style.removeProperty('--my');
    el.removeAttribute('data-magnet-active');
  };
  el.addEventListener('pointermove', (event) => {
    if (event.pointerType === 'touch') return;
    const rect = el.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const percentX = (x / rect.width) * 100;
    const percentY = (y / rect.height) * 100;
    el.style.setProperty('--mx', `${percentX}%`);
    el.style.setProperty('--my', `${percentY}%`);
    const moveX = (x - rect.width / 2) / rect.width;
    const moveY = (y - rect.height / 2) / rect.height;
    el.style.transform = `translate(${moveX * 4}px, ${moveY * 4}px)`;
    el.setAttribute('data-magnet-active', '1');
  });
  el.addEventListener('pointerleave', resetMagnet);
  el.addEventListener('pointercancel', resetMagnet);
  el.addEventListener('pointerup', resetMagnet);
  el.addEventListener('click', resetMagnet);
  el.addEventListener('blur', resetMagnet);
});

window.addEventListener('blur', () => {
  document.querySelectorAll('[data-magnet-active]').forEach((el) => {
    el.style.transform = 'translate(0, 0)';
    el.removeAttribute('data-magnet-active');
    el.style.removeProperty('--mx');
    el.style.removeProperty('--my');
  });
});

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    document.querySelectorAll('[data-magnet-active]').forEach((el) => {
      el.style.transform = 'translate(0, 0)';
      el.removeAttribute('data-magnet-active');
      el.style.removeProperty('--mx');
      el.style.removeProperty('--my');
    });
  }
});

const addTagButtons = document.querySelectorAll('[data-add-tag]');
addTagButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const container = btn.closest('.field')?.querySelector('[data-new-tag-container]');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'row tag-row-input';
    row.innerHTML = `
      <input name="new_tag_names" placeholder="标签名称" />
      <input class="color" type="color" name="new_tag_colors" value="#6b7280" />
    `;
    container.appendChild(row);
  });
});
