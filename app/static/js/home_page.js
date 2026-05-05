const STATE_KEYS = {
  AUTH: 'movieStarDemoAuth',
  WATCHLIST: 'movieStarDemoWatchlist'
};

const DEFAULT_STATES = {
  AUTH: 'guest',
  WATCHLIST: 'empty'
};

function initializeState() {
  if (!localStorage.getItem(STATE_KEYS.AUTH)) {
    localStorage.setItem(STATE_KEYS.AUTH, DEFAULT_STATES.AUTH);
  }

  if (!localStorage.getItem(STATE_KEYS.WATCHLIST)) {
    localStorage.setItem(STATE_KEYS.WATCHLIST, DEFAULT_STATES.WATCHLIST);
  }
}

function getAuthState() {
  return localStorage.getItem(STATE_KEYS.AUTH) || DEFAULT_STATES.AUTH;
}

function setAuthState(state) {
  localStorage.setItem(STATE_KEYS.AUTH, state);
  updateAuthDisplay();
}

function updateAuthDisplay() {
  const authState = getAuthState();
  const guestElements = document.querySelectorAll('.auth-guest-only');
  const loggedInElements = document.querySelectorAll('.auth-loggedin-only');

  if (authState === 'logged-in') {
    guestElements.forEach((el) => el.classList.add('hidden'));
    loggedInElements.forEach((el) => el.classList.remove('hidden'));
  } else {
    guestElements.forEach((el) => el.classList.remove('hidden'));
    loggedInElements.forEach((el) => el.classList.add('hidden'));
  }
}

function setupLogoutButton() {
  const logoutBtn = document.getElementById('home-logout-btn');

  if (!logoutBtn) {
    return;
  }

  logoutBtn.addEventListener('click', (event) => {
    event.preventDefault();
    setAuthState('guest');
  });
}

function setupDemoStateControls() {
  const toggleBtn = document.getElementById('demo-toggle-btn');
  const controlsPanel = document.getElementById('demo-controls');
  const authSelect = document.getElementById('auth-state-select');
  const switcher = document.getElementById('demo-state-switcher');

  if (!toggleBtn || !controlsPanel || !authSelect || !switcher) {
    return;
  }

  authSelect.value = getAuthState();

  toggleBtn.addEventListener('click', (event) => {
    event.stopPropagation();
    controlsPanel.classList.toggle('hidden');
  });

  authSelect.addEventListener('change', (event) => {
    setAuthState(event.target.value);
  });

  document.addEventListener('click', (event) => {
    if (!switcher.contains(event.target)) {
      controlsPanel.classList.add('hidden');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initializeState();
  updateAuthDisplay();
  setupLogoutButton();
  setupDemoStateControls();
});