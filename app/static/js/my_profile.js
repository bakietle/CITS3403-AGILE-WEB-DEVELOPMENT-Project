// My profile page interactions.
//
// All the demo localStorage / fake-auth logic that used to live here has
// been removed now that the page is server-rendered with real data and
// gated behind @login_required. The Edit Profile button is a plain link
// to /profile/edit so no JS is required for it either; this file just
// keeps the navbar scroll effect for visual polish.

const navbar = document.getElementById('navbar');

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  });
}
