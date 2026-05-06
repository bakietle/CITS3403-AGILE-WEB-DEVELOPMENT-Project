document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
  const formPanels = Array.from(document.querySelectorAll('.form-panel'));
  const tabLinks = Array.from(document.querySelectorAll('.tab-link'));

  function switchTab(target) {
    if (!target) return;

    tabButtons.forEach(button => {
      const isActive = button.dataset.target === target;
      button.classList.toggle('active', isActive);
    });

    formPanels.forEach(panel => {
      const isActive = panel.id === `panel-${target}`;
      panel.classList.toggle('active', isActive);
    });
  }

  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      switchTab(button.dataset.target);
    });
  });

  tabLinks.forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      switchTab(link.dataset.target);
    });
  });

  const initialTab = tabButtons.find(button => button.classList.contains('active'))?.dataset.target || 'login';
  switchTab(initialTab);
});
