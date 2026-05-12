// Watchlist page interactions.
//
// Each watchlist card has a Remove button. Clicking it fires a POST to
// /watchlist/remove/<movie_id>, then on success fades the card out and
// removes it from the DOM. If that was the last card, reload the page so
// the server-rendered empty state takes over.

const removeButtons = Array.from(
  document.querySelectorAll('.watchlist-remove-btn[data-movie-id]')
);

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

async function postWatchlistRemove(movieId) {
  const response = await fetch(`/watchlist/remove/${movieId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Accept': 'application/json',
    },
  });

  if (response.redirected || response.status === 401) {
    const next = encodeURIComponent(window.location.pathname);
    window.location.href = `/auth?next=${next}`;
    return null;
  }

  let data = {};
  try {
    data = await response.json();
  } catch (e) {
    // Non-JSON response; leave empty.
  }
  return { ok: response.ok, data };
}

function fadeAndRemove(card) {
  card.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
  card.style.opacity = '0';
  card.style.transform = 'scale(0.96)';
  window.setTimeout(() => {
    card.remove();
    // If that was the last card, reload to render the empty state from
    // the server template instead of patching the DOM by hand.
    if (!document.querySelector('.watchlist-card')) {
      window.location.reload();
    }
  }, 260);
}

removeButtons.forEach((btn) => {
  btn.addEventListener('click', async () => {
    const movieId = btn.dataset.movieId;
    if (!movieId) return;

    btn.disabled = true;
    const result = await postWatchlistRemove(movieId);
    if (result === null) return;

    if (result.ok) {
      const card = btn.closest('.watchlist-card');
      if (card) {
        fadeAndRemove(card);
      }
    } else {
      btn.disabled = false;
      const message = (result.data && result.data.error) || 'Could not remove this movie.';
      window.alert(message);
    }
  });
});
