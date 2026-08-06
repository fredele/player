// Contains vars  ....

// Write default values function
function get_local_var(variable, init_variable) {
  if (localStorage.getItem(variable) == null) {
    localStorage.setItem(variable, init_variable);
  }
}

// Write  values function
function set_local_var(variable, init_variable) {
  localStorage.setItem(variable, init_variable);
}

function setup_init_vars() {
  // Write all the default values for initialisation
  if (getExecutionContext() == "internet") {
    get_local_var("username", "user");
  }
  else {
    get_local_var("username", "admin");
  }
  get_local_var("password", "password");
  set_local_var("format_info", '<span class="extension">$extension$</span><span class="bitrate">*$bitrate$*</span>');
  get_local_var("thumb_width", "140");
  get_local_var("thumb_nbrs", "1500");
  get_local_var("font_size", "14");
  get_local_var("sideimage_width", "800");
  get_local_var("menu_file", "control_views");
  get_local_var("query_tags", "artist;album;date;genre;subgenre;instrument;composer;conductor;performer;organization;catalogserie;catalognumber;wikipedia;allmusic;discogs;compilation;extension;title;discnumber;tracknumber");
  get_local_var("singlevalue", "mediatype;last_modified;date_imported;dirname;dirhash;filename;title;cover;extension;date;album;catalognumber;catalogserie;discnumber;tracknumber");
  get_local_var("noneditable", "extension;last_modified;date_imported;dirname;dirhash");
  get_local_var("current_track_info", "$title$<br>$album$ / $artist$ $performer$");
  get_local_var("query_track_info", "$trackdiscnumber$ - $title;filename$ / $composer$");
  get_local_var("query_album_info", "$album$<br>$artist$<br>$date$");
  get_local_var("queue_track_info", "$trackdiscnumber$ - $title;filename$ / $composer$");
  get_local_var("track_info_1", "$album$<br>$artist$<br>$date$<br>$performer$<br>$conductor$<br>$composer$");

  window.translations =
    { "main window thumbnail size :": "Taille des Miniatures", "artwork images display resolution :": "Taille des Images de Pochette", "tags": "Etiquettes", "tags to query:": "Etiquettes à requêter", "single value tags :": "Etiquettes à valeur unique", "non editable tags in the query view :": "Etiquettes non éditables", "view": "Vues", "main view": "Vue Principale", "track info in the player bar :": "Information de piste dans la Barre du Player", "individual track info in the query View :": "Information de piste dans la vue", "query view": "Vue Requête", "query info at the top of the query view :": "Informations descriptives", "queue view": "Vue Playliste de Lecture", "individual track info in the queue view :": "Information de piste", "track info in the queue view :": "Information de piste sous l' image", "translation": "Traductions", "interface translation": "Traduction de l' interface", "save": "Enregistrer", "Scan Folders": "Scanner les Dossiers", "Scan New Folders": "Scanner les Nouveaux Dossiers", "Backup Library": "Sauvegarder la Librairie", "Restore Library": "Restaurer la Librairie", "Clear Queries": "Effacer les Requêtes", "Browse": "Naviguer", "Output": "Sortie", "Display": "Affichage", "Control": "Contrôle", "Login": "Connexion", "Database": "Librairie", "Shutdown": "Eteindre", "dirhash": "ID Album", "path": "chemin", "library": "Librairie", "composer": "compositeur", "composer_invert": "compositeur", "conductor": "chef d' orchestre", "conductor_invert": "chef d' orchestre", "artist": "artiste", "Jazz_Standard": "standard de jazz", "performer": "orchestre", "organization": "label", "catalogserie": "série du catalogue", "catalognumber": "numéro du catalogue", "subgenre": "style", "album_alphabet": "albums (A..Z)", "artist_alphabet": "artistes (A..Z)", "date_decade": "décade", "date": "année", "extension": "format", "group_artist": "artiste", "group_album": "album", "Discnumber": "Disque N°", "Update": "Mettre à Jour depuis les Fichiers", "Tag": "Etiquette", "Value": "Valeur", "title": "titre", "Rip": "Ripper", "tracknumber": "piste n°", "Settings": "Paramètres", "discnumber": "disque n°", "Choose an Output": "Choisissez une sortie", "Choose a Player": "Choisissez un lecteur", "searching players": "recherche des players", "No Connection": "Pas de connexion avec le serveur", "download from server": "téléchargez depuis le serveur", "back": "retour", "search": "rechercher", "here": "ici" }

  if (localStorage.getItem('translations') === null) {
    localStorage.setItem('translations', JSON.stringify(translations));
  }
}

function read_vars() {

  window.menu_file = localStorage.getItem("menu_file");
  window.query_track_info = localStorage.getItem("query_track_info");
  window.track_info_1 = localStorage.getItem("track_info_1");
  window.format_info = localStorage.getItem("format_info");
  window.queue_track_info = localStorage.getItem("queue_track_info");
  window.query_album_info = localStorage.getItem("query_album_info");
  window.current_track_info = localStorage.getItem("current_track_info");
  window.query_tags = localStorage.getItem("query_tags");
  window.singlevalue = localStorage.getItem("singlevalue");
  window.noneditable = localStorage.getItem("noneditable");
  val = localStorage.getItem("translations");
  try {
    window.translations = JSON.parse(val);
  } catch (error) { window.translations = {} }
  window.translations = lowerize(translations);
  iw = localStorage.getItem("sideimage_width")
  window.sideimage_width = iw;
  //pass
}

lowerize = obj =>
  Object.keys(obj).reduce((acc, k) => {
    acc[k.toLowerCase()] = obj[k];
    return acc;
  }, {});

function translate(word) {
  try {
    if (word.toLowerCase() in window.translations) {
      return translations[word.toLowerCase()].toLowerCase();
    } else {
      return word.toLowerCase();
    }
  } catch { }

}

