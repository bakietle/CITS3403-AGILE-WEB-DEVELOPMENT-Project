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

function getWatchlistState() {
  return localStorage.getItem(STATE_KEYS.WATCHLIST) || DEFAULT_STATES.WATCHLIST;
}

function setAuthState(state) {
  localStorage.setItem(STATE_KEYS.AUTH, state);
  updatePageDisplay();
}

function setWatchlistState(state) {
  localStorage.setItem(STATE_KEYS.WATCHLIST, state);
  updatePageDisplay();
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

function updateEmptyStateContent(authState) {
  const title = document.getElementById('watchlist-empty-title');
  const copy = document.getElementById('watchlist-empty-copy');
  const cta = document.getElementById('watchlist-empty-cta');

  if (!title || !copy || !cta) {
    return;
  }

  if (authState === 'guest') {
    title.textContent = 'Log in to save your watchlist';
    copy.textContent = 'Create an account or sign in to save movies and access your watchlist across the app.';
    cta.textContent = 'Log In / Sign Up';
    cta.setAttribute('href', 'auth.html');
  } else {
    title.textContent = 'Your Watchlist is Empty';
    copy.textContent = 'Start building your watchlist by browsing movies and adding the ones you want to watch later.';
    cta.textContent = 'Browse Movies';
    cta.setAttribute('href', 'home_page.html');
  }
}

function updatePageDisplay() {
  const authState = getAuthState();
  const watchlistState = getWatchlistState();

  const emptyState = document.getElementById('watchlist-empty-state');
  const filledState = document.getElementById('watchlist-filled-state');
  const watchlistSelect = document.getElementById('watchlist-state-select');
  const emptyInfoSection = document.getElementById('watchlist-empty-info-section');

  updateAuthDisplay();
  updateEmptyStateContent(authState);

  if (!emptyState || !filledState) {
    return;
  }

  if (authState === 'guest') {
    emptyState.classList.remove('hidden');
    filledState.classList.add('hidden');

    if (emptyInfoSection) {
      emptyInfoSection.classList.add('hidden');
    }
  } else if (watchlistState === 'empty') {
    emptyState.classList.remove('hidden');
    filledState.classList.add('hidden');

    if (emptyInfoSection) {
      emptyInfoSection.classList.remove('hidden');
    }
  } else {
    emptyState.classList.add('hidden');
    filledState.classList.remove('hidden');

    if (emptyInfoSection) {
      emptyInfoSection.classList.add('hidden');
    }
  }

  if (watchlistSelect) {
    watchlistSelect.disabled = authState === 'guest';
  }
}

function setupLogoutButton() {
  const logoutBtn = document.getElementById('watchlist-logout-btn');

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
  const watchlistSelect = document.getElementById('watchlist-state-select');
  const switcher = document.getElementById('demo-state-switcher');

  if (!toggleBtn || !controlsPanel || !authSelect || !watchlistSelect || !switcher) {
    return;
  }

  authSelect.value = getAuthState();
  watchlistSelect.value = getWatchlistState();

  toggleBtn.addEventListener('click', (event) => {
    event.stopPropagation();
    controlsPanel.classList.toggle('hidden');
  });

  authSelect.addEventListener('change', (event) => {
    setAuthState(event.target.value);
  });

  watchlistSelect.addEventListener('change', (event) => {
    setWatchlistState(event.target.value);
  });

  document.addEventListener('click', (event) => {
    if (!switcher.contains(event.target)) {
      controlsPanel.classList.add('hidden');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initializeState();
  updatePageDisplay();
  setupLogoutButton();
  setupDemoStateControls();
});