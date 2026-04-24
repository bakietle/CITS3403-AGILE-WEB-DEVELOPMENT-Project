const navbar = document.getElementById('navbar');
const logoutButton = document.getElementById('my-profile-logout-btn');
const editProfileButton = document.getElementById('edit-profile-btn');
const editButtons = Array.from(document.querySelectorAll('[data-review-edit]'));
const deleteButtons = Array.from(document.querySelectorAll('[data-review-delete]'));
const loggedInNavLinks = Array.from(document.querySelectorAll('[data-auth-nav="logged-in"]'));

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

if (editProfileButton) {
  editProfileButton.addEventListener('click', () => {
    window.alert('Edit profile is not implemented in this prototype yet.');
  });
}

editButtons.forEach((button) => {
  button.addEventListener('click', () => {
    window.alert('Review editing is postponed in this simplified prototype.');
  });
});

deleteButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const reviewCard = button.closest('[data-review-card]');

    if (!reviewCard) {
      return;
    }

    const confirmed = window.confirm('Remove this review from the profile list?');

    if (confirmed) {
      reviewCard.remove();
    }
  });
});
