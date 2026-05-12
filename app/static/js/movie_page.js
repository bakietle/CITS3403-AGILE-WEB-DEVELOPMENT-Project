// Movie detail page interactions.
//
// This file handles:
//   * navbar scroll effect
//   * "Write a Review" CTA scrolls down to the review section
//   * "Add to Watchlist" button posts to /watchlist/add/<id> via AJAX
//   * Write-review form submits to /movie/<id>/review via AJAX
//   * Edit/Delete buttons on the user's own review (inline edit toggle,
//     delete with confirmation, both via AJAX)
//
// On a successful review action we reload the page rather than patch the
// DOM by hand. This keeps the JS small and guarantees the rendered state
// matches what the server actually persisted (e.g. created_at, edited
// timestamps, sort order).

const navbar = document.getElementById('navbar');
const writeReviewTrigger = document.getElementById('write-review-trigger');
const writeReviewSection = document.getElementById('write-review');
const watchlistButton = document.querySelector('.movie-cta[data-movie-id]');
const writeReviewForm = document.getElementById('write-review-form');
const editButtons = Array.from(document.querySelectorAll('.review-edit-btn'));
const deleteButtons = Array.from(document.querySelectorAll('.review-delete-btn'));
const editCancelButtons = Array.from(document.querySelectorAll('.review-edit-cancel'));
const editForms = Array.from(document.querySelectorAll('.review-edit-form'));

// ── Helpers ────────────────────────────────────────────────────────

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

async function postJson(url, options = {}) {
  // Wraps fetch() with CSRF + redirect-on-auth handling. The body is
  // expected to be FormData / URLSearchParams (the FlaskForm endpoints
  // read from request.form, not request.json).
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Accept': 'application/json',
      ...(options.headers || {}),
    },
    body: options.body,
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
    // Non-JSON response — leave data empty.
  }
  return { ok: response.ok, status: response.status, data };
}

async function postWatchlist(action, movieId) {
  return postJson(`/watchlist/${action}/${movieId}`);
}

function showError(message) {
  window.alert(message || 'Something went wrong. Please try again.');
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
    if (result === null) return;

    if (result.ok) {
      watchlistButton.textContent = result.data.already_added
        ? 'Already on Watchlist'
        : 'Added to Watchlist';
      watchlistButton.classList.add('movie-cta-success');
    } else {
      watchlistButton.disabled = false;
      showError((result.data && result.data.error) || 'Could not update your watchlist.');
    }
  });
}

// ── Write a new review (create) ───────────────────────────────────

if (writeReviewForm) {
  writeReviewForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitBtn = writeReviewForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    const result = await postJson(writeReviewForm.action, {
      body: new FormData(writeReviewForm),
    });
    if (result === null) return;

    if (result.ok) {
      // Reload so the server-rendered template re-runs with the new review.
      window.location.reload();
      return;
    }

    if (submitBtn) submitBtn.disabled = false;
    showError(result.data && result.data.error);
  });
}

// ── Edit own review (toggle inline form + submit) ─────────────────

function getEditForm(reviewId) {
  return document.querySelector(`.review-edit-form[data-review-id="${reviewId}"]`);
}

function getReviewCard(reviewId) {
  return document.querySelector(`.your-review-card[data-review-id="${reviewId}"]`);
}

function toggleEdit(reviewId, showForm) {
  const form = getEditForm(reviewId);
  const card = getReviewCard(reviewId);
  if (!form || !card) return;
  // Hide the display elements (everything in the card except the form)
  // while editing, and toggle the form's visibility.
  Array.from(card.children).forEach((child) => {
    if (child === form) {
      child.classList.toggle('hidden', !showForm);
    } else {
      child.classList.toggle('hidden', showForm);
    }
  });
}

editButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    toggleEdit(btn.dataset.reviewId, true);
  });
});

editCancelButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    toggleEdit(btn.dataset.reviewId, false);
  });
});

editForms.forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    const result = await postJson(form.action, {
      body: new FormData(form),
    });
    if (result === null) return;

    if (result.ok) {
      window.location.reload();
      return;
    }

    if (submitBtn) submitBtn.disabled = false;
    showError(result.data && result.data.error);
  });
});

// ── Delete own review (with confirmation) ─────────────────────────

deleteButtons.forEach((btn) => {
  btn.addEventListener('click', async () => {
    const reviewId = btn.dataset.reviewId;
    if (!reviewId) return;

    const confirmed = window.confirm(
      'Delete this review? This cannot be undone.'
    );
    if (!confirmed) return;

    btn.disabled = true;
    const result = await postJson(`/review/${reviewId}/delete`);
    if (result === null) return;

    if (result.ok) {
      window.location.reload();
      return;
    }

    btn.disabled = false;
    showError(result.data && result.data.error);
  });
});
