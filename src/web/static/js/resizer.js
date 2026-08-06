function applyZoomByResolution() {

  const width = window.innerWidth;
  const height = window.innerHeight;
  // Calcul du ratio pour ajuster le zoom
  zoom = 0.6 + 0.4 * (width / 1500);
  document.body.style.zoom = zoom;

  if (document.getElementById('playlist_container') != null) {

    var playlist_container_width = window.getComputedStyle(document.getElementById('playlist_container')).width;
    var playlist_container_height = window.getComputedStyle(document.getElementById('playlist_container')).height;

    ratio = parseFloat(playlist_container_width) / parseFloat(playlist_container_height);

    if (ratio < 1) {
      // Si le ratio est inférieur à 1, on est en mode portrait
      document.getElementById('left_panel').classList.add('portrait');
      document.getElementById('left_panel').classList.remove('landscape');
      document.getElementById('right_panel').classList.add('portrait');
      document.getElementById('right_panel').classList.remove('landscape');
    }
    else {
      // Si le ratio est supérieur ou égal à 1, on est en mode paysage
      document.getElementById('left_panel').classList.add('landscape');
      document.getElementById('left_panel').classList.remove('portrait');
      document.getElementById('right_panel').classList.add('landscape');
      document.getElementById('right_panel').classList.remove('portrait');
    }
  }
}

// Appel au chargement et au redimensionnement
window.addEventListener('DOMContentLoaded', applyZoomByResolution);
window.addEventListener('resize', applyZoomByResolution);
