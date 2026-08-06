
function loadScript(scriptUrl, callback) {
    const script = document.createElement('script');
    script.src = scriptUrl;
    script.type = 'text/javascript';
    script.async = true;

    // Appelé une fois que le script est chargé
    script.onload = function () {
        window.loadedscript = script;
        console.log(`Script chargé : ${scriptUrl}`);

        if (callback) callback();
    };

    script.onerror = function () {
        console.error(`Erreur lors du chargement du script : ${scriptUrl}`);
    };

    // Ajouter le script à la page
    document.head.appendChild(script);
}

document.addEventListener('DOMContentLoaded', function () {



    const timeTotal = document.getElementById('time_total');
    const timeElapsed = document.getElementById('time_elapsed');

    let showTimeout = null; // pour mémoriser un éventuel délai en attente

    const MaskTimeFields = () => {
        const total = timeTotal.innerHTML.trim();
        const elapsed = timeElapsed.innerHTML.trim();

        const shouldHide = total === "00:00:00" || elapsed === "00:00:00" || total === "" || elapsed === "";

        if (shouldHide) {
            // Si l’un est vide ou "00:00:00", on masque immédiatement
            if (showTimeout) {
                clearTimeout(showTimeout); // annuler une apparition prévue
                showTimeout = null;
            }
            timeElapsed.style.opacity = "0";
            timeTotal.style.opacity = "0";
        } else {
            // Si les deux ont une vraie valeur, on attend 1 seconde avant d’afficher
            if (!showTimeout) {
                showTimeout = setTimeout(() => {
                    timeElapsed.style.opacity = "1";
                    timeTotal.style.opacity = "1";
                    showTimeout = null;
                }, 2000);
            }
        }
    };

    // Observer les changements sur les deux éléments
    const observer = new MutationObserver(MaskTimeFields);
    observer.observe(timeTotal, { childList: true, subtree: true, characterData: true });

    const observer1 = new MutationObserver(MaskTimeFields);
    observer1.observe(timeElapsed, { childList: true, subtree: true, characterData: true });

    // Appel initial
    MaskTimeFields();

    
    
    
    
    const timeSpacer = document.getElementById('time_spacer');
    if (timeSpacer) {
        const observer = new MutationObserver(function () {
            if (timeSpacer.innerHTML === '<span class="extension" style="text-decoration: none;"></span><span class="bitrate" style="text-decoration: none;"></span>') {
                timeSpacer.style.opacity = "0";
            } else {
                timeSpacer.style.display = "flex";
            }
        });
        observer.observe(timeSpacer, { childList: true, subtree: true, characterData: true });
        // Initial check
        if (timeSpacer.innerHTML === "") {
            timeSpacer.style.display = "none";
        }
    } 

    dropdownElements = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElements.forEach(function (dropdown) {
        try {
            new bootstrap.Dropdown(dropdown);
        } catch { }
    });

    // Initialise les valeurs de la boite de recherche
    let valeurs = localStorage.getItem("query_tags");
    if (valeurs && valeurs.trim() !== "") {
        valeurs = valeurs.split(';').filter(item => item !== "");
    } else {
        valeurs = [];
    }
    const datalist = document.getElementById("mylist");
    
    try{
        if (isCordova()) {
        
            if (navigator.splashscreen && navigator.splashscreen.hide) {
                navigator.splashscreen.hide();
            }

            if (window.StatusBar) { StatusBar.hide(); }

        }
        }catch(error) {}

 
    if (localStorage.getItem("current_player") !== null) {

        c = localStorage.getItem("current_player");

        if (c !== "here") {
            window.current_player = JSON.parse(c);
            loadScript("js/browse.js", function () { loadScript("js/browse_players.js", function () { onload_browse(); }); });
        } else { //si here

            if (isCordova()) {
                loadScript("js/browse.js", function () { loadScript("js/browse_cordova.js", function () { onload_browse(); window.dispatchEvent(new Event('resize')); }); });
            } else {
                loadScript("js/browse.js", function () { loadScript("js/browse_web.js", function () { onload_browse(); window.dispatchEvent(new Event('resize')); }); });
            }

        }
    } else // si pas de précédent player
    {
        if (getExecutionContext() == "internet") {
            loadScript("js/browse.js", function () { loadScript("js/browse_web.js", function () { onload_browse(); window.dispatchEvent(new Event('resize')); }); });
        }
        else { loadScript("js/browse.js", function () { loadScript("js/browse_players.js", function () { onload_browse(); window.dispatchEvent(new Event('resize')); }); }); }
    }
});


document.addEventListener("beforeunload", function () {
    if (mediaPlayer) {
        mediaPlayer.pause();
        mediaPlayer.release();
        mediaPlayer = null;
    }
});
