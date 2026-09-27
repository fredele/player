function initDropdown(dropdownId, buttonId, menuId) {
  const dropdown = document.getElementById(dropdownId);
  const button = document.getElementById(buttonId);
  const menu = document.getElementById(menuId);

  if (!dropdown || !button || !menu) return;

  // Ouvrir / fermer au clic sur le bouton
  button.addEventListener('click', function (e) {
    e.stopPropagation();
    // Ferme les autres dropdowns ouverts (optionnel mais pratique)
    document.querySelectorAll('.dropdown-menu.show').forEach(m => {
      if (m !== menu) m.classList.remove('show');
    });
    menu.classList.toggle('show');
  });

  // Fermer si on clique ailleurs
  document.addEventListener('click', function () {
    menu.classList.remove('show');
  });

  // Empêcher la fermeture quand on clique dans le menu + fermer après clic sur un item
  menu.addEventListener('click', function (e) {
    // Si on clique sur un item (a, button, ou élément avec classe dropdown-item)
    if (e.target.closest('a, button, .dropdown-item')) {
      menu.classList.remove('show');
    }
    e.stopPropagation(); // empêche la fermeture immédiate par le document
  });
}

// Exemple d'utilisation
document.addEventListener('DOMContentLoaded', function () {
  initDropdown('playerDropdown', 'playerdropbtn', 'playerdrop');
  initDropdown('outputDropdown', 'outputgstdropbtn', 'outputgstdrop');
});
