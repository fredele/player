function addLongPressListener(target, onShortPress, onLongPress, duration = 700) {
  const element = typeof target === 'string' ? document.querySelector(target) : target;
  if (!element) return;

  element.addEventListener('contextmenu', (e) => {
    e.preventDefault();
  });
  
  let pressTimer = null;
  let isLongPress = false;
  let lockClick = false; // Verrou anti-rebond pour la TV

  const startPress = (e) => {
    if (e.type === 'keydown') {
      if (e.key !== 'Enter' || e.repeat) return;
    }
    if (e.type === 'pointerdown' && e.button !== 0) return;

    isLongPress = false;

    pressTimer = setTimeout(() => {
      isLongPress = true;
      lockClick = true; // Activer le verrou lors de l'appui long
      if (typeof onLongPress === 'function') {
        onLongPress(e);
      }
    }, duration);
  };

  const cancelPress = (e) => {
    if (e.type === 'keyup' && e.key !== 'Enter') return;
    
    clearTimeout(pressTimer);

    // Si c'était un appui long, on garde le verrou quelques ms de plus
    // pour consommer le 'click' parasite envoyé par la TV au relâchement
    if (isLongPress) {
      setTimeout(() => {
        lockClick = false;
        isLongPress = false;
      }, 300); // 300ms de marge pour intercepter le clic de la TV
    }
  };

  const handleClick = (e) => {
    // Si l'appui long a eu lieu ou que le verrou TV est actif
    if (isLongPress || lockClick) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }

    if (typeof onShortPress === 'function') {
      onShortPress(e);
    }
  };

  // Événements Pointeur (Souris / Tactile)
  element.addEventListener('pointerdown', startPress);
  element.addEventListener('pointerup', cancelPress);
  element.addEventListener('pointerleave', cancelPress);
  element.addEventListener('pointercancel', cancelPress);

  // Événements Clavier (Télécommande / PC)
  element.addEventListener('keydown', startPress);
  element.addEventListener('keyup', cancelPress);

  // Clic final
  element.addEventListener('click', handleClick);
}