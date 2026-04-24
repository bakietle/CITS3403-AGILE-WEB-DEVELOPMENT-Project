const navbar = document.getElementById('navbar');
const genreChips = Array.from(document.querySelectorAll('.filter-chip'));
const genreFilterGroup = document.getElementById('genre-filter-group');
const releaseYearInput = document.getElementById('release-year');
const minRatingSelect = document.getElementById('min-rating');
const resetFiltersButton = document.getElementById('reset-filters-btn');

const setActiveGenre = (selectedChip) => {
  genreChips.forEach((chip) => {
    chip.classList.toggle('active', chip === selectedChip);
  });
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
