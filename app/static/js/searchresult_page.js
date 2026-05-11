// Search results page interactions.
// Filter chips, year input, and min-rating select all live inside a single
// GET <form>. Genre chips also sync a hidden input so the form submits the
// chosen genre, and clicking a chip auto-submits the form for instant
// feedback. Reset button restores defaults without submitting.

const navbar = document.getElementById('navbar');
const genreChips = Array.from(document.querySelectorAll('.filter-chip'));
const genreFilterGroup = document.getElementById('genre-filter-group');
const genreHiddenInput = document.getElementById('genre-hidden');
const releaseYearInput = document.getElementById('release-year');
const minRatingSelect = document.getElementById('min-rating');
const resetFiltersButton = document.getElementById('reset-filters-btn');

const setActiveGenre = (selectedChip) => {
  genreChips.forEach((chip) => {
    chip.classList.toggle('active', chip === selectedChip);
  });

  // Sync the hidden form field so the GET form submits the chosen genre.
  if (genreHiddenInput && selectedChip) {
    genreHiddenInput.value = selectedChip.dataset.genre || 'All';
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
