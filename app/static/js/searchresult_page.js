const navbar = document.getElementById('navbar');
const genreChips = Array.from(document.querySelectorAll('.filter-chip'));
const genreFilterGroup = document.getElementById('genre-filter-group');
const genreHiddenInput = document.getElementById('genre-hidden');
const releaseYearInput = document.getElementById('release-year');
const minRatingSelect = document.getElementById('min-rating');
const resetFiltersButton = document.getElementById('reset-filters-btn');
const loggedInNavLinks = Array.from(document.querySelectorAll('[data-auth-nav="logged-in"]'));

const setActiveGenre = (selectedChip) => {
  genreChips.forEach((chip) => {
    chip.classList.toggle('active', chip === selectedChip);
  });

  // Sync the hidden form field so the GET form submits the chosen genre.
  if (genreHiddenInput && selectedChip) {
    genreHiddenInput.value = selectedChip.dataset.genre || 'All';
  }
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

loggedInNavLinks.forEach((link) => {
  link.addEventListener('click', preserveLoggedInState);
});
