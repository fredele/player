var addr
var WsSocket
var second_interval;
var second_interval_5 = null;
var token
var server_mode = true;
var try_reconnect_ws = 0;


function getBaseUrl(url) {
  try {
    return new URL(url).origin;
  } catch (error) {
    console.error("URL invalide:", error);
    return null;
  }
}

function sleep(milliseconds) {
  const date = Date.now();
  let currentDate = null;
  do {
    currentDate = Date.now();
  } while (currentDate - date < milliseconds);
}

function on_ws_msg(data) {
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
    if (id != playerid) { return };

    if (msg == "mediafile_updated") {

      try { cancelabletimer.cancel(); } catch (error) { }
      cancelabletimer = CancelableTimer(3000);
    }


    if (msg == "SetNextAVT") {
      console.log("SetNextAVT")
      setnextav = val;
    }

    if (msg == "playlist changed") {
      Server_Get_Queue(after_Get_Queue, null);
    }

    if (msg == "auto import") {
      clearTimeout(myTimeOut);
      document.getElementById('scanning_img').opacity = 1;
      myTimeOut = setTimeout(function () {
        document.getElementById('scanning_img').opacity = 0;
      }, 3000);
    }

    if (msg == "audio changed") {
      // Reload the infos
      Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
      Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist);
      Server_Player_CurrentTrack(format_info, " ", after_Format_Display);
      setTimeout(() => { Server_Player_CurrentPosition(after_Player_CurrentPosition, null); }, 4000); // 1000, trop court ...
      setTimeout(() => { Server_Player_CurrentPosition(after_Player_CurrentPosition, null); }, 10000);
      //Remise a zero en pause
      if (window.current_player["type"] == "gstreamer") {
      }
      window.position = 0
      console.log(window.position)
      console.log("audio changed")
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
      }
      else if (val == "paused") {
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Pause" });
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/pause.png" });
        playing = false
      }
      else if (val == "stopped") {
        playing = false
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Stop" });
        Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/stop.png" });
        drawlevel("-60;-60");
      }
      else { }

    }

    if (msg == 'last player found') {
      Server_Get_Players_Detected(after_Get_Players_Detected);
    }
  }
}




function onload_server() {
  var browse_page = sessionStorage.getItem("browse_page");
  try {
    document.getElementById('browse_btn').setAttribute('href', browse_page);
  } catch { }
  window.serverurl = localStorage.getItem('serverurl')
  token = localStorage.getItem('token');
  read_vars();
  translateUI();
  dbinfos();
}

function Server_Connect_ws(ws_addr) {
  WsSocket = new WebSocket(ws_addr);
  WsSocket.onmessage = function (event) {
    on_ws_msg(JSON.parse(event.data)); // Entry point for each file specific JS file.
  };

  WsSocket.onopen = () => {
    if (try_reconnect_ws > 0) {
      // Reconnection occured ...
      try_reconnect_ws = 0;
      Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
      //Server_Get_State(after_Server_get_State, null);
    }
  };

  WsSocket.onerror = (ev) => {
    //console.error('error:', ev);
  };

  WsSocket.onclose = () => {
    try_reconnect_ws = try_reconnect_ws + 1;
    console.info('connection lost, reconnecting in 1s');
    if (try_reconnect_ws < 11) // Try to reconnect 0 Times ...
    {
      setTimeout(() => Server_Connect_ws(ws_addr), 1000);
      Array.from(document.getElementsByClassName('display_str')).forEach(el => {
        //el.innerHTML = translate("Try Reconnecting");
      })
    }
    else {
      try_reconnect_ws = 0;
      Array.from(document.getElementsByClassName('display_str')).forEach(el => {
        //el.innerHTML = translate("No Connection") ;
      })
    }
  };
}


function Server_Ports(clbk, state) {
  SendCommand("/v1/Ports", clbk, state);
}

function Server_Scanning(clbk, state) {
  SendCommand("/v1/Scanning", clbk, state);
}

function after_Ports() {
  if (this.status == 404) { return };
  res = this.response;
  res = JSON.parse(res)
  ws_addr = "ws://" + res.ip + ":" + res.wsport

  Server_Connect_ws(ws_addr)
  ip = res.ip;

  if (res.server == "True") { server_mode = true } else { server_mode = false }
}

function SendCommand(ApiEntry, Callback, state) {
  current_address = window.location.href;
  if (current_address.includes("https")) { prot = "https://" }
  else { prot = "http://" }
  if (window.serverurl != undefined) {
    window.addr = getBaseUrl(window.serverurl);
  } else {
    window.addr = getBaseUrl(current_address);
    window.serverurl = getBaseUrl(current_address);
  }
  var request = new XMLHttpRequest();
  var url = addr + ApiEntry

  if (url.includes("/Player/") || url.includes("/Queue/")) {
    if (window.current_player != undefined) {
      player_id = window.current_player["id"]
    }
    else {
      if (localStorage.getItem("current_player") !== null && localStorage.getItem("current_player") !== "here") {
        window.current_player = JSON.parse(localStorage.getItem("current_player"));
        player_id = window.current_player.id
      }
      else {
        player_id = 1;
      }

    }
    if (url.indexOf('?') > -1) {
      url += "&player_id=" + player_id
    } else {
      url += "?player_id=" + player_id
    }

  }

  request.open('GET', url, true);
  request.setRequestHeader("Authorization", "Bearer " + token);
  request.addEventListener('load', Callback);
  request.addEventListener('readystatechange', state);
  try {
    request.send();
  } catch {

  }
}


function SendCommandPOST(ApiEntry, Callback, state) {
  window.addr = prot + document.location.hostname + ":" + document.location.port;
  var request = new XMLHttpRequest();
  var url = addr + ApiEntry
  request.open('POST', url, true);
  request.setRequestHeader("Authorization", "Bearer " + token);
  request.addEventListener('load', Callback);
  request.addEventListener('readystatechange', state);
  try {
    request.send();
  } catch {

  }
}

function Unauth_state(s, e) {
  if (s.srcElement.status == 401) {
    alert("Login again ...");
    document.location.href = "config.html"
  }
}

//function Server_Get_Addr(){
//  return window.serverurl;
//}

function Server_Get_Coverurl(dirhash) {
  if (updatedimages.indexOf(dirhash) >= 0) {
    return window.serverurl + "/v1/Covers/" + dirhash + ".jpg" + "?uploadTime=" + Math.floor(Date.now() / 1000 / 10) * 10 + "&thumbnail=" + window.sideimage_width;
  }
  else {
    return window.serverurl + "/v1/Covers/" + dirhash + ".jpg?thumbnail=" + window.sideimage_width;
  }
}

function Server_Get_ThumbUrl(dirhash) {
  if (updatedimages.indexOf(dirhash) >= 0) {
    return window.serverurl + "/v1/Thumbnails/" + dirhash + ".jpg" + "?uploadTime=" + Math.floor(Date.now() / 1000 / 10) * 10; //+"&thumbnail=150"  
  }
  else {
    return window.serverurl + "/v1/Thumbnails/" + dirhash + ".jpg"; //+".jpg?thumbnail=150"
  }
}

function Server_DbInfo(clbk, state) {
  SendCommand("/v1/Stats", clbk, state);
}

function dbinfos() {
  Server_DbInfo(after_dbinfos, null);
}

function after_dbinfos() {
  res = JSON.parse(this.response);
  rep =
    capitalizeFirstLetter(translate("artist")) + " : " + res['artist_count'] + ", " +
    capitalizeFirstLetter(translate("album")) + " : " + res['album_count'] + ", " +
    capitalizeFirstLetter(translate("genre")) + " : " + res['genre_count']
  try {
    document.getElementById('dbinfos').innerHTML = rep;
  } catch (e) {
    //console.error("Erreur lors de l'affichage des informations de la base de données : ", e);
  }
}

function Server_Get_Commands() {
  SendCommand("/v1/Commands/Get", after_get_commands, null);
}

function Server_Run_Command(cmd) {
  SendCommand("/v1/Commands/Run?cmd=" + encodeURIComponent(cmd), after_run_commands, null);
}

function Server_Reimport_Query(query, clbk) {
  SendCommand("/v1/Library/Reimport?query=" + query, clbk, null);
}

function Server_Import_Drop(folder) {
  SendCommand("/v1/Library/Import?folder=" + encodeURIComponent(folder));
}

function Server_Import_New_Folders(minutes) {
  SendCommand("/v1/Library/Import?last=" + encodeURIComponent(minutes));
}

function Server_ClearQueries(clbk, state) {
  SendCommand("/v1/Cache/ClearQueries", clbk, Unauth_state);
}

function Server_LibraryRestore(clbk, state) {
  SendCommand("/v1/Library/Restore", clbk, Unauth_state);
}

function Server_LibraryBackup(clbk, state) {
  SendCommand("/v1/Library/Backup", clbk, Unauth_state);
}

function Server_Play(clbk, state) {
  SendCommand("/v1/Player/Play", clbk, null);
}

function Server_Stop(clbk, state) {
  SendCommand("/v1/Player/Stop", clbk, null);
}

function Server_Next(clbk, state) {
  SendCommand("/v1/Player/Next", clbk, state);
}

function Server_Previous(clbk, state) {
  SendCommand("/v1/Player/Previous", clbk, state);
}

function Server_Play_Radio(query, clbk, state) {
  SendCommand("/v1/Player/Radio?query=" + query, clbk, state);
}

function Server_Queue_Add_Ids_Play(ids, clbk, state) {
  SendCommand("/v1/Queue/Add?clear=true&play=true&ids=" + ids, clbk, state);
}

function Server_Queue_Add_Query_Play(query, clbk, state) {
  SendCommand("/v1/Queue/Add?clear=true&play=true&query=" + query, clbk, state);
}

function Server_Queue_Add_Ids_Queue(ids, clbk, state) {
  SendCommand("/v1/Queue/Add?ids=" + ids, clbk, state);
}

function Server_Queue_Add_Query_Queue(query, clbk, state) {
  SendCommand("/v1/Queue/Add?query=" + query, clbk, state);
}

function Server_Queue_Move_Ids(from_id, to_id, clbk, state) {
  SendCommand("/v1/Queue/Move?from=" + from_id + "&to=" + to_id, clbk, state);
}

function Server_Queue_Delete_Id(id, clbk, state) {
  SendCommand("/v1/Queue/Delete?id=" + id, clbk, state);
}

function Server_Get_Volume(clbk, state) {
  SendCommand("/v1/Player/Volume/Get", clbk, state);
}

function Server_Set_Volume(val, clbk, state) {
  SendCommand("/v1/Player/Volume/Set?val=" + val, clbk, state);
}

function Server_LibraryScanFolders(clbk, state) {
  SendCommand("/v1/Library/Scan/Update/Folders", clbk, state);
}

function Server_Player_CurrentTrack(displaystr, separator, clbk, state) {
  sep = encodeURIComponent(separator);
  //if(sep ==""){sep = "json"}
  SendCommand("/v1/Player/CurrentTrack?displaystr=" + encodeURIComponent(displaystr) + "&separator=" + sep, clbk, state);

  // Retrieve info on Current Track
  SendCommand("/v1/Player/CurrentTrack?displaystr=" + encodeURIComponent(displaystr) + "&separator=" + encodeURIComponent(sep), clbk, state);
}

function Server_Player_CurrentPosition(clbk, state) {
  // Retrieve position in queue
  SendCommand("/v1/Player/CurrentPosition", clbk, state);
}

function Server_Get_Queue(clbk, state) {
  SendCommand("/v1/Queue/Get?displaystr=" + encodeURIComponent(queue_track_info), clbk, state);
}

function Server_Get_Ouputs(clbk, state) {
  SendCommand(`/v1/Player/Outputs/Get`, clbk, state);
}

function Server_Get_Ouput_HW_params(clbk, state) {
  SendCommand(`/v1/Player/Output/GetParams`, clbk, state);
}

function Server_Set_Ouput(nbr, clbk, state) {
  SendCommand(`/v1/Player/Output/Set?nbr=` + nbr, clbk, state);
}

function Server_Player_Id(nbr, clbk, state) {
  SendCommand(`/v1/Player/Play?id=` + nbr, clbk, state);
}

function Server_Get_Menu(file, clbk, state) {
  SendCommand(`/v1/Menu/Get?file=` + file, clbk, state);
}

function Server_find(q, field, sort, display, page_nbr, response_count, clbk, state) {
  if (isNaN(page_nbr)) {
    return;
  }
  page_nbr = 0;
  page_nbr = page_nbr.toString();
  SendCommand("/v1/Library/Find?query=" + q + "&field=" + encodeURIComponent(field) + "&sorttag=" + encodeURIComponent(sort) + "&display=" + encodeURIComponent(display) + "&page_nbr=" + page_nbr + "&response_count=" + response_count, clbk, state);
}

function Server_search(field, value, query, clbk, state) {
  SendCommand("/v1/Library/Search?field=" + field + "&value=" + value + "&query=" + query, clbk, state);
}

function Server_Get_Podcast(file, clbk, state) {
  SendCommand("/v1/Library/Podcast/Get?file=" + file + "&levels=1", clbk, state);
}

function Server_Get_Radio(file, clbk, state) {
  SendCommand("/v1/Library/Radio/Get?file=" + file, clbk, state);
}

function Server_Play_Podcast(stream, cover, title, length, clbk, state) {
  SendCommand("/v1/Player/Play?stream=" + stream + "&cover=" + cover + "&length=" + length + "&title=" + title, clbk, state);
}

function Server_Decode_Podcast(rss, cover, clbk, state) {
  SendCommand("/v1/Podcast/Decode?rss=" + rss + "&cover=" + encodeURIComponent(cover), clbk, state);
}

function Server_Get_Covers(q, clbk, state) {
  SendCommand("/v1/Display/Covers?query=" + q, clbk, state);
}

function Server_Get_Group_Query(q, displaystr, separator, clbk, state) {
  SendCommand("/v1/Display/Group?query=" + q + "&displaystr=" + encodeURIComponent(displaystr) + "&separator=" + encodeURIComponent(separator), clbk, state);
}

function Server_Get_Group_Ids(ids, displaystr, separator, clbk, state) {
  ids = current_ids.join(';')
  SendCommand("/v1/Display/Group?ids=" + ids + "&displaystr=" + encodeURIComponent(displaystr) + "&separator=" + encodeURIComponent(separator), clbk, state);
}

function Server_TrackInfo(id, displaystr, separator, clbk, state) {
  SendCommand("/v1/Player/TrackInfo?id=" + id + "&displaystr=" + encodeURIComponent(displaystr) + "&separator=" + encodeURIComponent(separator), clbk, state);
}

function Server_Get_Files_query(q, displaystr, clbk, state) {
  var trackliste = document.getElementById('query_tracklist');
  try { trackliste.innerHTML = ""; } catch { }
  SendCommand("/v1/Display/Files?query=" + q + "&displaystr=" + encodeURIComponent(displaystr), clbk, state);
}

function Server_Get_Files_ids(ids, displaystr, clbk, state) {
  var trackliste = document.getElementById('query_tracklist');
  try { trackliste.innerHTML = ""; } catch { }
  SendCommand("/v1/Display/Files?ids=" + ids + "&displaystr=" + encodeURIComponent(displaystr), clbk, state);
}

function Server_Get_Files_dirhash(dirhash, clbk, state) {
  q = "{'$and': [{'mediatype': 'audio'}, {'dirhash': " + dirhash + "}]}";
  displaystr = '$discnumber$ / $tracknumber$ - $title$'
  SendCommand("/v1/Display/Files?query=" + q + "&displaystr=" + encodeURIComponent(displaystr), clbk, state);
}

function Server_Get_SideFiles(query, clbk, state) {
  if (query.startsWith("query=")) {
    query = query.slice(6);
  }
  SendCommand("/v1/SideFiles?query= " + query, clbk, state);
}

function Server_Get_SideFile(dirhash, filename, clbk, state) {
  SendCommand("/v1/SideFile/" + dirhash + "/" + filename, clbk, state);
}

function Server_Get_GetValues(q, tags, clbk, state) {
  SendCommand("/v1/Library/GetValues?query=" + q + "&tags=" + encodeURIComponent(tags), clbk, state);
}

function Server_Get_Pulse_Outputs(clbk, state) {
  SendCommand("/v1/Pulseaudio/Outputs", clbk, state);
}

function Server_Set_Pulse(output, clbk, state) {
  SendCommand("/v1/Pulseaudio/SetOutput?output=" + encodeURIComponent(output), clbk, state);
}

function Server_Get_State(clbk, state) {
  SendCommand("/v1/Player/State", clbk, state);
}


function Server_Get_Players(clbk, state) {
  SendCommand("/v1/Player/Players/Get", clbk, state);
}

function Server_Get_Players_Detected(clbk, state) {
  SendCommand("/v1/Players/Get?devices=detected", clbk, state);
}

function Server_Get_Players_Detect(clbk, state) {
  SendCommand("/v1/Players/Get?devices=detect", clbk, state);
}

function Server_Get_Players(clbk, state) {
  SendCommand("/v1/Players/Get", clbk, state);
}

function Server_Set_Player(id, clbk, state) {
  SendCommand("/v1/SetPlayer/" + id, clbk, state);
}

function Server_Shutdown() {
  SendCommand("/v1/Shutdown", after_shutdown, null);
}

function after_shutdown() {
  var responseObject = JSON.parse(this.response);
}

function Server_FindFiles_Query(query, clbk, state) {
  SendCommand("/v1/Library/FindFiles?query=" + query, clbk, state);
}

function Server_GetValues(ids, tag, clbk, state) {
  ids = ids.join(';')
  SendCommand("/v1/Library/GetValues?tags=" + tag + "&ids=" + ids, clbk, state);
}

function Server_set_tag(current_ids, tag, value, clbk, state) {
  ids = current_ids.join(';')
  SendCommand("/v1/Library/SetTag?tag=" + encodeURIComponent(tag) + "&value=" + encodeURIComponent(value) + "&ids=" + ids, clbk, state);
}

function Server_Get_UpdatedImages(clbk, state) {
  SendCommand("/v1/Thumbnails/Epoch", clbk, state);
}


function Server_Get_Settings(clbk) {
  SendCommand("/v1/Settings/Get", clbk, null);
}


function Server_Get_Lang(clbk) {
  SendCommand("/v1/Player/Lang/Get", clbk, null);
}

function Server_Set_Settings(tags_indexes, tags_singlevalues, tags_customtags, player_volume) {

  SendCommand("/v1/Settings/Set?indexes=" + tags_indexes
    + "&singlevalue=" + tags_singlevalues
    + "&txxx=" + tags_customtags
    + "&volume=" + player_volume
  );

}

function Server_Rip() {
  SendCommand("/v1/Rip");
}
