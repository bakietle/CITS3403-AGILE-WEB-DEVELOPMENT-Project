// Other user's profile page interactions.
//
// Two things this file does:
//   * Navbar scroll effect for visual polish.
//   * Follow / Unfollow toggle on the hero card, posting to
//     /user/<id>/follow or /unfollow and updating the visible follower
//     count from the server's authoritative response.
//
// CSRF: token is read from <meta name="csrf-token"> in the page head.

const navbar = document.getElementById('navbar');
const followButton = document.getElementById('follow-btn');
const followerCountEl = document.getElementById('follower-count');

// ── Helpers ────────────────────────────────────────────────────────

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

async function postFollow(action, userId) {
  // action is 'follow' or 'unfollow'.
  const response = await fetch(`/user/${userId}/${action}`, {
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
    // Not JSON.
  }
  return { ok: response.ok, status: response.status, data };
}

// ── Navbar ────────────────────────────────────────────────────────

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}

// ── Follow / Unfollow ──────────────────────────────────────────────

if (followButton) {
  followButton.addEventListener('click', async () => {
    const userId = followButton.dataset.userId;
    if (!userId) return;

    const isFollowing = followButton.classList.contains('is-following');
    const action = isFollowing ? 'unfollow' : 'follow';

    followButton.disabled = true;
    const result = await postFollow(action, userId);
    if (result === null) return;

    if (result.ok) {
      followButton.classList.toggle('is-following');
      followButton.textContent = isFollowing ? 'Follow' : 'Following';
      if (
        followerCountEl
        && typeof result.data.follower_count === 'number'
      ) {
        followerCountEl.textContent = result.data.follower_count;
      }
      followButton.disabled = false;
    } else {
      followButton.disabled = false;
      const message = (result.data && result.data.error)
        || 'Could not update your follow status.';
      window.alert(message);
    }
  });
}
