// Movie detail page interactions.
// The star-rating widget and write-review form will be added back by
// Module C when the review endpoints land. For now we only keep the
// navbar scroll effect and the "Write a Review" CTA that scrolls down
// to the placeholder review section.

const navbar = document.getElementById('navbar');
const writeReviewTrigger = document.getElementById('write-review-trigger');
const writeReviewSection = document.getElementById('write-review');

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}

if (writeReviewTrigger && writeReviewSection) {
  writeReviewTrigger.addEventListener('click', () => {
    writeReviewSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}
