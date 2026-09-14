// Can uses this here
if (cordova.platformId === 'android') {
  isAndroid = true;
  var VolumeControl = cordova.plugins.VolumeControl;
}
else
{
  isAndroid = false;
}



function after_Player_CurrentPosition() { }

function mediaStatusCallback() { }

// déplace un élément dans le tableau de queue
function local_queue_move(oldIndex, newIndex) {
  if (oldIndex === newIndex || oldIndex < 0 || newIndex < 0) return;
  const item = queue.splice(oldIndex, 1)[0];
  queue.splice(newIndex, 0, item);
}

// supprime un élément
function local_queue_delete(index) {
  if (index < 0 || index >= queue.length) return;
  queue.splice(index, 1);
}

function playlist_item_dragend_local(e) {
  document.getElementById('playlist_item_delete_img').style.display = "none";
  console.log(this);

  // dragstart_nbr et dragend_nbr sont utilisées comme dans ton code existant
  if (dragstart_nbr != dragend_nbr && dragend_nbr != -1) {
    local_queue_move(parseInt(dragstart_nbr, 10), parseInt(dragend_nbr, 10));
    Fill_Queue() // réaffiche la queue après déplacement
  }
  if (dragend_nbr == -1) {
    local_queue_delete(parseInt(dragstart_nbr, 10));
    Fill_Queue() // réaffiche après suppression
    document.getElementById('playlist_item_delete_img').style.backgroundColor = "#0000001a";
  }
}

function Fill_Queue() {

  var playliste = document.getElementById('playlist');
  playliste.innerHTML = "";
  var sumt = 0;


  var playlist_content = "";
  for (var i = 0; i < queue.length; i++) {
    track = queue[i];

    if (i == current_playing_position) {
      playingimg = "img/volume.png"
    } else {
      playingimg = "img/transparent.png"
    }
    title = track["display"];

    if ("dirhash" in track) {
      if (updatedimages.indexOf(track["dirhash"]) >= 0) {
        imgurl = Server_Get_ThumbUrl(track["dirhash"]);
      } else {
        imgurl = Server_Get_ThumbUrl(track["dirhash"]);
      }

    } else if ("covers" in track) {
      imgurl = track["covers"][0];
    } else {
      imgurl = "img/cd.png";
    }

    t = track["length"] * 1000;
    sumt = sumt + t;

    time = MsToMMSS(t);
    draggable = `draggable="true"`;
    playlist_content = playlist_content +
      `
      <div ` + draggable + ` class="playlist_item" nbr="${i}" idnbr="${track["_id"]}"  >
      <img id= "" class="item_cover" src="${imgurl}" loading="lazy"  onerror="this.src='img/cd.png'"   > 
      <div class="item_title_1"  >${title}</div>
      <img id= "" class="item_playing" src="${playingimg}" loading="lazy"   >
      <div class="item_time" onclick="change_track(${i})">${time}</div>
      </div>

    `;

  } // End for
  playliste.innerHTML = playlist_content;
  var playlist_items = document.querySelectorAll('.playlist_item');
  playlist_items.forEach(function (item) {
    item.addEventListener('dragstart', playlist_item_dragstart);
    item.addEventListener('dragend', playlist_item_dragend_local);
    item.addEventListener('dragleave', playlist_item_dragleave);
    item.addEventListener('dragenter', playlist_item_dragenter);
  }); // End foreach

}


function play_radio(thumb) {
  document.getElementById('time_spacer').innerHTML = '<span class="extension" style="text-decoration: none;"></span><span class="bitrate" style="text-decoration: none;"></span>';
  window.position = 0;
  window.duration = 0;
  url = thumb.getAttribute("url");
  cover = thumb.getAttribute("covers");
  title = thumb.getAttribute("title");
  length = 0;
  //url =  encodeURI(url);
  if (mediaplayer) {
    mediastop = true;
    mediaplayer.stop(); // Arrête la lecture actuelle
    mediaplayer.release(); // Libère les ressources associées à cet objet
  }

  // Créer un nouvel objet avec la nouvelle source
  console.log("Media:");
  console.log(Media);
  mediaplayer = new Media(url,
    function () {
      console.log("Lecture terminée avec succès.");
      end_of_stream();
    },
    function (err) {
      console.error("Erreur :", err);
    },
    mediaStatusCallback
  );

  // Démarrer la lecture du nouveau fichier audio
  mediaplayer.play();
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.innerHTML = "Play"
  });
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/play.png"
  });
  queue = []
  queue.push({
    "url": url,
    "covers": [cover],
    "title": title,
    "display": title,
    "length": 0
  });
  Fill_Queue();
  current_playing_position = 0;
  queue_position = current_playing_position;
  Set_Covers_addr(encodeURI(cover));
  Array.from(document.getElementsByClassName('display_str')).forEach(el => {
    el.innerHTML = title;
  })
  Array.from(document.getElementsByClassName('current_track_infos')).forEach(el => {
    el.innerHTML = title;
  })
  window.playing = true;
}


function after_play_radio() {
  //TODO: Erase playlist
}


function play_podcast(thumb) {
  document.getElementById('time_spacer').innerHTML = '<span class="extension" style="text-decoration: none;"></span><span class="bitrate" style="text-decoration: none;"></span>';
  url = thumb.getAttribute("url");
  cover = thumb.getAttribute("covers");
  title = thumb.getAttribute("title");
  length = thumb.getAttribute("length"); // In seconds ...
  window.duration = parseInt(length) * 1000;

  if (mediaplayer) {
    mediastop = true;
    mediaplayer.stop(); // Arrête la lecture actuelle
    mediaplayer.release(); // Libère les ressources associées à cet objet
  }

  // Créer un nouvel objet avec la nouvelle source
  console.log("Media:");
  console.log(Media);
  mediaplayer = new Media(url,
    function () {
      console.log("Lecture terminée avec succès.");
      end_of_stream();
    },
    function (err) {
      console.error("Erreur :", err);
    },
    mediaStatusCallback
  );

  // Démarrer la lecture du nouveau fichier audio
  mediaplayer.play();
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.innerHTML = "Play"
  });
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/play.png"
  });
  queue = []
  queue.push({
    "url": url,
    "covers": [cover],
    "title": title,
    "display": title,
    "length": length
  });
  Fill_Queue();
  current_playing_position = 0;
  queue_position = current_playing_position;
  Set_Covers_addr(cover);
  Array.from(document.getElementsByClassName('display_str')).forEach(el => {
    el.innerHTML = title;
  })
  Array.from(document.getElementsByClassName('current_track_infos')).forEach(el => {
    el.innerHTML = title;
  })
  window.playing = true;
}

function after_play_podcast() {

  //TODO: Erase playlist
}


function set_addr(track) {

  if (!isCordova()) {
    document.getElementById('activate_streaming').disabled = true;
    localStorage.setItem("web_transcode_active", true);
    document.getElementById('activate_streaming').checked = true;
    web_transcode_active = true;
  }
  else {
    web_transcode_active = localStorage.getItem("web_transcode_active") === "true";
  }
  if (web_transcode_active === true) {
    // Route actuelle (compatibilité si besoin) : /v1/Transcode/<codec>/<bitrate>/<fileid>.<extension>
    const trackExt = (track.extension || (track.file || "track.mp3").split('.').pop() || "mp3");
    track["file_addr"] = window.serverurl + "/v1/Transcode/" + web_codec + "/" + web_bitrate + "/" + track["_id"] + "." + trackExt;
  }
  return track["file_addr"];
}


function end_of_stream() {
  if (mediastop == true) {
    mediastop = false;
    return;
  }


  if (document.getElementById("playerdropbtn").innerHTML != translate("Here")) {
    return;
  };
  console.log("End of this file !")
  current_playing_position += 1;
  queue_position = current_playing_position;
  try {
    addr = set_addr(queue[current_playing_position]);
  } catch {
    // End of playlist
    document.getElementById("current_track_infos").innerHTML = "";
    document.getElementById("time_total").innerHTML = "";
    document.getElementById("time_elapsed").innerHTML = "";
  };
  window.duration = 1000 * parseFloat(queue[current_playing_position]["length"])
  document.getElementById('time_total').innerHTML = MsToMMSS(1000 * parseFloat(queue[current_playing_position]["length"]));
  calc_queueelapse();



  // Créer un nouvel objet avec la nouvelle source
  mediaplayer = new Media(addr,
    function () {
      console.log("Lecture terminée avec succès.");
      end_of_stream();
    },
    function (err) {
      console.error("Erreur :", err);
    },
    mediaStatusCallback
  );
  // Démarrer la lecture du nouveau fichier audio
  mediaplayer.play();
  window.current_id = queue[current_playing_position]["_id"]

  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.innerHTML = "Play"
  });
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/play.png"
  });
  setTimeout(() => {
    mark_track();
  }, 500);
}


function query_play() {

  if (current_selected_ids.length > 0) {
    queue = []
    for (var i = 0; i < files_queried.length; i++) {
      if (current_selected_ids.includes(files_queried[i]["_id"])) {
        queue.push(files_queried[i]);
      }
    }
  } else {
    queue = files_queried
  }
  Fill_Queue()
  reset_query_container()
  current_playing_position = 0;
  queue_position = current_playing_position;
  addr = set_addr(queue[current_playing_position]);
  addr = encodeURI(addr);

  console.log(addr);
  window.duration = 1000 * parseFloat(queue[current_playing_position]["length"])
  document.getElementById('time_total').innerHTML = MsToMMSS(1000 * parseFloat(queue[current_playing_position]["length"]));
  calc_queueelapse();
  if (mediaplayer) {
    mediastop = true;
    mediaplayer.stop(); // Arrête la lecture actuelle
    mediaplayer.release(); // Libère les ressources associées à cet objet
  }

  // Créer un nouvel objet avec la nouvelle source
  console.log("Media:");
  console.log(Media);
  mediaplayer = new Media(addr,
    function () {
      console.log("Lecture terminée avec succès.");
      end_of_stream();
    },
    function (err) {
      console.error("Erreur :", err);
    },
    mediaStatusCallback
  );
  // Démarrer la lecture du nouveau fichier audio
  mediaplayer.play();
  window.current_id = queue[current_playing_position]["_id"]

  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.innerHTML = "Play"
  });
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/play.png"
  });

  setTimeout(() => {
    mark_track();
  }, 2000);
  ///////
  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";
  playing = true;
}

function query_queue() {



  if (current_selected_ids.length > 0) {
    for (var i = 0; i < files_queried.length; i++) {
      if (current_selected_ids.includes(files_queried[i]["_id"])) {
        queue.push(files_queried[i]);
      }
    }
  } else {
    queue = queue.concat(files_queried);
  }
  Fill_Queue()
  reset_query_container()
  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";
  calc_queueelapse();
}



function Play() {


  playing = window.playing
  if (playing == true) {
    if (mediaplayer) {
      mediaplayer.pause();
    }
    playing = false;
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.innerHTML = "Pause"
    });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/pause.png"
    });
  } else {
    if (mediaplayer) {
      mediaplayer.play();
    }
    playing = true;
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.innerHTML = "Play"
    });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/play.png"
    });
  }
}

function Next() {
  if (current_playing_position < queue.length - 1) {
    current_playing_position += 1;
    queue_position = current_playing_position;
    addr = set_addr(queue[current_playing_position]);
    window.duration = 1000 * parseFloat(queue[current_playing_position]["length"])
    document.getElementById('time_total').innerHTML = MsToMMSS(1000 * parseFloat(queue[current_playing_position]["length"]));


    addr = encodeURI(addr);
    if (mediaplayer) {
      mediastop = true;
      mediaplayer.stop(); // Arrête la lecture actuelle
      mediaplayer.release(); // Libère les ressources associées à cet objet
    }

    // Créer un nouvel objet avec la nouvelle source
    console.log("Media:");
    console.log(Media);
    mediaplayer = new Media(addr,
      function () {
        console.log("Lecture terminée avec succès.");
        end_of_stream();
      },
      function (err) {
        console.error("Erreur :", err);
      },
      mediaStatusCallback
    );

    // Démarrer la lecture du nouveau fichier audio

    mediaplayer.play();
    window.current_id = queue[current_playing_position]["_id"]

    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.innerHTML = "Play"
    });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/play.png"
    });
    calc_queueelapse();
    setTimeout(() => {
      mark_track();
    }, 500);
    each5second();
  }
}

function Previous() {
  if (current_playing_position > 0) {
    current_playing_position -= 1;
    queue_position = current_playing_position;
    addr = set_addr(queue[current_playing_position]);
    window.duration = 1000 * parseFloat(queue[current_playing_position]["length"])
    document.getElementById('time_total').innerHTML = MsToMMSS(1000 * parseFloat(queue[current_playing_position]["length"]));



    addr = encodeURI(addr);
    if (mediaplayer) {
      mediastop = true;
      mediaplayer.stop(); // Arrête la lecture actuelle
      mediaplayer.release(); // Libère les ressources associées à cet objet
    }

    // Créer un nouvel objet avec la nouvelle source
    console.log("Media:");
    console.log(Media);
    mediaplayer = new Media(addr,
      function () {
        console.log("Lecture terminée avec succès.");
        end_of_stream();
      },
      function (err) {
        console.error("Erreur :", err);
      },
      mediaStatusCallback
    );

    // Démarrer la lecture du nouveau fichier audio
    mediaplayer.play();
    window.current_id = queue[current_playing_position]["_id"]

    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.innerHTML = "Play"
    });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/play.png"
    });
    calc_queueelapse();
    setTimeout(() => {
      mark_track();
    }, 500);
    each5second();
  }
}

function volume_show() {
  if (isAndroid) {
  VolumeControl.getVolume(
    function (vol) {
      console.log("Volume actuel de l'appareil :", vol);
      vol = vol * 100;
      document.getElementById("volume-progress-bar").style.width = String(vol) + "%";
    },
    function (err) {
      console.error("Erreur lors de la récupération du volume :", err);
    }
  );

  document.getElementById("volume_background").style.width = "100%";
  document.getElementById("volume_background").style.height = "100%";
  document.getElementById("volume_container").style.width = "100%";
  document.getElementById("volume_container").style.height = "20px";
  document.getElementById("volume_background_top").style.width = "100%";
  document.getElementById("volume_background_bottom").style.width = "100%";
  }

}



function getMousePosition(canvas, event) {
  let pos = event.clientX /  window.innerWidth;
  VolumeControl.setVolume(pos);
  pos = Math.round(pos * 100);
  document.getElementById("volume-progress-bar").style.width = String(pos) + "%";
}

function on_ws_msg(data) {
  if (typeof data === 'string') {
    if (data.startsWith("#") == true) {
      return;
    }
  }
  if (typeof data === 'string') {
    if (data.startsWith("##") == true) {
      return;
    }
  }

  if ("message" in data) {
    var msg = data["message"];
    var val = data["value"];

    if (msg == "auto import") {
      clearTimeout(myTimeOut);
      document.getElementById('scanning_img').style.opacity = 1;
      myTimeOut = setTimeout(function () {
        document.getElementById('scanning_img').style.opacity = 0;
      }, 3000);
    }

    if (msg == "Update Library") {
      document.getElementById('scanning_img').style.opacity = 1;
      window.scanning = true;
      sessionStorage.setItem("Library Updating", "true");
    }

    if (msg == "Library Updated") {
      document.getElementById('scanning_img').style.opacity = 0;
      sessionStorage.setItem("Library Updating", "false");
      window.scanning = false;
      Server_Get_UpdatedImages(after_Get_UpdatedImages)
    }

    if (msg == "Cover changed") {
      Server_Get_UpdatedImages(after_Get_UpdatedImages)
    }

  }
}

function change_track(nbr) {
  event.stopPropagation();
  current_playing_position = nbr;
  queue_position = nbr;
  addr = set_addr(queue[current_playing_position]);
  addr = encodeURI(addr);
  window.duration = 1000 * parseFloat(queue[current_playing_position]["length"])
  document.getElementById('time_total').innerHTML = MsToMMSS(1000 * parseFloat(queue[current_playing_position]["length"]));
  calc_queueelapse();


  if (mediaplayer) {
    mediastop = true;
    mediaplayer.stop(); // Arrête la lecture actuelle
    mediaplayer.release(); // Libère les ressources associées à cet objet
    window.position = 0;
    let hhmmssposition = MsToMMSS(window.position)
    document.getElementById('time_elapsed').innerHTML = hhmmssposition;
  }

  // Créer un nouvel objet avec la nouvelle source
  console.log("Media:");
  console.log(Media);
  mediaplayer = new Media(addr,
    function () {
      console.log("Lecture terminée avec succès.");
      end_of_stream();
    },
    function (err) {
      console.error("Erreur :", err);
    },
    mediaStatusCallback
  );
  window.current_id = queue[current_playing_position]["_id"]
  // Démarrer la lecture du nouveau fichier audio
  mediaplayer.play();
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.innerHTML = "Play"
  });
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/play.png"
  });


  setTimeout(() => {
    mark_track();
  }, 500);
  each5second();

}

function after_Server_Player_Id() {
  res = JSON.parse(this.response);
}

function each5second() {

  if (mediaplayer) {
    mediaplayer.getCurrentPosition(
      // success callback
      function (pos) { // en secondes
        window.position = pos * 1000;
      },
      // error callback
      function (e) {
        console.log("Error getting position");
        window.position = 0;
      }
    );

  }


  if (window.playing == true) {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.innerHTML = "Play"
    });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/play.png"
    });
  } else {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.innerHTML = "Pause"
    });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/pause.png"
    });
  }




  if (window.playing == true) {
    if (window.position <= window.duration) {

      if (flipflopelapsedbool == false) {
        let hhmmssposition = MsToMMSS(window.position);
        document.getElementById('time_elapsed').innerHTML = hhmmssposition;
        
      } else {
        let hhmmssposition = MsToMMSS(window.position + queueelapse);
        document.getElementById('time_elapsed').innerHTML = hhmmssposition;
       
      }
    }
  }

  if (window.duration != undefined) {
    if (MsToMMSS(window.duration) != "") {

      if (flipflopelapsedbool == false) {
        document.getElementById.innerHTML = MsToMMSS(window.duration);
       
      } else {
        document.getElementById.innerHTML = MsToMMSS(queuetot);
     
      }

    }
  } else {
    document.getElementById('time_elapsed').innerHTML = "";
  
  }
 Server_Scanning(after_Scanning, null);
}

function onload_browse() {

  if (localStorage.hasOwnProperty('web_transcode_codec')) {

  } else {
    localStorage.setItem('web_transcode_codec', 'mp3');
  }

  if (localStorage.hasOwnProperty('web_transcode_bitrate')) {
  } else {
    localStorage.setItem('web_transcode_bitrate', '128');
  }

  if (localStorage.hasOwnProperty('web_transcode_active')) {

    document.getElementsByTagName("web_transcode_active").value = localStorage.getItem("web_transcode_active") === "true";
  } else {
    localStorage.setItem('web_transcode_active', false);
  }


  if (!isCordova()) {
    document.getElementById('activate_streaming').disabled = true;
    document.getElementById('activate_streaming').checked = true;
    web_transcode_active = true;
  }



  if (localStorage.hasOwnProperty('serverurl')) {
    window.serverurl = localStorage.getItem('serverurl')
  } else {
    window.location.href = window.current_address + "config.html";
  }

  var elementToChange = document.getElementsByTagName("body")[0];
  cu = 'img/cursor.png';
  elementToChange.style.cursor = cu;

  makeUnselectable(document.getElementById("query_image_img_div"));
  makeUnselectable(document.getElementById("query_cover_big_container"));
  makeUnselectable(document.getElementById("query_tracklist"));
  makeUnselectable(document.getElementById("query_topheader"));
  makeUnselectable(document.getElementById("bigcoverimg"));
  makeUnselectable(document.getElementById("playlist_cover"));
  makeUnselectable(document.getElementById("time_display"));
  sessionStorage.setItem("browse_page", document.URL);

  if (localStorage.hasOwnProperty('thumb_nbrs')) {
    req_thumb_cout = parseInt(localStorage.getItem('thumb_nbrs'));
    if (req_thumb_cout < 10) {
      req_thumb_cout = 1500
    }
  }

  function stop() {
    event.preventDefault();
    event.stopPropagation();
    return false;
  }

  window.oncontextmenu = function (event) {
    s = event.srcElement.src;
    if (s.includes("play.png")) {
      stop();
    }
    if (s.includes("pause.png")) {
      stop();
    }
    if (s.includes("volume.png")) {
      stop();
    }
    if (s.includes("next.png")) {
      stop();
    }
    if (s.includes("previous.png")) {
      stop();
    }

  }


  levelcanvas = document.getElementById('level');
  spectrumcanvas = document.getElementById('spectrum');
  setup_init_vars();
  translateUI();
  document.getElementById('search_span').innerHTML = translate("Search");
  document.getElementById('search_btn').value = translate("Search");


  singlevalue = singlevalue.split(";")
  noneditable = noneditable.split(";")

  document.getElementById('editor1').innerHTML = translate("Tag") + " :";
  document.getElementById('editor2').innerHTML = translate("Value") + " :";
  document.getElementById('button_set_value').value = translate("save");
  document.getElementById("playerdropbtn").innerHTML = translate("Here");
  document.getElementById("chooseoutput").style.display = "none";

  window.ui = "active"

  updating = sessionStorage.getItem('Library Updating');
  if (updating == "true") {
    document.getElementById('scanning_img').style.opacity = 1;
  }

  // Get the modals
  window.tageditormodal = document.getElementById("TagEditorModal");
  window.searchmodal = document.getElementById("SearchBoxModal");

  window.outputmodal = document.getElementById("OutputModal");

  window.onclick = function (event) {

    if (event.target == searchmodal) {
      searchmodal.style.display = "none";
      typing = false;
    }
    if (event.target == window.tageditormodal) {
      window.tageditormodal.style.display = "none";
      document.getElementById('button_set_value').disabled = true;
    }

    if (event.target == window.outputmodal) {
      window.outputmodal.style.display = "none";

    }

  }




  window.current_address = window.serverurl;

  // Load the menu in the URL args
  var args = getJsonFromUrl(window.current_address);
  if ("menu_file" in args) {
    menu_file = args["menu_file"];
  }
  if ("thumb_style" in args) {
    thumb_style = args["thumb_style"];
  }


  document.getElementById("volume-progress-bar-background").addEventListener("click", function (e) {
    getMousePosition(document.getElementById("volume-progress-bar-background"), e);
  });
  document.getElementById("volume_background_bottom").addEventListener("click", function (e) {
    getMousePosition(document.getElementById("volume-progress-bar-background"), e);
  });

  //login with username password in localstorage
  window.current_address = window.serverurl;
  if (window.current_address.includes("https")) {
    var prot = "https://"
  } else {
    var prot = "http://"
  }

  var loginUrl = window.serverurl + "/v1/Login";
  if (localStorage.getItem('username') != null && localStorage.getItem('password') != null) {

    var user = localStorage.getItem('username');
    var password = localStorage.getItem('password');
    var hash = btoa(user + ":" + password);
    var authorizationBasic = "Basic " + hash;
    var request = new XMLHttpRequest();
    request.open('GET', loginUrl, true)
    request.setRequestHeader('Authorization', authorizationBasic);
    request.addEventListener('load', after_onload_browse);
    request.addEventListener('error', after_error_onload_browse);
    try {
      request.send();
    } catch {


    }
  }


  if (second_interval == null) {
    second_interval = setInterval(function () {
      try {
        eachsecond()
      } catch { }
    }, 1000);
  }
  if (second_interval_5 == null) {
    second_interval_5 = setInterval(function () {
      try {
        each5second()
      } catch { }
    }, 5000);
  }
}

function after_onload_browse() {
  var responseObject = JSON.parse(this.response);

  token = responseObject["token"]
  // set the token after login ...
  localStorage.setItem("token", token);
  window.isAdmin = responseObject["isAdmin"];

  Server_Ports(after_Ports);
  Server_Get_Menu(menu_file, after_Get_Menu_Library, null);
  window.executionlocation = responseObject["location"];
  // Barre du Player
  // Rien à charger ici ...

  // Updated images
  Server_Get_UpdatedImages(after_Get_UpdatedImages, null);


  window.onpopstate = ("popstate", function (e) {
    browsepopstate();
  });

  if (!isAndroid) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      document.getElementById('playlist_cover').addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      document.getElementById('query_cover').addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      document.getElementById('thumbs_container_2').addEventListener(eventName, preventDefaults, false);
    });

    document.getElementById('playlist_cover').addEventListener('drop', handleDrop, false);
    document.getElementById('query_cover').addEventListener('drop', handleDrop_query, false);
    document.getElementById('thumbs_container_2').addEventListener('drop', handleDrop_import, false);
   
  }
  document.getElementById('playlist_item_delete_img').addEventListener('dragend', playlist_item_delete, false);
  document.getElementById('playlist_item_delete_img').addEventListener('dragenter', playlist_item_dragenter);
  Server_Get_Players_Detected(after_Get_Players_Detected);
  //Server_Get_Players_Detect(after_Get_Players_Detect);
   Server_Scanning(after_Scanning, null);

}
