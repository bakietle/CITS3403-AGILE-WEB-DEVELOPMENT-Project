// Watchlist page interactions.
//
// The previous version of this file faked auth state via localStorage so
// the static prototype could toggle between guest / logged-in / empty /
// filled views. Now that the page is server-rendered with the actual
// watchlist items from the DB and gated by @login_required, that demo
// logic is dead weight and has been removed.
//
// The Remove button AJAX is wired up in the next commit.
