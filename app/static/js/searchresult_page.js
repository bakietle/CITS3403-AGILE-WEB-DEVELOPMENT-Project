// Search results page interactions.
//
// Filter chips, year input, and min-rating select all live inside a single
// GET <form>. Genre chips also sync a hidden input so the form submits the
// chosen genre, and clicking a chip auto-submits the form for instant
// feedback. Reset button restores defaults without submitting.
//
// Watchlist bookmark buttons on each result card POST to
// /watchlist/add/<id> via AJAX.

const navbar = document.getElementById('navbar');
const genreChips = Array.from(document.querySelectorAll('.filter-chip'));
const genreFilterGroup = document.getElementById('genre-filter-group');
const genreHiddenInput = document.getElementById('genre-hidden');
const releaseYearInput = document.getElementById('release-year');
const minRatingSelect = document.getElementById('min-rating');
const resetFiltersButton = document.getElementById('reset-filters-btn');
const watchlistButtons = Array.from(
  document.querySelectorAll('.search-card-watchlist[data-movie-id]')
);

// ── Helpers ────────────────────────────────────────────────────────

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

async function postWatchlistAdd(movieId) {
  const response = await fetch(`/watchlist/add/${movieId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Accept': 'application/json',
    },
  });

  if (response.redirected || response.status === 401) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
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

const setActiveGenre = (selectedChip) => {
  genreChips.forEach((chip) => {
    chip.classList.toggle('active', chip === selectedChip);
  });

  // Sync the hidden form field so the GET form submits the chosen genre.
  if (genreHiddenInput && selectedChip) {
    genreHiddenInput.value = selectedChip.dataset.genre || 'All';
  }
};

// ── Navbar ────────────────────────────────────────────────────────

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}

// ── Filter chips ──────────────────────────────────────────────────

if (genreFilterGroup) {
  genreChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      setActiveGenre(chip);
      // Submit the form so the chosen genre takes effect immediately
      // without forcing the user to click the separate Search button.
      const form = chip.closest('form');
      if (form) {
        form.submit();
      }
    });
  });
}

if (resetFiltersButton) {
  resetFiltersButton.addEventListener('click', () => {
    const allGenreChip = genreChips.find((chip) => chip.dataset.genre === 'All');

    if (allGenreChip) {
      setActiveGenre(allGenreChip);
    }

    if (releaseYearInput) {
      releaseYearInput.value = '';
    }

    if (minRatingSelect) {
      minRatingSelect.value = 'Any';
    }
  });
}

// ── Watchlist bookmark buttons ────────────────────────────────────

watchlistButtons.forEach((btn) => {
  btn.addEventListener('click', async (event) => {
    // The button sits inside an <article> whose entire surface links to
    // the movie detail page. Stop the click from bubbling up to that link.
    event.preventDefault();
    event.stopPropagation();

    const movieId = btn.dataset.movieId;
    if (!movieId) return;

    btn.disabled = true;
    const result = await postWatchlistAdd(movieId);
    if (result === null) return;

    if (result.ok) {
      btn.classList.add('search-card-watchlist-added');
      btn.setAttribute('aria-label', 'Already in watchlist');
      btn.title = result.data.already_added
        ? 'Already on your watchlist'
        : 'Added to your watchlist';
    } else {
      btn.disabled = false;
      const message = (result.data && result.data.error) || 'Could not update your watchlist.';
      window.alert(message);
    }
  });
});
