const navbar = document.getElementById('navbar');
const logoutButton = document.getElementById('other-profile-logout-btn');
const followButton = document.getElementById('follow-btn');
const followerCount = document.getElementById('follower-count');
const likeButtons = Array.from(document.querySelectorAll('[data-like-btn]'));
const loggedInNavLinks = Array.from(document.querySelectorAll('[data-auth-nav="logged-in"]'));

let isFollowing = false;

const preserveLoggedInState = () => {
  try {
    localStorage.setItem('movieStarDemoAuth', 'logged-in');
  } catch (error) {
    // Ignore storage failures in static preview.
  }
};

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}

if (logoutButton) {
  logoutButton.addEventListener('click', (event) => {
    event.preventDefault();

    try {
      localStorage.setItem('movieStarDemoAuth', 'guest');
    } catch (error) {
      // Ignore storage failures in static preview.
    }

    window.location.href = 'home_page.html';
  });
}

loggedInNavLinks.forEach((link) => {
  link.addEventListener('click', preserveLoggedInState);
});

if (followButton && followerCount) {
  followButton.addEventListener('click', () => {
    const currentFollowers = Number(followerCount.textContent);

    isFollowing = !isFollowing;
    followerCount.textContent = String(isFollowing ? currentFollowers + 1 : currentFollowers - 1);
    followButton.textContent = isFollowing ? 'Following' : 'Follow';
    followButton.classList.toggle('btn-ghost', isFollowing);
    followButton.classList.toggle('btn-primary', !isFollowing);
  });
}

likeButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const count = button.querySelector('.like-count');

    if (!count) {
      return;
    }

    const current = Number(count.textContent);
    const isLiked = button.classList.toggle('is-liked');
    count.textContent = String(isLiked ? current + 1 : current - 1);
  });
});
