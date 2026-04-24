const navbar = document.getElementById('navbar');
const logoutButton = document.getElementById('movie-logout-btn');
const writeReviewTrigger = document.getElementById('write-review-trigger');
const writeReviewSection = document.getElementById('write-review');
const starContainer = document.getElementById('star-container');
const stars = Array.from(document.querySelectorAll('.star-btn'));
const ratingLabel = document.getElementById('rating-label');
const loggedInNavLinks = Array.from(document.querySelectorAll('[data-auth-nav="logged-in"]'));

let selectedRating = 0;

const paintStars = (value) => {
  stars.forEach((star, index) => {
    star.classList.toggle('active', index < value);
  });
};

const preserveLoggedInState = () => {
  try {
    localStorage.setItem('movieStarDemoAuth', 'logged-in');
  } catch (error) {
    // Ignore storage failures in static preview and continue navigation.
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
      // Ignore storage failures in static preview and continue navigation.
    }

    window.location.href = 'home_page.html';
  });
}

loggedInNavLinks.forEach((link) => {
  link.addEventListener('click', preserveLoggedInState);
});

if (writeReviewTrigger && writeReviewSection) {
  writeReviewTrigger.addEventListener('click', () => {
    writeReviewSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

stars.forEach((star) => {
  star.addEventListener('mouseenter', () => {
    const value = Number(star.dataset.val);
    paintStars(value);

    if (ratingLabel) {
      ratingLabel.textContent = `${value} / 10`;
    }
  });

  star.addEventListener('click', () => {
    selectedRating = Number(star.dataset.val);
    paintStars(selectedRating);

    if (ratingLabel) {
      ratingLabel.textContent = `Selected: ${selectedRating} / 10`;
    }
  });
});

if (starContainer) {
  starContainer.addEventListener('mouseleave', () => {
    paintStars(selectedRating);

    if (ratingLabel) {
      ratingLabel.textContent = selectedRating ? `Selected: ${selectedRating} / 10` : 'Click to rate';
    }
  });
}
