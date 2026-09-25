function play_radio(thumb) {
  url = thumb.getAttribute("url");
  cover = thumb.getAttribute("covers");
  title = thumb.getAttribute("title");
  length = 0;

  Server_Play_Podcast(url, cover, title, length, after_play_radio, null);
}

function after_play_radio() {
  Server_Get_Queue(after_Get_Queue, null);
}


function play_podcast(thumb) {
  url = thumb.getAttribute("url");
  cover = thumb.getAttribute("covers");
  title = thumb.getAttribute("title");
  length = thumb.getAttribute("length");

  Server_Play_Podcast(url, cover, title, length, after_play_podcast, null);
}


function after_play_podcast() {
  Server_Get_Queue(after_Get_Queue, null);
}



function after_Player_CurrentPosition() {

  if (this.response == undefined) { return; };
  var responseObject = JSON.parse(this.response);
  window.state = responseObject["state"];
  if (window.state == "playing") { playing = true } else { playing = false }
  // OR : playing, paused, stopped
  window.position = responseObject.position;
  calc_queueelapse();
  let hhmmssposition = MsToMMSS(window.position);

  if (responseObject.position != undefined) {
    //-----------
    if (flipflopelapsedbool == true) {
      document.getElementById('time_elapsed').innerHTML = MsToMMSS(queueelapse + window.position); 
    }
    else {
      if (responseObject.duration == 0) {
        document.getElementById('time_elapsed').innerHTML = "";
        document.getElementById('time_total').innerHTML = "";
      }
      else{
      document.getElementById('time_elapsed').innerHTML = MsToMMSS(window.position); 
      }
    }
  }
  //-----------
  if (responseObject.duration != undefined) {
    if (flipflopelapsedbool == true) {
      document.getElementById('time_total').innerHTML = MsToMMSS(queuetot);
    }
    else {
      document.getElementById('time_total').innerHTML = MsToMMSS(responseObject.duration); 
    }
  }
  else {
    document.getElementById('time_total').innerHTML = "";
    document.getElementById('time_elapsed').innerHTML = "";
  }
  window.duration = responseObject.duration;

  if (responseObject.state == "paused") {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Pause" });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/pause.png" });
    playing = false
  }
  if (responseObject.state == "playing") {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Play" });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/play.png" });
    playing = true
  }
}

function move_panels() {


  if (Array.from(document.getElementsByClassName('display_str'))[0].innerHTML == translate("No Connection")) {
    location.reload();
    return;
  }
  if (document.getElementById("menu_all").style.width == "80px") {
    menu_hide();
    return;
  }
  try {
    if (document.getElementById('doc').style.left == "0%") {
      document.getElementById('doc').style.left = "-100%";
      document.getElementById('doc').contentDocument.body.innerHTML = "";
      return;
    }
  } catch (error) { }
  var playlist = document.getElementById('playlist_container');
  var thumbs = document.getElementById('thumbs_container');
  var query = document.getElementById('query_container');




  hidebigcover();

  if (document.getElementById('playlist').innerHTML == '') /*playlist is empty*/ {
    return; /* Playlist vide ...*/
  }


  if (query.style.left == "-150%" || query.style.left == "") {
    if (thumbs.style.left == "0%" || thumbs.style.left == "") {
      playlist.style.left = "0%";
      thumbs.style.left = "-150%";
    }
    else {
      playlist.style.left = "-150%";
      thumbs.style.left = "0%";
    }
  }

  if (query.style.left == "0%") {
    if (playlist.style.left == "-150%" || playlist.style.left == "") {
      header_line.pop();
      document.getElementById("header_container").innerHTML = header_line.join(' > ');
    }
    query.style.left = "-150%";
    thumbs.style.left = "0%";
    return;
  }
}

function Play() {
  Server_Play(after_Play, null);
}

function after_Play() {
  var responseObject = JSON.parse(this.response);
  //window.state = responseObject["state"];
}

function after_Stop() {
  //var responseObject = JSON.parse(this.response);
}

function Next() {
  Server_Next(after_Next, null);
}

function Previous() {
  Server_Previous(after_Previous, null);
}

function after_Previous() {
  res = JSON.parse(this.response);
  var playliste = document.getElementById('playlist');
  queue_position = res.queue_position;
  calc_queueelapse();
}

function after_Next() {
  res = JSON.parse(this.response);
  var playliste = document.getElementById('playlist');
  queue_position = res.queue_position;
  calc_queueelapse();
}

function volume_show() {
  if (current_player["volume_control"] == true) {
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
  Server_Set_Volume(pos, after_Set_Volume, null);
}

function after_Set_Volume() {
  res = JSON.parse(this.response);
  vol = res["volume"];
  document.getElementById("volume-progress-bar").style.width = vol * 100 + "%";
}

function after_Get_Volume(data) {
  var responseObject = JSON.parse(this.response);
  volume = responseObject.volume * 100;
  document.getElementById("volume-progress-bar").style.width = volume + "%";
}

function change_track(nbr) {
  queue_position = nbr;
  window.position = 0;
  playing = false; //fredele
  calc_queueelapse();
  console.log(nbr)
  Server_Player_Id(nbr, after_Server_Player_Id, null);

  event.stopPropagation();
}

function after_Server_Player_Id() {
  res = JSON.parse(this.response);
}

function query_play() {



  ids = []
  Array.from(document.getElementsByClassName('query_track_item_selected')).forEach(el => { ids.push(el.getAttribute("idnbr")) });


  if (ids.length > 0) {
    Server_Queue_Add_Ids_Play(ids.join(';'), after_query_play(), null);
  }
  else {
    //Server_Queue_Add_Query_Play(window.queryview_last_query,after_query_play(),null);
    Server_Queue_Add_Ids_Play(current_ids.join(";"), after_query_play(), null);
  }
  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";
}

function after_query_play() {
  playing = true;
}

function query_queue() {

  ids = []
  Array.from(document.getElementsByClassName('query_track_item_selected')).forEach(el => { ids.push(el.getAttribute("idnbr")) });


  if (ids.length > 0) {
    Server_Queue_Add_Ids_Queue(ids.join(';'), null, null);
  }
  else {
    Server_Queue_Add_Ids_Queue(current_ids.join(";"), null, null);
  }
  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";

}



function each5second() {
  if (player != null) {
    Server_Get_State(after_Server_get_State, null)
  }
}

function after_Server_get_State() {
  if (this.response == undefined) { return; };
  var responseObject = JSON.parse(this.response);
  if (responseObject['response'] == "Error") { return }
  if (responseObject['position'] > 0) {
    window.position = responseObject['position']
    //console.log(window.position)
    //console.log("after_Server_get_State")
  }
  
  window.duration = responseObject['duration']
  window.state = responseObject['state']

  // Mark track
  var playliste = document.getElementById('playlist');
  for (var i = 0; i < playliste.children.length; i++) {
    playliste.children[i].children[2].src = "img/transparent.png"
    if (responseObject["queue_position"] == i) {
      playliste.children[i].children[2].src = "img/volume.png"
    }

  }

  if (window.state == "playing") { playing = true } else { playing = false }
  calc_queueelapse();
  if (window.state == "stopped") {
    document.getElementById('time_elapsed').innerHTML = ""; 
    drawlevel("-60;-60");
  }

  if (window.state == "playing") {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Play" });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/play.png" });

  }

  if (window.duration != undefined) {
    if (flipflopelapsedbool == false) {
      if(window.duration > 0) {
      document.getElementById('time_total').innerHTML = MsToMMSS(window.duration); 
      }
      if(window.duration == 0) {
      document.getElementById('time_total').innerHTML = ""; 
      document.getElementById('time_elapsed').innerHTML = "";
  
    }

    }
    else {
      document.getElementById('time_total').innerHTML = MsToMMSS(queuetot);
    }
  }
  else {
    document.getElementById('time_total').innerHTML = ""; 
    document.getElementById('time_elapsed').innerHTML = "";
  }
  if (window.state == "paused") {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Pause" });
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/pause.png" });
  }
}

function on_ws_msg(data) {

  if (window.current_player == undefined) {
    return;
  };
  if (olddata == data) {
    return;
  };
  olddata = data;
  if (typeof data === 'string') {
    if (data.startsWith("##") == true) {

      data = data.slice(2);
      if (data.split(":")[0] == window.current_player["id"]) {
        c(data);
      }
      return;
    }
  }

  if (typeof data === 'string') {
    if (data.startsWith("#") == true) {
      data = data.slice(1);
      if (data.split(":")[0] == window.current_player["id"]) {
        drawlevel(data.split(":")[1]);
      }
      return;
    }
  }

  if ("message" in data) {
    var msg = data["message"];
    var val = data["value"];
    var id = data["id"];




    if (msg == "auto import") {
      clearTimeout(myTimeOut);
      document.getElementById('scanning_img').style.opacity = 1;
      myTimeOut = setTimeout(function () {
        document.getElementById('scanning_img').style.opacity = 0;
      }, 3000);
    }


    if (msg == "library_scan_started")
    {
      document.getElementById('scanning_img').style.opacity = 1;
      window.scanning = true;
      sessionStorage.setItem("Library Updating", "true");
      return;
    }

    if (msg == "library_scan_finished" || msg == "library_scan_stopped" || msg == "library_scan_error")
    {
      document.getElementById('scanning_img').style.opacity = 0;
      sessionStorage.setItem("Library Updating", "false");
      window.scanning = false;
      Server_Get_UpdatedImages(after_Get_UpdatedImages)
      return;
    }
   

    if (msg == "Cover changed") {
      Server_Get_UpdatedImages(after_Get_UpdatedImages)
    }


    if (id != window.current_player["id"]) { return }; // Messages for the current player ONLY ..

    if (msg == "No player Object for this player") {
      console.log("No player Object for this player " + id);

    }




    if (msg == "SetNextAVT") {
      console.log("SetNextAVT")
      setnextav = val;
    }

    if (msg == "Tags Edited") {
      Server_Get_Queue(after_Get_Queue, null);
    }

    if (msg == "playlist changed") {
      Server_Get_Queue(after_Get_Queue, null);
    }

    if (msg == "audio changed") {
      // Reload the infos
      Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
      Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist);
      Server_Player_CurrentTrack(format_info, " ", after_Format_Display);
      setTimeout(() => { Server_Player_CurrentPosition(after_Player_CurrentPosition, null); }, 4000);
      setTimeout(() => { Server_Player_CurrentPosition(after_Player_CurrentPosition, null); }, 10000);
      //Remise a zero en pause

      window.position = 0
    }




    if (msg == "end of stream") {
      playing = false
      document.getElementById('time_total').innerHTML = ""; 
      document.getElementById('time_elapsed').innerHTML = ""; 
      var playliste = document.getElementById('playlist');
      for (var i = 0; i < playliste.children.length; i++) { playliste.children[i].children[2].src = "img/transparent.png" }
      Array.from(document.getElementsByClassName('display_str')).forEach(el => { el.innerHTML = ""; })
      document.getElementById('time_spacer').innerHTML = "";
      Array.from(document.getElementsByClassName('current_track_infos')).forEach(el => { el.innerHTML = ""; })
    }
    if (msg == "Calculating query") {
      console.log("Calculating query for hash " + val)

    }

    if (msg == "state changed") {
      // Play Btns
      if (val == "playing") {
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Play" });
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/play.png" });
        playing = true
        console.log("state changed to playing")
      }
      else if (val == "paused") {
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Pause" });
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/pause.png" });
        playing = false
        console.log("state changed to paused")
      }
      else if (val == "stopped") {
        playing = false
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Stop" });
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/stop.png" });
        console.log("state changed to stopped")
        drawlevel("-60;-60");
      }
      else { }

    }

    if (msg == 'last player found') {
      Server_Get_Players_Detected(after_Get_Players_Detected);
    }
  }
}

function onload_browse() {



  if (isCordova()) {
    if (localStorage.hasOwnProperty('serverurl')) {
      window.serverurl = localStorage.getItem('serverurl')
    }
    else {
      console.log(window.current_address);

      if (isCordova()) {
        window.location.href = "config.html";
      } else {
        window.location.href = "/html/config.html";
      }


    }
  }

  var elementToChange = document.getElementsByTagName("body")[0];
  cu = 'img/cursor.png';
  elementToChange.style.cursor = cu;


  sessionStorage.setItem("browse_page", document.URL);

  if (localStorage.hasOwnProperty('thumb_nbrs')) {
    req_thumb_cout = parseInt(localStorage.getItem('thumb_nbrs'));
    if (req_thumb_cout < 10) { req_thumb_cout = 1500 }
  }

  function stop() {
    event.preventDefault();
    event.stopPropagation();
    return false;
  }

  window.oncontextmenu = function (event) {

  }

  // Overflow detection
  document.getElementById('thumbs_container_2').addEventListener('scroll', () => {
    thumbsbox_overflow();
  });

  document.getElementById('play_btn').addEventListener('long-press', function (e) {
    e.preventDefault();

    if (document.getElementById('play_btn').src.includes("play")) {
      Server_Stop(after_Stop);
      return;
    };

    if (lastquery != "") {
      Server_Play_Radio(lastquery, after_Server_Play_Radio);
    };
  });






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
  document.getElementById('search1').innerHTML = translate("Search") + " :";
  document.getElementById('button_set_value').value = translate("save");

  window.ui = "active"
  try { Server_LibraryScanStatus(after_ScanStatus, null); } catch (e) {}

  // Get the modals
  tageditormodal = document.getElementById("TagEditorModal");
  window.searchmodal = document.getElementById("SearchBoxModal");

  window.outputmodal = document.getElementById("OutputModal");

  window.onclick = function (event) {

    if (event.target == window.searchmodal) {
      window.searchmodal.style.display = "none";
      typing = false;
    }

    if (event.target == tageditormodal) {
      tageditormodal.style.display = "none";
      typing = false;
      document.getElementById('button_set_value').disabled = true;
    }

    if (event.target == window.outputmodal) {
      window.outputmodal.style.display = "none";

    }
  }


  var ua = navigator.userAgent.toLowerCase();
  isAndroid = ua.indexOf("android") > -1;

  current_address = window.serverurl;

  // Load the menu in the URL args
  var args = getJsonFromUrl(current_address);
  if ("menu_file" in args) { menu_file = args["menu_file"]; }
  if ("thumb_style" in args) {
    thumb_style = args["thumb_style"];
  }


  document.getElementById("volume-progress-bar-background").addEventListener("click", function (e) { getMousePosition(document.getElementById("volume-progress-bar-background"), e); });
  document.getElementById("volume_background_bottom").addEventListener("click", function (e) { getMousePosition(document.getElementById("volume-progress-bar-background"), e); });

  //login with username password in localstorage

  if (isCordova()) {
    var loginUrl = window.serverurl + "/v1/Login"
  }
  else {
    var loginUrl = "/v1/Login"
  }
  if (localStorage.getItem('username') != null && localStorage.getItem('password') != null) {

    var user = localStorage.getItem('username');
    var password = localStorage.getItem('password');
    var hash = btoa(user + ":" + password);
    var authorizationBasic = "Basic " + hash;
    var request = new XMLHttpRequest();
    request.open('GET', loginUrl, true)
    request.setRequestHeader('Authorization', authorizationBasic);
    request.addEventListener('load', after_onload_browse);
    request.onerror = function () {
      if (isCordova()) {
        window.location.href = "config.html";
      } else {
        window.location.href = "/html/config.html";
      }
    };

    try {
      request.send();
    } catch {

    }


  }


  if (second_interval == null) {
    second_interval = setInterval(function () { try { eachsecond() } catch { } }, 1000);
  }
  if (second_interval_5 == null) {
    second_interval_5 = setInterval(function () { try { each5second() } catch { } }, 5000);
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
  if (window.current_player == undefined) {
    if (getExecutionContext() != "internet") {
      document.getElementById("chooseoutput").style.display = "none";
      document.getElementById("OutputModal").style.display = "block";
      Server_Get_Players_Detected(after_Get_Players_Detected);

      return;
    } else {
      window.current_player = "here";
      document.getElementById("playerdropbtn").innerHTML = translate("Here")
      loadScript("js/browse_web.js", null);
      drawlevel("-60;-60");
      clear_ui();
    }

  }
  if (window.current_player !== undefined) {
    Server_Get_Volume(after_Get_Volume, null);
    // Barre du Player
    Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
    Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist, null);
    Server_Player_CurrentTrack(format_info, " ", after_Format_Display, null);
    Server_LibraryScanStatus(after_ScanStatus, null);
    Server_Get_Ouputs(after_Get_Output, null);
    Server_Get_Queue(after_Get_Queue, null);
    Server_Player_CurrentPosition(after_Player_CurrentPosition, null);
    // Connect to last used player if available
    //document.getElementById("playerdropbtn").innerHTML = window.current_player["name"];
    Server_Get_Players_Detected(after_Get_Players_Detected);
  }

  document.getElementById("status").innerHTML = "status : OK"
  //TODO: detect upnp players
  //Server_Get_Players_Detect(after_Get_Players_Detect);
  Server_Get_Ouputs(after_Get_Output);

  // Updated images
  Server_Get_UpdatedImages(after_Get_UpdatedImages, null);

  window.dispatchEvent(new Event('resize'));
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
    const queryCoverImg = document.getElementById('query_cover');
    queryCoverImg.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
    });

    queryCoverImg.addEventListener('drop', handleDrop_query, false);



    document.getElementById('thumbs_container_2').addEventListener('drop', handleDrop_import, false);
    
  }
  document.getElementById('playlist_item_delete_img').addEventListener('dragend', playlist_item_delete, false);
  document.getElementById('playlist_item_delete_img').addEventListener('dragenter', playlist_item_dragenter);


}

