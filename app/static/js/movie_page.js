// Movie detail page interactions.
// The star-rating widget and write-review form will be added back by
// Module C when the review endpoints land. For now this file handles:
//   * navbar scroll effect
//   * "Write a Review" CTA scrolls down to the placeholder section
//   * "Add to Watchlist" button posts to /watchlist/add/<id> via AJAX

const navbar = document.getElementById('navbar');
const writeReviewTrigger = document.getElementById('write-review-trigger');
const writeReviewSection = document.getElementById('write-review');
const watchlistButton = document.querySelector('.movie-cta[data-movie-id]');

// ── Helpers ────────────────────────────────────────────────────────

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

async function postWatchlist(action, movieId) {
  // action is 'add' or 'remove'.
  const response = await fetch(`/watchlist/${action}/${movieId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Accept': 'application/json',
    },
  });

  // Flask-Login redirects unauthenticated requests to /auth; the browser
  // transparently follows the 302 and the final response.url ends up at
  // the auth page. Detect that and bounce the user there explicitly.
  if (response.redirected || response.status === 401) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/auth?next=${next}`;
    return null;
  }

  let data = {};
  try {
    data = await response.json();
  } catch (e) {
    // Not JSON — leave data empty so callers see ok=false below.
  }

  return { ok: response.ok, status: response.status, data };
}

// ── Navbar ────────────────────────────────────────────────────────

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}

// ── Write a Review CTA ────────────────────────────────────────────

if (writeReviewTrigger && writeReviewSection) {
  writeReviewTrigger.addEventListener('click', () => {
    writeReviewSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

// ── Add to Watchlist ──────────────────────────────────────────────

if (watchlistButton) {
  watchlistButton.addEventListener('click', async () => {
    const movieId = watchlistButton.dataset.movieId;
    if (!movieId) return;

    watchlistButton.disabled = true;
    const result = await postWatchlist('add', movieId);
    if (result === null) return; // redirect already happened

    if (result.ok) {
      // Server says either "added: true" (new) or "already_added: true".
      watchlistButton.textContent = result.data.already_added
        ? 'Already on Watchlist'
        : 'Added to Watchlist';
      watchlistButton.classList.add('movie-cta-success');
    } else {
      // Re-enable so the user can retry if the request failed.
      watchlistButton.disabled = false;
      const message = (result.data && result.data.error) || 'Could not update your watchlist.';
      window.alert(message);
    }
  });
}
