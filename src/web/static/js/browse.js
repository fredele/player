var token = null;
var levelcanvas = null;
var lastthumb = null;
var lastbrowsethumb = null;
var spectrumcanvas = null;
var elem = document.documentElement;
var current_ids = [];
var current_player;
var files_queried = [];
var current_selected_ids = [];
var myTimeOut
var header_line = []
var dragstart = 0;
var dragend = 0;
var selected_podcast;
var queue_position;
var queue = [];
var thumb_style = "thumb"
var block = false;
var lastquery = ""
var query_all_height = ""
var updatedimages = [];
var thumb_q = null;
var page_nbr = 0;
var field_q = null;
var sort_q = null;
var display_q = null;
var isAndroid = false;
var pressTimer;
var snapstream = null;
var ws_snapstream_addr = null;
var query_image_content = `<div id="query_image_btn_previous" onclick="previousimg()"></div><div id="query_image_img_div" ><img  class="yall_lazy" id="query_image_img" src="" ></div><div id="query_image_btn_next" onclick="nextimg()"></div>`;
var isAndroid = false
var invdictranslation;
var lastquery = "";
var lastfield = "";
var lastsort = "";
var lastdisplay = "";
var playlist = [];
var current_playing_position = 0;
let player;
var current_hub = "";
var reimport_query = "";
var req_thumb_cout = 1500;
var level = 0;
var browsemenu = 0;
let globalPipeline;
var mediaplayer = null;
var second_interval = null;
var second_interval_5 = null;
var init_player = true;
var player_change_block = false;
window.playhere = true;
var mediastop = false;
var flipflopelapsedbool = false;
flexContainer = document.getElementById('thumbs_container_2');

var uan = navigator.userAgent.toLowerCase();

if (uan.includes("mobi") || uan.includes("android") || uan.includes("iphone") || uan.includes("ipad")) {
    console.log("Chargé sur un appareil mobile (souvent Android si 'android' est présent)");
    var uap = "mobi"
} else {
    console.log("Chargé sur PC (desktop)");
    var uap = "desk"
}

try {
  if (isCordova()) {
    console.log('Cordova détecté')
  } else {
    console.log('Cordova non détecté')
  }
} catch (e) { }



function after_Player_CurrentPosition() { }
try {

  //document.getElementById('volume_btn').addEventListener('long-press', function (e) {
  //  e.preventDefault();
  //  show_outputs();
  //});

  const volumeBtn = document.getElementById('volume_btn');

  addLongPressListener(
    volumeBtn,
    () => volume_show(),    
    () => show_outputs(),   
    700                    
  );



  const scanBtn = document.getElementById('scanning_img');

  addLongPressListener(
    scanBtn,
    () => move_panels(),    
    () => Server_LibraryScanMusicFolders(),   
    700                 
  );



} catch (e) { }



function ScanMusicFolders() {

  if (document.getElementById('scanning_img').style.opacity == 0) {
      // n'exécute le scan que si on est dans le hub "music library"
      if (current_hub === 'music_library') {
        Server_LibraryScanMusicFolders();
      }
    }

}


function move_panels() {
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
    } else {
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

function flipflopelapsed() {
  event.stopPropagation();
  calc_queueelapse();
  flipflopelapsedbool = !flipflopelapsedbool;
  if (flipflopelapsedbool == true) {
    document.getElementById('time_total').innerHTML = MsToMMSS(queuetot);

  } else {
    document.getElementById('time_total').innerHTML = MsToMMSS(window.duration);

  }

  if (flipflopelapsedbool == false) {
    document.getElementById('time_elapsed').innerHTML = MsToMMSS(window.position);
  } else {
    document.getElementById('time_elapsed').innerHTML = MsToMMSS(window.position + queueelapse);
  }

}

function makeLinksOpenInNewWindow() {
  // Sélectionner tous les éléments <a> de la page
  const links = document.querySelectorAll('a');

  // Parcourir chaque lien et modifier son attribut target
  links.forEach(link => {
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'noopener noreferrer'); // Meilleure sécurité pour éviter les attaques par tab-napping
  });
}

function makeUnselectable(node) {
  if (node == null) {
    return;
  }
  if (node.nodeType == 1) {
    //node.setAttribute("unselectable", "on");
    node.classList.add("unselectable")
  }
  var child = node.firstChild;
  while (child) {
    makeUnselectable(child);
    child = child.nextSibling;
  }
}

function iframeclick() {
  document.getElementById("doc").contentWindow.document.body.onclick = function () {
    document.getElementById('doc').style.left = "-100%";
    document.getElementById('doc').contentDocument.body.innerHTML = "";
  }
}

function setkeydownhandler() {
  window.addEventListener("keydown", function (inEvent) {
    if (typing == true) {
      return;
    };
    if (window.event) {
      keycode = inEvent.keyCode;
    } else if (e.which) {
      keycode = inEvent.which;
    }
    switch (keycode) {
      //case 461: doBack(); break;  
      case 38:
        Previous();
        break; //  arrow up
      case 40:
        Next();
        break; //  arrow down
      //case 19: doPause(); break;
      case 415:
        Play();
        break;
      case 32:
        Play();
        break; // space bar
      case 403:
        doRed();
        break;
      case 404:
        doGreen();
        break;
      case 405:
        doYellow();
        break;
      case 406:
        doBlue();
        break;
      case 13:
        menu_display();
        break;
      case 33:
        inEvent.preventDefault();
        ScrollUpthumbs();
        break; //pageUp
      case 34:
        inEvent.preventDefault();
        ScrollDownthumbs();
        break; //pageDown
    }
  });
}

function calc_queueelapse() {
  queueelapse = 0
  queuetot = 0
  for (var i = 0; i < queue.length; i++) {
    t = queue[i]["length"] * 1000;
    if (i < queue_position) {
      queueelapse = queueelapse + t
    }
    queuetot = queuetot + t
  }

}

function set_overflow()
/*
Completes pagination on Windows sizing
*/ {
  const isOverflowing = flexContainer.scrollHeight > flexContainer.clientHeight;
  if (isOverflowing == false) {
    //Server_find(thumb_q,field_q,sort_q,display_q, page_nbr +1,req_thumb_cout,after_Server_find,null)

  }
}

function isandroid() {
  // Renderer process
  if (typeof window !== 'undefined' && typeof window.process === 'object' && window.process.type === 'renderer') {
    return true;
  }

  // Main process
  if (typeof process !== 'undefined' && typeof process.versions === 'object' && !!process.versions.android) {
    return true;
  }

  // Detect the user agent when the `nodeIntegration` option is set to true
  if (typeof navigator === 'object' && typeof navigator.userAgent === 'string' && navigator.userAgent.indexOf('android') >= 0) {
    return true;
  }

  return false;
}

function showsearch() {
  typing = true;

  window.searchmodal.style.display = "block";
  document.getElementById('search_btn').disabled = false;
  document.getElementById('search_txt').focus();
}

function exit_search() {
  event.stopPropagation();
  //document.getElementById('header_container').innerHTML = searchheader
  browse_to_level(level);
}

function Search_value() {

  document.getElementById('header_container').innerHTML = '<span class="color1"> < </span>' + '<span class="color2" onclick="exit_search()">' + translate("back") + '</span>'
  search_text = document.getElementById('search_txt').value;
  document.getElementById('search_btn').disabled = true; 
  Server_search(search_text, lastquery, After_Search_value, null);
  window.searchmodal.style.display = "none";
}

function After_Search_value() {
  res = JSON.parse(this.response)
  if (res["response"] == "Error") {
    return;
  }
  window.searchmodal.style.display = "none";
  var thumbs_box = document.getElementById("thumbs_box");
  thumbs_box.innerHTML = '';
  allcontent = "";
  for (var i = 0; i < res['Result'].length; i++) {
    dirhash = res["Result"][i]["dirhash"]
    thumburl = Server_Get_ThumbUrl(dirhash)
    coverurl = thumburl
    display = res["Result"][i]["album"]
    query = "%7B%27%24and%27%3A+%5B%7B%27dirhash%27%3A+" + dirhash + "%7D%5D%7D"
    content = '<div class="thumb" onclick="on_thumb_click_Search(this)" dirhash="' + dirhash + '" covers="' + coverurl + '" query="' + query + '" style="width: 135px; height: 151px;"><img class="yall_lazy thumbimg" data-src="' + thumburl + `" onerror="this.src='img/cd.png' draggable='false' "> <div class="thumbtitle"><span class=` + `album` + `_display >${display}</span></div></div>`
    allcontent = allcontent + content;
    thumbs_box.innerHTML = allcontent;
    lazyload.run();
  }
}

function reload_ui() {
  level = 0
  window.ui = "active"
  Server_Get_Menu(menu_file, after_Get_Menu_Library, null);
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/play.png"
  });
  document.getElementById('query_background').src = "img/transparent.png"
  document.getElementById('query_tracklist').innerHTML = "";
  document.getElementById('query_cover').src = "img/cd.png"
  document.getElementById('query_bigcoverimg').src = "img/cd.png"
  document.getElementById('coverimg').src = "img/cd.png"
  Array.from(document.getElementsByClassName('display_str')).forEach(el => {
    el.innerHTML = "";
  })
  document.getElementById('time_elapsed').innerHTML = ""
  var imgs = document.images;
  for (var i = 0, iLen = imgs.length; i < iLen; i++) {
    imgs[i].style.display = "block";
  }
  document.getElementById("playlist_item_delete_img").style.display = "none";
  document.getElementById("scanning_img").style.display = "none";
  document.getElementById("header_container").style.display = "block";
}

function error_ui() {
  window.ui = "error"
  snapstream == null;

  Array.from(document.getElementsByClassName('cover-bckg')).forEach(el => {
    // Avoids the flickering ..
    el.src = "img/transparent.png"
  });
  document.getElementById('playlist_container').style.left = "-150%";
  document.getElementById('thumbs_container').style.left = "0%";
  document.getElementById('query_container').style.left = "-150%";
  Array.from(document.getElementsByClassName('display_str')).forEach(el => {
    el.innerHTML = "No Connection";
  })
  document.getElementById('playlist').innerHTML = "";
  document.getElementById("current_track_infos").innerHTML = "";
  document.getElementById("time_total").innerHTML = "";
  document.getElementById("time_elapsed").innerHTML = "";
  document.getElementById("thumbs_box").innerHTML = "";
  document.getElementById("header_container").style.display = "none";
  var imgs = document.images;
  for (var i = 0, iLen = imgs.length; i < iLen; i++) {
    imgs[i].style.display = "none";
  }
}


function hiderightpanel() {
  const rp = document.getElementById('right_panel');
  const lp = document.getElementById('left_panel');

  if (rp.classList.contains('portrait')) {
    // rp a la classe "portrait"
    return;
  }

  if (rp.classList.contains('landscape')) {
    rp.classList.remove('portrait');
    rp.classList.remove('landscape');
    lp.classList.remove('portrait');
    lp.classList.remove('landscape');
    rp.classList.remove('full');
    rp.classList.add('half');
    lp.classList.remove('portrait');
    lp.classList.add('visible');
  }

  rp.classList.remove('portrait');
  rp.classList.remove('landscape');
  lp.classList.remove('portrait');
  lp.classList.remove('landscape');


  if (rp.classList.contains('half') || !rp.classList.contains('full')) {
    rp.classList.remove('half');
    rp.classList.add('full');
    lp.classList.add('portrait');
    lp.classList.remove('visible');
  } else {
    rp.classList.remove('full');
    rp.classList.add('half');
    lp.classList.remove('portrait');
    lp.classList.add('visible');
  }
}

function browse_to(dirhash) {
  event.stopPropagation();
  browse_to_dirhash(dirhash);
}

/* View in fullscreen */
function openFullscreen() {
  if (elem.requestFullscreen) {
    elem.requestFullscreen();
  } else if (elem.webkitRequestFullscreen) {
    /* Safari */
    elem.webkitRequestFullscreen();
  } else if (elem.msRequestFullscreen) {
    /* IE11 */
    elem.msRequestFullscreen();
  }
}

/* Close fullscreen */
function closeFullscreen() {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    /* Safari */
    document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) {
    /* IE11 */
    document.msExitFullscreen();
  }
}


var level = 0
var qlevel = {};
var browsemenu = 0;
var olddata = "";

function showbigcover() {

  if (document.getElementById('coverimg').src.split('/').pop() == "cd.png") {
    return;
  }
  try {
    if (document.getElementById('doc').style.left == "0%") {
      return;
    }
  } catch (error) { }
  if (document.getElementById('cover_big_container').style.width == "0px" || document.getElementById('cover_big_container').style.width == "") {
    document.getElementById('cover_big_container').style.width = "100%";
    document.getElementById('cover_big_container').style.bottom = "80px";
    document.getElementById('cover_big_container').style.top = "0px";
  } else {
    hidebigcover();
  }
  event.stopPropagation();
}

function showbigquerycover(src) {
  src = src.replace("Thumbnails", "Covers");
  if (document.getElementById('query_cover_big_container').style.width == "0px" || document.getElementById('query_cover_big_container').style.width == "") {

    document.getElementById('query_cover_big_container').style.width = "100%";
    document.getElementById('query_cover_big_container').style.top = "0px";
  } else {
    hidebigcover();
  }

}

function hidebigcover() {

  sleep(1);
  document.getElementById('cover_big_container').style.width = "0px";
  document.getElementById('cover_big_container').style.bottom = "0px";
  document.getElementById('cover_big_container').style.top = "0px";
  document.getElementById('query_cover_big_container').style.width = "0px";
  document.getElementById('query_cover_big_container').style.bottom = "0px";
  document.getElementById('query_cover_big_container').style.top = "0px";

}

function iframeclick() {
  document.getElementById("doc").contentWindow.document.body.onclick = function () {
    document.getElementById('doc').style.left = "-100%";
    document.getElementById('doc').contentDocument.body.innerHTML = "";
  }
}


function select_item(el) {

  el = el.parentElement;
  if (el.classList.contains("query_track_item")) {
    el.classList.add("query_track_item_selected");
    el.classList.remove("query_track_item");
  } else {
    el.classList.add("query_track_item");
    el.classList.remove("query_track_item_selected");
  }
  ids = "";
  tracklist = document.getElementById('query_tracklist');
  for (var i = 0; i < tracklist.childElementCount; i++) {
    if (tracklist.children[i].classList.contains("query_track_item_selected")) {
      ids = ids + tracklist.children[i].attributes[2].value.toString() + ';';
    }
  }




  ids = ids.slice(0, -1);
  if (ids != "") {
    // Request the tags ...
    current_selected_ids = ids.split(";")
    Server_GetValues(ids.split(";"), query_tags, after_Server_Get_Query_Overview_select, null);
  } else {
    current_selected_ids = []
    Server_GetValues(current_ids, query_tags, after_Server_Get_Query_Overview_select, null);
  }
}

function select_item_parent(el) {
  el = el.parentElement;
  if (el.classList.contains("playlist_item")) {
    el.classList.add("playlist_item_selected");
    el.classList.remove("playlist_item");
  } else {
    el.classList.add("playlist_item");
    el.classList.remove("playlist_item_selected");
  }
}



function playlist_item_delete(e) {
 
}

function playlist_item_dragstart(e) {
  // don not delete current playing ...
  if (this.childNodes[5].src.includes("transparent")) {
    document.getElementById('playlist_item_delete_img').style.display = "block";
  } else {
    document.getElementById('playlist_item_delete_img').style.display = "none";
  }

  nbr = this.getAttribute("nbr");
  e.dataTransfer.setData('text/plain', nbr);
  setTimeout(() => {
    e.target.classList.add('hide');
  }, 0); // drag element disappears ...
  dragstart_nbr = this.getAttribute("nbr");
}


function playlist_item_dragenter(e) {

    console.log(this);

    if (this.className == "playlist_item") {

      var playlist_items = document.querySelectorAll('.playlist_item');
      playlist_items.forEach(function (item) {
        item.style.backgroundColor = "#0000001a";
      });
      this.style.backgroundColor = "#0000005a";
      dragend_nbr = this.getAttribute("nbr");
      document.getElementById('playlist_item_delete_img').style.backgroundColor = "#0000001a";


    }

    if (this.className == "playlist_item_delete") {
      var playlist_items = document.querySelectorAll('.playlist_item');
      playlist_items.forEach(function (item) {
        item.style.backgroundColor = "#0000001a";
      });
      this.style.backgroundColor = "#0000005a";
      dragend_nbr = -1;

    }

}

function playlist_item_dragleave(e) {

}


function playlist_item_dragend(e) {

    document.getElementById('playlist_item_delete_img').style.display = "None";
    console.log(this);
    if (dragstart_nbr != dragend_nbr && dragend_nbr != -1) {
      Server_Queue_Move_Ids(dragstart_nbr, dragend_nbr, after_Get_Queue);
    }
    if (dragend_nbr == -1) {
      Server_Queue_Delete_Id(dragstart_nbr, after_Get_Queue);
      document.getElementById('playlist_item_delete_img').style.backgroundColor = "#0000001a";
    }
 
}


function eachsecond() {
  if (window.playing == true) {
    window.position = window.position + 1000;
    if (window.position <= window.duration) {
      if (flipflopelapsedbool == false) {
        if (document.getElementById('time_total').innerHTML != "") {
          document.getElementById('time_elapsed').innerHTML = MsToMMSS(window.position);
        }
        else {
          document.getElementById('time_elapsed').innerHTML = "";
        }
      } else {
        if (document.getElementById('time_total').innerHTML != "") {
          document.getElementById('time_elapsed').innerHTML = MsToMMSS(window.position + queueelapse);
        }
        else {
          document.getElementById('time_elapsed').innerHTML = "";
        }
      }
    } else {
      //window.position > window.duration
    }

    if (window.duration == 0) {
      window.position = 0;
      document.getElementById('time_total').innerHTML = ""
      if (document.getElementById('time_total').innerHTML != "") {
        if (document.getElementById('time_total').innerHTML != "") {
          document.getElementById('time_elapsed').innerHTML = MsToMMSS(window.position);
        }
        else {
          document.getElementById('time_elapsed').innerHTML = "";
        }
      }
      else {
        document.getElementById('time_elapsed').innerHTML = "";
      }
    }
  }
}


function Goto_Browse_after_Reimport() {
  if (lastfield != "") {
    Server_find(lastquery, lastfield, lastsort, lastdisplay, after_Server_find, null);
  }
  Goto_Browse()
}

function Goto_Browse() {
  current_ids = [];
  files_queried = [];
  current_selected_ids = [];

  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  document.getElementById('playlist_container').style.left = "-150%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";

  document.getElementById('query_background').src = "img/transparent.png"
  document.getElementById('query_tracklist').innerHTML = "";
  document.getElementById('query_cover').src = "img/cd.png"
  document.getElementById('query_bigcoverimg').src = "img/cd.png"
  document.getElementById('title1').innerHTML = "";
  document.getElementById('query_images').innerHTML = "";
  document.getElementById('query_image').innerHTML = query_image_content;
  document.getElementById('query_text').innerHTML = "";
  document.getElementById('query_text').classList.remove("cls_query_text");

}


function goto_param() {
  document.getElementById("header_container").innerHTML = "";

  if (isCordova()) {
    window.location.href = "config.html";
  } else {
    window.location.href = "/html/config.html";
  }


  document.getElementById("library_btn").style.backgroundColor = "#00000000";
  document.getElementById("podcast_btn").style.backgroundColor = "#00000000";
  document.getElementById("radio_btn").style.backgroundColor = "#00000000";
  document.getElementById("param_btn").style.backgroundColor = "#c9c9c94f";
}

function goto_database() {
  document.getElementById("header_container").innerHTML = "";


  if (isCordova()) {
    window.location.href = "database.html";
  } else {
    window.location.href = "/html/database.html";
  }

  document.getElementById("library_btn").style.backgroundColor = "#00000000";
  document.getElementById("podcast_btn").style.backgroundColor = "#00000000";
  document.getElementById("radio_btn").style.backgroundColor = "#00000000";
  document.getElementById("param_btn").style.backgroundColor = "#c9c9c94f";
}

function goto_music_library() {
  level = 0;
  current_hub = "music_library";
  browsemenu = 0;
  header_line = []
  header_line.push(translate("library"));
  document.getElementById("header_container").innerHTML = header_line.join(' > ');

  Server_Get_Menu(menu_file, after_Get_Menu_Library, null);
  document.getElementById("library_btn").style.backgroundColor = "#c9c9c94f";
  document.getElementById("podcast_btn").style.backgroundColor = "#00000000";
  document.getElementById("radio_btn").style.backgroundColor = "#00000000";
  document.getElementById("param_btn").style.backgroundColor = "#00000000";
}

function goto_podcast() {
  level = 0;
  current_hub = "podcast";
  header_line = []
  header_line.push(translate("podcasts"));
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  Server_Get_Menu(menu_file, after_Get_Menu_Podcast, null);
  document.getElementById("library_btn").style.backgroundColor = "#00000000";
  document.getElementById("podcast_btn").style.backgroundColor = "#c9c9c94f";
  document.getElementById("radio_btn").style.backgroundColor = "#00000000";
  document.getElementById("param_btn").style.backgroundColor = "#00000000";
}

function goto_radio() {
  level = 0;
  current_hub = "radio";
  header_line = []
  header_line.push(translate("radios"));
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  Server_Get_Menu(menu_file, after_Get_Menu_Radio, null);
  document.getElementById("library_btn").style.backgroundColor = "#00000000";
  document.getElementById("podcast_btn").style.backgroundColor = "#00000000";
  document.getElementById("radio_btn").style.backgroundColor = "#c9c9c94f";
  document.getElementById("param_btn").style.backgroundColor = "#00000000";
}


function after_Server_Play_Radio() {

}


function setDisplay() {
  if (localStorage.hasOwnProperty('thumb_width')) {
    var w = parseInt(localStorage.getItem('thumb_width'));
    $('div.thumb').css("width", w);
    w = Math.round(w * 1.12);
    $('div.thumb').css("height", w);
  }
}


function after_error_onload_browse() {

  if (isCordova()) {
    window.location.href = "config.html";
  } else {
    window.location.href = "/html/config.html";
  }

}


function after_Scanning() {
  res = JSON.parse(this.response);
  scanning = res["scanning"];
  if (scanning == true) {
    document.getElementById('scanning_img').style.opacity = 1;
  } else {
    document.getElementById('scanning_img').style.opacity = 0;
  }
}

function browsepopstate(event) {
  hidebigcover();
  if (document.getElementById('doc').style.left == "0%") {
    document.getElementById('doc').style.left = "-100%";
    document.getElementById('doc').contentDocument.body.innerHTML = "";
    return;
  }

  if (document.getElementById('thumbs_container').style.left == "-150%") {
    Goto_Browse();
  } else {
    console.log("location change! : " + document.location);
    browse_back();
  }

};

function preventDefaults(e) {
  e.preventDefault()
  e.stopPropagation()
}

function handleDrop(e) {

  if (window.isAdmin == false) {
    return;
  }
  let dt = e.dataTransfer
  let files = dt.files

  //handleFiles_query(files)
}

function handleFiles(files) {
  ([...files]).forEach(uploadFile)
}

function uploadFile(file) {
  let url = window.addr + "/v1/UpdateCover";
  let formData = new FormData()
  authorizationBasic = ``;
  if (token != null ) {
  authorizationBasic = `Bearer ` + token;
  }

  formData.append('file', file)
  fetch(url, {
    method: 'POST',
    body: formData,
     headers: {
      'Authorization': authorizationBasic
    }
  })
    .then(() => {
      Server_Get_UpdatedImages(after_Upload_file)
    })
    .catch(() => {
      /* Error. Inform the user */
    })
}


function handleDrop_import(e) {

  if (window.isAdmin == false) {
    return;
  }

  let path = e.dataTransfer.files[0].path
  // Test values ...
  //path = "/home/fredele/.Player/mediafiles/Music/Disque 1/Classique/Orozco - Iberia, Albeniz"
  //path = "smb://fredele.local/music/Disque 1/Classique/Orozco - Iberia, Albeniz/"

  folder = ""
  if (path.includes("/Music/") == true) {
    folder = "Music/" + path.split("/Music/")[1];
  }
  if (path.includes("=music/") == true) {
    folder = "Music/" + path.split("=music/")[1];
  }
  // Folder commence par 'Music/...'
  if (folder != "") {
    Server_Import_Drop(folder);
  }
}


function handleDrop_query(e) {

  e.preventDefault();
  e.stopPropagation();


  let dt = e.dataTransfer
  let files = dt.files

  handleFiles_query(files)
}

function handleFiles_query(files) {
  ([...files]).forEach(uploadFile_query)
}

function uploadFile_query(file) {

 authorizationBasic = ``;
  if (token != null ) {
  authorizationBasic = `Bearer ` + token;
  }
  let url = window.addr + "/v1/UpdateCover?query=" + lastqueryview;

  let formData = new FormData()

  formData.append('file', file)
  fetch(url, {
    method: 'POST',
    body: formData,
     headers: {
      'Authorization': authorizationBasic
    }
  })
    .then(() => {
      Server_Get_UpdatedImages(after_Upload_file, null);
    })
    .catch(() => {
      /* Error. Inform the user */
    })
}



function after_Get_UpdatedImages() {
  res = JSON.parse(this.response);
  updatedimages = res

}

function after_Upload_file() {
  res = JSON.parse(this.response);
  updatedimages = res
  /*Update the Queue List ...*/
  Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
  Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist, null);
  Server_Player_CurrentTrack(format_info, "", after_Format_Display, null);

  if (lastqueryview != undefined && lastqueryview != "") {
    Server_Get_Covers(lastqueryview, after_Server_Get_Covers, null)
  }
}



function after_CurrentTrack_Playlist() {
  if (this.response == undefined) {
    return;
  };
  var responseObject = JSON.parse(this.response);
  if (responseObject.response == "Error") {
    return;
  };
  var display = responseObject.display;
  correctdisplay(display, "current_track_infos");
  volume = responseObject.volume * 100;
  document.getElementById("volume-progress-bar").style.width = volume + "%";

}

function after_Format_Display() {
  if (this.response == undefined) {
    return;
  };
  var responseObject = JSON.parse(this.response);
  val = responseObject.display
  if (val == "") {
    return;
  };
  if (val == undefined) {
    return;
  };
  kbps = val.split("*")[1].split("*")[0]
  res = val.split("*")[0] + Math.round(kbps / 1000) + " Kbps" + val.split("*")[2];
  if (Math.round(val.split("*")[1] / 1000) == 0) {
    res = val.split("*")[0] + val.split("*")[2];
  }

  document.getElementById('time_spacer').innerHTML = res;
  draw_transcode(queue[current_playing_position]);
}

// Corrects
function correctdisplay(display, name) {
  Array.from(document.getElementsByClassName(name)).forEach(el => {
    el.innerHTML = nettoyerSeparateurs(display);
  });

}


function mark_track() {
  var playliste = document.getElementById('playlist');
  if (playliste != null) {

    // Mark track
    for (var i = 0; i < playliste.children.length; i++) {
      idnbr = playliste.children[i].getAttribute("idnbr")
      playliste.children[i].children[2].src = "img/transparent.png"
      if (i == current_playing_position) {
        playliste.children[i].children[2].src = "img/volume.png"
      }


    }
  }
  Set_Covers()
  if (queue.length != 0) {
    id = queue[current_playing_position]["_id"]
    Server_TrackInfo(id, current_track_info, "json", after_current_track_info)
    Server_TrackInfo(id, track_info_1, "json", after_track_info_1)
    Server_TrackInfo(id, format_info, "", after_Format_Display, null);
  }

}

function after_current_track_info() {
  var responseObject = JSON.parse(this.response);
  display = responseObject["display"]
  Array.from(document.getElementsByClassName('display_str')).forEach(el => {
    el.innerHTML = display;
  })
}

function nettoyerSeparateurs(str) {
  return str
    .replace(/[\s/\\-]{2,}/g, ' / ')
    .replace(/\s+\/\s*/g, ' / ')
    .replace(/\/\s+/g, '/ ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}



function after_track_info_1() {
  var responseObject = JSON.parse(this.response);
  display = responseObject["display"]
  Array.from(document.getElementsByClassName('current_track_infos')).forEach(el => {
    el.innerHTML = nettoyerSeparateurs(display);
  })
}

function after_CurrentTrack() {
  if (this.response == undefined) {
    return;
  };
  if (this.response == "") {
    return;
  };

  var responseObject = JSON.parse(this.response);
  if (responseObject == "") {
    return;
  };
  if (responseObject["response"] == "Error") {

    return;
  }
  window.state = responseObject["state"];

  // scanning indicator
  var scanning = responseObject["scanning"];
  if (scanning == true) {
    document.getElementById('scanning_img').style.opacity = 1;
  } else {
    document.getElementById('scanning_img').style.opacity = 0;
  }


  // Set the cover for each class="cover"

  if ("dirhash" in responseObject) {
    if (updatedimages.indexOf(responseObject["dirhash"]) >= 0) {
      Array.from(document.getElementsByClassName('cover')).forEach(el => {
        el.src = Server_Get_Coverurl(responseObject.dirhash);
      });
      document.getElementById('playlist_background').src = Server_Get_Coverurl(responseObject.dirhash);

    } else {
      Array.from(document.getElementsByClassName('cover')).forEach(el => {
        el.src = Server_Get_Coverurl(responseObject.dirhash);
      });
      document.getElementById('playlist_background').src = Server_Get_Coverurl(responseObject.dirhash);
    }

  }


  if ("covers" in responseObject) {
    Array.from(document.getElementsByClassName('cover')).forEach(el => {
      el.src = responseObject.covers[0];
    });
    document.getElementById('playlist_background').src = responseObject.covers[0];

  }


  Array.from(document.getElementsByClassName('infos')).forEach(el => {
    el.innerHTML =

      responseObject.display

  });
  window.current_id = responseObject._id;
  queue_position = responseObject.queue_position;
  current_playing_position = queue_position;

  // Barre du player
  display = responseObject.display;
  correctdisplay(display, 'display_str');

  if ("dirhash" in responseObject) {
    coverurl = Server_Get_Coverurl(responseObject.dirhash) + "?uploadTime=" + Math.floor(Date.now() / 1000 / 10) * 10;
    coverurl2 = Server_Get_Coverurl(responseObject.dirhash)
  }
  if ("covers" in responseObject) {
    if (updatedimages.indexOf(responseObject["dirhash"]) >= 0) {
      coverurl2 = responseObject.covers[0] + "?uploadTime=" + Math.floor(Date.now() / 1000 / 10) * 10;
    } else {
      coverurl2 = responseObject.covers[0]
    }
  } else {
    coverurl = null;
  }

  Array.from(document.getElementsByClassName('cover-bckg')).forEach(el => {
    el.src = encodeURI(coverurl2);
  });
  Array.from(document.getElementsByClassName('cover')).forEach(el => {
    try {
      if (coverurl != null) { el.style.src = coverurl; }
    } catch (e) { el.style.src = "img/transparent.png" }
  });

  window.duration = 1000 * responseObject.duration;

  var playliste = document.getElementById('playlist');
  if (playliste != null) {

    // Mark track
    for (var i = 0; i < playliste.children.length; i++) {
      idnbr = playliste.children[i].getAttribute("idnbr")
      playliste.children[i].children[2].src = "img/transparent.png"
      if (i == current_playing_position) {
        playliste.children[i].children[2].src = "img/volume.png"
      }


    }
  }

  var arr = Array.from(document.getElementsByClassName('query_item_playing'));
  arr.forEach(child => {
    var idnbr = child.getAttribute("idnbr")
    if (idnbr == window.current_id) {
      child.src = "img/volume.png"
    } else {
      child.src = "img/transparent.png"
    }
  });


  //setTimeout(setdoclinks, 1000);


}

function setdoclinks() {
  var arr = Array.from(document.getElementsByClassName('artist'));
  arr.forEach(child => {
    var page = addr + "/Docs/artist/" + child.innerText + ".html";
    ifUrlExist(page, child, ifdocexists);
  });
}




function ifdocexists(url, el) {
  if (url != "") {
    el.onclick = function () {
      event.stopPropagation();
      navtodoc(url);
    };
    el.classList.add("color2");
  }
}

function navtodoc2(url) {
  event.stopPropagation();
  navtodoc(url);
}

function navtodoc(url) {
  thumbs = document.getElementById('thumbs_container');
  docframe = document.getElementById('doc');
  docframe.style.left = "0%";
  docframe.src = url;
}


function menuchange_Library(item) {
  lastfield = "";
  lastquery = "";
  lastsort = "";
  lastdisplay = "";
  menu_hide();
  header_line = [];
  header_line.push(translate("library"));
  txt = item.textContent;
  newheader_line = '<span class="color1">' + txt + '</span>'
  header_line.push(newheader_line)
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  menuw = document.getElementById("menu_items");
  children = menuw.children;
  for (var i = 0; i < children.length; i++) {
    children[i].classList.remove("menu_item_selected");
    children[i].classList.add("menu_item_deselected");
  }
  item.classList.remove("menu_item_deselected");
  item.classList.add("menu_item_selected");
  browsemenu = item.getAttribute("nbr");
  level = 0;
  server_find(browsemenu);
}

function after_Get_Menu_Library() {
  if (level != 0) {
    return;
  }
  res = this.response;
  menu = JSON.parse(res);
  construct_menu_Library(menu);
  menuw.children[0].classList.remove("menu_item_deselected");
  menuw.children[0].classList.add("menu_item_selected");

  header_line = [];
  header_line.push(translate("library"));
  txt = menuw.children[0].textContent;
  newheader_line = '<span class="color1">' + txt + '</span>'
  header_line.push(newheader_line)
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  level = 0;
  server_find(browsemenu);
}

function after_Get_Menu_Radio() {
  res = this.response;
  menu = JSON.parse(res);
  construct_menu_Radio(menu);
  header_line = []
  header_line.push(translate("radios"));
  header_line.push(menuw.children[0].innerHTML);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  menuw.children[0].classList.remove("menu_item_deselected");
  menuw.children[0].classList.add("menu_item_selected");

  //Select/display the first entry ...
  menuw = document.getElementById("menu_items");
  children = menuw.children;
  for (var i = 0; i < children.length; i++) {
    children[i].classList.remove("menu_item_selected");
    children[i].classList.add("menu_item_deselected");
  }

  item = menuw.children[0];
  item.classList.remove("menu_item_deselected");
  item.classList.add("menu_item_selected");
  name = item.getAttribute("name");
  file = item.getAttribute("file");
  console.log(file)
  Server_Get_Radio(file, after_Get_radio, null);


  if (!isCordova()) {
    history.pushState(menuw.children[0].innerHTML, "", null);
  }
}


function after_Get_Menu_Podcast() {
  res = this.response;
  menu = JSON.parse(res);
  construct_menu_Podcast(menu);
  header_line = []
  header_line.push(translate("podcasts"));
  header_line.push(menuw.children[0].innerHTML);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  menuw.children[0].classList.remove("menu_item_deselected");
  menuw.children[0].classList.add("menu_item_selected");

  // Select/display the frst entry ...
  menuw = document.getElementById("menu_items");
  children = menuw.children;
  for (var i = 0; i < children.length; i++) {
    children[i].classList.remove("menu_item_selected");
    children[i].classList.add("menu_item_deselected");
  }
  item = menuw.children[0];
  item.classList.remove("menu_item_deselected");
  item.classList.add("menu_item_selected");
  name = item.getAttribute("name");
  file = item.getAttribute("file");
  console.log(file)
  Server_Get_Podcast(file, after_Get_podcast, null);

  if (!isCordova()) {
    history.pushState(menuw.children[0].innerHTML, "", null);
  }

}



function after_Get_Queue() {
  if (this.status == 404) {
    return;
  }
  res = JSON.parse(this.response);
  queue = res["queue"]
  queue_position = res["position"]
  calc_queueelapse()
  var playliste = document.getElementById('playlist');
  playliste.innerHTML = "";
  var sumt = 0;
  var playlist_content = "";
  for (var i = 0; i < queue.length; i++) {
    track = queue[i];

    if (i == queue_position) {
      playingimg = "img/volume.png"
    } else {
      playingimg = "img/transparent.png"
    }
    title = track["display"];
    if ("covers" in track) {
      imgurl = track["covers"][0];
      delete track.dirhash
    } else if ("dirhash" in track) {
      imgurl = Server_Get_ThumbUrl(track["dirhash"]);
    } else {
      imgurl = "img/cd.png";
    }

    t = track["length"] * 1000;
    sumt = sumt + t;
    time = MsToMMSS(t);
    
      

    if (uap == "desk"){
    draggable = `draggable="true"`;
    }else{
    draggable = ``;
    }
  
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
    if (uap == "desk"){
    playlist_items.forEach(function (item) {
    
      item.addEventListener('dragstart', playlist_item_dragstart);
      item.addEventListener('dragend', playlist_item_dragend);
      item.addEventListener('dragleave', playlist_item_dragleave);
      item.addEventListener('dragenter', playlist_item_dragenter);
     
    }); // End foreach
    }
  }



function construct_menu_Radio(menu) {
  menuw = document.getElementById("menu_items");
  menuw.innerHTML = '';
  radios = menu["radios"];
  for (var i = 0; i < radios.length; i++) {
    menuitem = radios[i]
    title = menuitem["name"];
    title = title.replace("[size=$small$]", "");
    title = title.replace("[/size]", "");
    menuw.innerHTML = menuw.innerHTML +
      `
     <div class="menu_item menu_item_deselected" name=${radios[i].name} file=${radios[i].file} onclick= menuchange_Radio(this)>${title}</div>
    `;
  }

}

function construct_menu_Podcast(menu) {
  menuw = document.getElementById("menu_items");
  menuw.innerHTML = '';
  podcasts = menu["podcast"];
  for (var i = 0; i < podcasts.length; i++) {
    menuitem = podcasts[i]
    title = menuitem["name"];
    title = title.replace("[size=$small$]", "");
    title = title.replace("[/size]", "");
    menuw.innerHTML = menuw.innerHTML +
      `
     <div class="menu_item menu_item_deselected" name=${podcasts[i].name} file=${podcasts[i].file} onclick= menuchange_Podcast(this)>${title}</div>
    `;
  }


}

function construct_menu_Library(menu) {
  menuw = document.getElementById("menu_items");
  menuw.innerHTML = '';
  musics = menu["music"];
  for (var i = 0; i < musics.length; i++) {
    menuitem = musics[i]
    title = menuitem["name"];
    title = title.replace("[size=$small$]", "");
    title = title.replace("[/size]", "");
    menuw.innerHTML = menuw.innerHTML +
      `
     <div class="menu_item menu_item_deselected" nbr=${i} onclick= menuchange_Library(this)>${title}</div>
    `;
  }


}

function menuchange_Radio(item) {

  header_line = []
  header_line.push(translate("radios"));
  header_line.push(item.innerHTML);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  menu_hide();
  menuw = document.getElementById("menu_items");
  children = menuw.children;
  for (var i = 0; i < children.length; i++) {
    children[i].classList.remove("menu_item_selected");
    children[i].classList.add("menu_item_deselected");
  }
  item.classList.remove("menu_item_deselected");
  item.classList.add("menu_item_selected");
  name = item.getAttribute("name");
  file = item.getAttribute("file");
  console.log(file)
  Server_Get_Radio(file, after_Get_radio, null);
  if (!isCordova()) {
    history.pushState(item.innerHTML, "", null);
  }
}


function menuchange_Podcast(item) {
  selected_podcast = item;
  menu_hide();
  header_line = []
  header_line.push(translate("podcasts"));
  header_line.push(item.innerHTML);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  menuw = document.getElementById("menu_items");
  children = menuw.children;
  for (var i = 0; i < children.length; i++) {
    children[i].classList.remove("menu_item_selected");
    children[i].classList.add("menu_item_deselected");
  }
  item.classList.remove("menu_item_deselected");
  item.classList.add("menu_item_selected");
  name = item.getAttribute("name");
  file = item.getAttribute("file");
  console.log(file)
  Server_Get_Podcast(file, after_Get_podcast, null);
}


function after_Get_radio() {
  res = JSON.parse(this.response);
  window.scrollTo(0, 0);
  res = JSON.parse(this.response);
  res = res["items"];
  var thumbs_box = document.getElementById("thumbs_box");
  thumbs_box.innerHTML = '';
  for (var i = 0; i < res.length; i++) {
    var thumb = document.createElement('div');
    thumb.setAttribute('class', thumb_style);
    thumb.setAttribute('onclick', 'play_radio(this)');
    thumb.setAttribute('url', res[i]["url"]);
    thumb.setAttribute('covers', res[i]["covers"]);

    thumburl = res[i]["covers"][0]

    display = BBCodeToHtml(res[i]["display"]);

    var match = /\r|\n/.exec(display);
    if (!match) { } else {
      display = "<br>" + display;
    }

    thumb.innerHTML =
      `
          <img  class="thumbimg" loading="lazy" src="${thumburl}" onerror="this.src='img/cd.png'">
          <div class="thumbtitle"><span>${display}</span></div>

          `;
    thumb.setAttribute('title', display);
    thumbs_box.appendChild(thumb);
  }



  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }
  setDisplay();
}

function after_Get_podcast() {
  res = JSON.parse(this.response);
  window.scrollTo(0, 0);
  res = JSON.parse(this.response);
  res = res["items"];
  var thumbs_box = document.getElementById("thumbs_box");
  thumbs_box.innerHTML = '';
  for (var i = 0; i < res.length; i++) {
    var thumb = document.createElement('div');
    thumb.setAttribute('class', thumb_style);
    thumb.setAttribute('onclick', 'on_thumb_click_Podcast(this)');
    thumb.setAttribute('url', res[i]["url"]);
    thumb.setAttribute('covers', res[i]["covers"]);
    thumburl = res[i]["covers"][0]
    display = BBCodeToHtml(res[i]["display"])
    var match = /\r|\n/.exec(display);
    if (!match) { } else {
      display = "<br>" + display;
    }

    thumb.innerHTML =
      `
            <img  class="thumbimg" src="${thumburl}" loading="lazy" onerror="this.src='img/cd.png'">
            <div class="thumbtitle"><span>${display}</span></div>

            `;
    thumbs_box.appendChild(thumb);
  }

  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }
  setDisplay();
}

function server_find(browsemenu) {

  q = menu["music"][browsemenu]["query"];
  q = EncodePercentString(q);
  thumb_q = EncodePercentString(q);
  field = menu["music"][browsemenu]["levels"][level][0];
  sort = menu["music"][browsemenu]["levels"][level][1];
  display = menu["music"][browsemenu]["levels"][level][2];
  display = display.replace(/(?:\r\n|\r|\n)/g, '<br>');
  block = true;
  field_q = field;
  sort_q = sort;
  display_q = display;
  Server_find(q, field, sort, display, 0, req_thumb_cout, after_Server_find, null)
  qlevel[level] = q;
  lastquery = q;
}

function on_thumb_click_Podcast(thumb) {
  if (thumb.innerText == 'undefined') {
    return;
  };
  newheader_line = '<span class="color2">' + translate(thumb.innerText) + '</span>'
  header_line.push(newheader_line);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  rss = thumb.getAttribute("url");
  cover = thumb.getAttribute("covers");
  Server_Decode_Podcast(rss, cover, after_Server_Decode_Podcast, null);
  if (!isCordova()) {
    history.pushState(thumb.getAttribute("url"), "", null);
  }

}

function on_thumb_click_Radio(thumb) {
  if (thumb.innerText == 'undefined') {
    return;
  };
  newheader_line = '<span class="color1">' + translate(thumb.innerText) + '</span>'
  header_line.push(newheader_line);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  url = thumb.getAttribute("url");
}


function after_Server_Decode_Podcast() {

  window.scrollTo(0, 0);
  res = JSON.parse(this.response);
  var thumbs_box = document.getElementById("thumbs_box");
  thumbs_box.innerHTML = '';
  for (var i = 0; i < res.length; i++) {

    var thumb = document.createElement('div');
    thumb.setAttribute('class', thumb_style);
    thumb.setAttribute('onclick', 'play_podcast(this)');
    thumb.setAttribute('url', res[i]["url"]);
    l = HHMMSSToMs(res[i]["length"]) / 1000;
    thumb.setAttribute('length', l);
    thumb.setAttribute('covers', res[i]["covers"]);
    thumburl = res[i]["covers"][0]
    display = BBCodeToHtml(res[i]["display"])
    var match = /\r|\n/.exec(display);
    if (!match) { } else {
      display = "<br>" + display;
    }

    thumb.innerHTML =
      `
      <img  class="thumbimg" src="${thumburl}" loading="lazy" onerror="this.src='img/cd.png'">
      <div class="thumbtitle"><span>${display}</span></div>

      `;
    thumb.setAttribute('title', display);
    thumbs_box.appendChild(thumb);
  }

  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }

  setDisplay();
}


function on_thumb_click_Library(thumb) {
  lastthumb = thumb
  if (thumb.innerText == 'undefined') {
    return;
  };
  if (thumb.innerText == undefined) {
    return;
  };
  if (block == true) {
    return;
  }
  block = true;
  try {
    newheader_line = '<span class="color1 ' + thumb.children[1].children[0].className + '">' + translate(thumb.innerText) + '</span>'
  } catch { }
  // Not on last level
  if (level < menu["music"][browsemenu]["levels"].length - 1) {
    header_line.push(newheader_line);
  }
  document.getElementById("header_container").innerHTML = header_line.join(' > ');

  q = thumb.getAttribute("query");
  if (level + 1 < menu["music"][browsemenu]["levels"].length) {

    lastbrowsethumb = thumb;
    level = level + 1;
    field = menu["music"][browsemenu]["levels"][level][0];

    if (field.includes("$full")) {
      field = field.split("$")[0]
    }
    sort = menu["music"][browsemenu]["levels"][level][1];
    display = menu["music"][browsemenu]["levels"][level][2];
    display = display.replace(/(?:\r\n|\r|\n)/g, '<br>');
    lastquery = q;
    lastfield = field;
    lastsort = sort;
    lastdisplay = display;

    Server_find(q, field, sort, display, 0, req_thumb_cout, after_Server_find, null)

    qlevel[level] = q
  } else {
    window.queryview_last_query = q
    lastqueryview = q
    document.getElementById('thumbs_container').style.left = "-150%";
    document.getElementById('query_container').style.left = "0%";
    Server_Get_Covers(q, after_Server_Get_Covers, null)
  }

}


function on_thumb_click_Search(thumb) {
  document.getElementById('thumbs_container').style.left = "-150%";
  document.getElementById('query_container').style.left = "0%";
  q = thumb.getAttribute("query")
  window.queryview_last_query = q
  Server_Get_Covers(q, after_Server_Get_Covers, null)
}

function after_Server_Get_Covers() {
  var responseObject = JSON.parse(this.response);
  if (queue.length == 0) {
    document.getElementById('query_queue_btn').style.display = 'none';
  } else {
    document.getElementById('query_queue_btn').style.display = 'block';
  }
  dirhash = responseObject["dirhash"];
  dirname = responseObject["dirname"];
  thumb_q = responseObject["query"];
  document.getElementById('query_cover').src = Server_Get_ThumbUrl(dirhash);
  document.getElementById('query_background').src = Server_Get_ThumbUrl(dirhash);
  document.getElementById('query_bigcoverimg').src = Server_Get_Coverurl(dirhash);
  var divs = document.querySelectorAll(".item_query_cover");
  for (i = 0; i < divs.length; ++i) {
    divs[i].src = Server_Get_ThumbUrl(dirhash)
  }
  Server_Get_Group_Query(q, query_album_info, "json", after_Server_Get_Group_Query, null)
}

function tagmodal() {
  q = document.getElementById("albumaction").getAttribute("query");
}

function playmodal(thumb) {
  q = document.getElementById("albumaction").getAttribute("query");
  Server_Queue_Add_Query_Play(q, null, null);
  $("#albumaction").modal('hide');
}


function browse_to_level(lev) {
  if (block == true) {
    return;
  }
  block = true;
  menu_hide();
  level = lev;
  header_line = header_line.splice(0, 3 + 2 * lev);
  document.getElementById("header_container").innerHTML = header_line.join(' > ');
  field = menu["music"][browsemenu]["levels"][lev][0];
  sort = menu["music"][browsemenu]["levels"][lev][1];
  display = menu["music"][browsemenu]["levels"][lev][2].replace(/(?:\r\n|\r|\n)/g, '<br>');
  block = true;
  thumb_q = qlevel[lev]
  field_q = field;
  sort_q = sort;
  display_q = display;
  Server_find(thumb_q, field, sort, display, 0, req_thumb_cout, after_Server_find2, null);
  lastquery = qlevel[lev];
  q = qlevel[lev];
}


function after_Server_find2() {
  // Click sur les tag en haut de la fenêtre pour la navigation vers l' arrière
  window.scrollTo(0, 0);
  res = JSON.parse(this.response);
  resk = res.key
  res = res["result"];
  var thumbs_box = document.getElementById("thumbs_box");
  thumbs_box.innerHTML = '';
  for (var i = 0; i < res.length; i++) {
    var thumb = document.createElement('div');
    thumb.setAttribute('class', thumb_style);
    thumb.setAttribute('onclick', 'on_thumb_click_Library(this)');
    thumb.setAttribute('query', res[i]["query"]);
    thumb.setAttribute('keyval', res[i]["keyval"]);
    thumb.setAttribute('covers', res[i]["covers"]);
    thumburl = Server_Get_ThumbUrl(res[i]["covers"][0])
    display = BBCodeToHtml(res[i]["display"]);
    display = display.substring(0, 70);
    var match = /\r|\n/.exec(display);
    if (!match) { } else {
      display = "<br>" + display;
    }

    thumb.innerHTML =
      `
        <img  class="lozad thumbimg" src="${thumburl}" loading="lazy" draggable="false" onerror="this.src='img/cd.png'">
        <div class="thumbtitle"><span>${display}</span></div>

        `;
    thumbs_box.appendChild(thumb);
  }
  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }
  block = false;
  setDisplay();
}

function after_Server_find() {

  window.scrollTo(0, 0);
  if (this.response == undefined) {
    block = false;
    return;
  }
  res = JSON.parse(this.response);
  if (res["response"] == "No more pages") {
    var thumbs_box = document.getElementById("thumbs_box");
    thumbs_box.innerHTML = '';
    block = false;
    return;
  }

  key = res.key
  if (res["result"] == []) {
    return;
  };
  resk = res.key
  if (resk == "dirhash") {
    resk = "album"
  }
  if (resk == 'undefined') {
    return;
  };
  if (resk == undefined) {
    return;
  };
  newheader_line = '<span class="color2" onclick="javascript:event.stopPropagation();browse_to_level(' + level + ');">' + translate(resk) + '</span>'
  if (header_line.indexOf(newheader_line) <= -1) // Ne pas doubler ...
  {
    header_line.push(newheader_line);
  }
  document.getElementById("header_container").innerHTML = header_line.join(' > ');

  q = this.responseURL.split("=")[1];
  res = res["result"];
  var thumbs_box = document.getElementById("thumbs_box");
  thumbs_box.innerHTML = '';
  allcontent = "";
  for (var i = 0; i < res.length; i++) {

    if (updatedimages.indexOf(res[i]["covers"][0]) >= 0) {
      thumburl = Server_Get_ThumbUrl(res[i]["covers"][0])
    } else {
      thumburl = Server_Get_ThumbUrl(res[i]["covers"][0])
    }

    display = BBCodeToHtml(res[i]["display"]);
    display = display.substring(0, 70);
    var match = /\r|\n/.exec(display);
    if (!match) { } else {
      display = "<br>" + display;
    }

    coverurl = res[i]["covers"]
    content = '<div class="thumb" onclick="on_thumb_click_Library(this)" query="' + res[i]["query"] + '" keyval="' + res[i]["keyval"] + '" covers="' + coverurl + '" style="width: 135px; height: 151px;"><img class="yall_lazy thumbimg" draggable="false" data-src="' + thumburl + `" onerror="this.src='img/cd.png'"> <div class="thumbtitle"><span class=` + key + `_display >${display}</span></div></div>`
    allcontent = allcontent + content;
  }

  thumbs_box.innerHTML = allcontent;
  lazyload.run();
  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }
  block = false;
  //setTimeout(setdoclinks, 1000);
  setDisplay();
}


function reset_query_container() {
  current_selected_ids = []
  tracklist = document.getElementById('query_tracklist');
  for (var i = 0; i < tracklist.childElementCount; i++) {
    tracklist.children[i].classList.remove("query_track_item_selected")
  }
  try {
    document.getElementById('query_tracklist').innerHTML = "";
    document.getElementById('query_text').innerHTML = "";
    document.getElementById('query_cover').src = "img/cd.png";
    document.getElementById('query_overview').innerHTML = "";
    document.getElementById('title1').innerHTML = "";
    document.getElementById('query_images').innerHTML = "";
    document.getElementById('query_image').innerHTML = query_image_content;
    document.getElementById('query_overview_hidden').innerHTML = "";

    for (var i = 0; i < tracklist.childElementCount; i++) {
      tracklist.children[i].classList.remove("query_track_item_selected")
    }
  } catch (error) { }
}

function browse_back() {

  if (header_line[0] == "podcasts" && header_line.length == 3) {
    menuchange_Podcast(selected_podcast);
    return;
  }

  reset_query_container();
  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";


  if (level > 0) {
    header_line.pop();
    header_line.pop();
    document.getElementById("header_container").innerHTML = header_line.join(' > ');
    level = level - 1;
    field = menu["music"][browsemenu]["levels"][level][0];
    sort = menu["music"][browsemenu]["levels"][level][1];
    display = menu["music"][browsemenu]["levels"][level][2];
    display = display.replace(/(?:\r\n|\r|\n)/g, '<br>');
    q = qlevel[level];
    Server_find(q, field, sort, display, after_Server_find, null);
  }
}


function menu_display() {
  if (document.getElementById("menu_all").style.width == "80px") {
    menu_hide();
    return;
  }
  var playlist = document.getElementById('playlist_container');
  var thumbs = document.getElementById('thumbs_container');
  var query = document.getElementById('query_container');
  left = query.style.left;
  if (left == "" || left == "-150%") {
    document.getElementById("menu_container").style.width = "100%";
    document.getElementById("menu_items").style.width = "100%";
    document.getElementById("menu_all").style.width = "80px";

  }
  if (left == "0%") {

    playlist.style.left = "-150%";
    thumbs.style.left = "0%";
    query.style.left = "-150%";

    header_line.pop();
    document.getElementById("header_container").innerHTML = header_line.join(' > ');
  }
}

function menu_hide() {
  document.getElementById("menu_container").style.width = 0;
  document.getElementById("menu_items").style.width = 0;
  document.getElementById("menu_all").style.width = 0;
  document.getElementById("menu_hide").style.width = 0;
}

function setVolume() {
  document.getElementById("volume-progress-bar").style.width = 0;
}

function volume_hide() {
  document.getElementById("volume_background").style.width = 0;
  document.getElementById("volume_background").style.height = 0;
  document.getElementById("volume_container").style.width = 0;
  document.getElementById("volume_container").style.width = 0;
  document.getElementById("volume_background_top").style.width = 0;
  document.getElementById("volume_background_bottom").style.width = 0;
}

function changeimg(img) {
  imgs = document.getElementById('query_images').children;

  for (let item of imgs) {
    item.setAttribute("style", "");
  }

  img.setAttribute("style", "background-color:#0000008a");
  src = img.src
  src = src.split("?")[0] + "?thumbnail=" + window.sideimage_width;

  const imgElement = document.getElementById('query_image_img');
  imgElement.onload = function () {
    largeurFenetre = document.documentElement.clientWidth;
    largeurFenetre = document.getElementById('query_images').clientWidth;
    const nouvelleLargeur = largeurFenetre * 0.8;
    //imgElement.style.width = nouvelleLargeur + "px"
    document.getElementById('query_image_btn_previous').style.height = imgElement.height + "px";
    document.getElementById('query_image_btn_next').style.height = imgElement.height + "px";
  };
  document.getElementById('query_image_img').setAttribute("src", src);
  document.getElementById('query_image_img').setAttribute("nbr", img.getAttribute("nbr"));
}


function previousimg() {
  nbr = parseInt(document.getElementById('query_image_img').getAttribute("nbr"));
  nbr = nbr - 1;
  img = document.getElementById('query_images').children[nbr]
  if (img == undefined) {
    return;
  }
  for (let item of imgs) {
    item.setAttribute("style", "");
  }
  img.setAttribute("style", "background-color:#0000008a");
  src = img.src
  src = src.split("?")[0] + "?thumbnail=" + window.sideimage_width;
  document.getElementById('query_image_img').setAttribute("src", src);
  document.getElementById('query_image_img').setAttribute("nbr", img.getAttribute("nbr"));
}


function nextimg() {
  nbr = parseInt(document.getElementById('query_image_img').getAttribute("nbr"));
  nbr = nbr + 1;
  img = document.getElementById('query_images').children[nbr]
  if (img == undefined) {
    return;
  }
  for (let item of imgs) {
    item.setAttribute("style", "");
  }
  img.setAttribute("style", "background-color:#0000008a");
  src = img.src
  src = src.split("?")[0] + "?thumbnail=" + window.sideimage_width;
  document.getElementById('query_image_img').setAttribute("src", src);
  document.getElementById('query_image_img').setAttribute("nbr", img.getAttribute("nbr"));
}



function after_Server_Get_SideFiles() {
  var res = JSON.parse(this.response);
  document.getElementById('query_images').innerHTML = '';
  document.getElementById('query_image').innerHTML = query_image_content
  document.getElementById('query_images').classList.remove("cls_query_images");
  document.getElementById('query_text').innerHTML = "";
  document.getElementById('query_text').classList.remove("cls_query_text");
  let content = ""
  nbr = 0;
  res.images.forEach(
    function (element, index) {

      content = content +
        '<img nbr=' + index + ' data-src="' + window.serverurl + '/v1/SideFile' + element + '?thumbnail=150" class="yall_lazy sideimage"  onclick="changeimg(this)">'
    }
  );
  document.getElementById('query_images').innerHTML = content;

  if (res.images.length > 0) {

  }
  if ("text" in res) {
    source = `/v1/SideFile${res["text"]}`;
    document.getElementById('query_text').setAttribute("class", "cls_query_text");
    document.getElementById('query_text').innerHTML = decodeURIComponent(res["text"]);
  }

  lazyload.run();

  setTimeout(() => {
    Server_Get_GetValues(q, "dirname;dirhash", after_Server_Get_Query_Overview_hidden, null);
  }, 2000);

  makeLinksOpenInNewWindow();

}


function after_Server_Get_Files() {
  current_ids = []
  var trackliste = document.getElementById('query_tracklist');
  try {
    trackliste.innerHTML = "";
  } catch { }
  var responseObject = JSON.parse(this.response);
  display = responseObject["display"]
  // Fill the Files ...
  var sumt = 0;
  let text = "";
  for (var i = 0; i < display.length; i++) {

    track = display[i];
    current_ids.push(track._id)
    if (track._id == current_id) {
      playingimg = "img/volume.png"
    } else {
      playingimg = "img/transparent.png"
    }
    title = track["display"];
    track["file_addr"] = addr + "/" + track["dirname"] + "/" + track["filename"] + "." + track["extension"]

    files_queried.push(track)
    imgurl = ""
    if ("dirhash" in track) {
      if (updatedimages.indexOf(track["dirhash"]) >= 0) {
        imgurl = Server_Get_ThumbUrl(track["dirhash"]);
      } else {
        imgurl = Server_Get_ThumbUrl(track["dirhash"]);
      }
    }
    t = track["length"] * 1000;
    sumt = sumt + t;

    time = MsToMMSS(t);

    cl = "query_track_item"
    if (current_selected_ids.includes(track._id)) {
      cl = "query_track_item_selected"
    }

    text = text +
      `
     <div class=` + cl + ` nbr="${i}" idnbr="${track["_id"]}" >
      <img id= "" class=" item_query_cover" src="${imgurl}" loading="lazy" onerror="this.src='img/cd.png'">
      <div class="item_title_1"  onclick="select_item(this)" >${title}</div>
      <img id= "" class="query_item_playing" src="${playingimg}" loading="lazy" idnbr="${track["_id"]}" >
      <div class="item_time">${time}</div>
      <div class="file_addr">${track["file_addr"]}</div>
      </div>

    `;
  }
  trackliste.innerHTML = text;
  if (q.startsWith("query=")) {
    q = q.slice(6);
  }

  setTimeout(function () {
    Server_Get_SideFiles(q, after_Server_Get_SideFiles, null);
  }, 1000);

  block = false;
}

function after_Server_Get_Query_Overview_and_Files() {
  /*
  After editing the tag, retrieve tag values and the track list
  */
  document.getElementById('query_all').scrollTop = 0;
  var jsonresponse = JSON.parse(this.response);
  response = jsonresponse["values"]
  ids = jsonresponse["param"]["ids"]
  //const array = ids.split(';');
  //current_ids = [...new Set(array)];
  if (current_selected_ids.length == 0) {
    ids = current_ids
  } else {
    ids = current_selected_ids
  }
  i = 0
  l = response.length
  translated = {}
  for (var tag in response) {
    translated[translate(tag)] = tag
  }
  translated = Object.keys(translated).sort()
  invtranslated = {}
  for (var tag in response) {
    invtranslated[translate(tag)] = tag
  }
  var scontent = "";
  for (var tag of translated) {
    i += 1
    t = response[invtranslated[tag]];

    var value = "";
    var value2 = "";
    values = t["common_tags"].sort();
    for (const v of values) {
      value += '<span class="' + invtranslated[tag] + ' overview_element_' + invtranslated[tag] + '" >' + v + '</span>, ';
      value2 += v;
    }

    value = value.slice(0, -2);

    if (value != "") {
      if (value2.startsWith('http') == false) {
        scontent += `<div class="overview_element"  tag="` + invtranslated[tag] + `" onclick="show_tag_editor('` + invtranslated[tag] + `')" ><div  class="overview_tag">${translate(tag)}: </div><div class="overview_tag_value" >${value}</div></div>`;
      } else {
        scontent += '<a class="overview_element" target="_blank" href="' + value2 + '" tag="' + tag + '">' + translate(tag) + '</a>';
      }
    }
  }
  document.getElementById('query_overview').innerHTML = scontent;
  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }

  // Fills the track list in the Query view
  Server_Get_Files_ids(current_ids.join(";"), query_track_info, after_Server_Get_Files, null);
  Server_Get_Group_Ids(current_ids.join(";"), query_album_info, "json", after_Server_Get_Group_Ids, null);

  Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
  Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist, null);
  Server_Player_CurrentTrack(format_info, "", after_Format_Display, null);
}


function after_Server_Get_Query_Overview_select() {
  //Fills query overview
  var jsonresponse = JSON.parse(this.response);
  response = jsonresponse["values"]
  i = 0
  l = response.length
  translated = {}
  for (var tag in response) {
    translated[translate(tag)] = tag
  }
  translated = Object.keys(translated).sort()
  invtranslated = {}
  for (var tag in response) {
    invtranslated[translate(tag)] = tag
  }
  var scontent = "";
  for (var tag of translated) {
    i += 1
    t = response[invtranslated[tag]];

    var value = "";
    var value2 = "";
    values = t["common_tags"].sort();
    for (const v of values) {
      value += '<span class="' + invtranslated[tag] + " " + "overview_element_" + invtranslated[tag] + '">' + v + '</span>, ';
      value2 += v;
    }

    value = value.slice(0, -2);

    if (value != "") {
      if (value2.startsWith('http') == false) {
        scontent += `<div class="overview_element"  tag="` + invtranslated[tag] + `" onclick="show_tag_editor('` + invtranslated[tag] + `')" ><div  class="overview_tag">${translate(tag)}: </div><div class="overview_tag_value " >${value}</div></div>`;
      } else {
        scontent += '<a class="overview_element" target="_blank" href="' + value2 + '" tag="' + tag + '">' + translate(tag) + '</a>';
      }
    }
  }
  document.getElementById('query_overview').innerHTML = scontent;

}

function after_Server_Get_Query_Overview() {
  //Fills query overview
  var jsonresponse = JSON.parse(this.response);
  response = jsonresponse["values"]
  i = 0
  l = response.length

  translated = {}
  for (var tag in response) {
    translated[translate(tag)] = tag
  }
  translated = Object.keys(translated).sort()
  invtranslated = {}
  for (var tag in response) {
    invtranslated[translate(tag)] = tag
  }
  var scontent = "";
  for (var tag of translated) {
    i += 1
    t = response[invtranslated[tag]];
    var value = "";
    var value2 = "";
    values = t["common_tags"].sort();
    for (const v of values) {
      value += '<span class="' + invtranslated[tag] + " " + "overview_element_" + invtranslated[tag] + '">' + v + '</span>, ';
      value2 += v;
    }
    value = value.slice(0, -2);
    if (value != "") {
      if (value2.startsWith('http') == false) {
        scontent += `<div class="overview_element"  tag="` + invtranslated[tag] + `" onclick="show_tag_editor('` + invtranslated[tag] + `')" ><div  class="overview_tag">${translate(tag)}: </div><div class="overview_tag_value " >${value}</div></div>`;
      } else {
        scontent += '<a class="overview_element" target="_blank" href="' + value2 + '" tag="' + tag + '">' + translate(tag) + '</a>';
      }
    }
  }
  document.getElementById('query_overview').innerHTML = scontent;

  if (!isCordova()) {
    history.pushState(this.response, "", null);
  }
  Server_Get_Files_query(q, query_track_info, after_Server_Get_Files, null);
}


function draw_transcode(file) {
  if (file == undefined) {
    return;
  };
  if (file.hasOwnProperty('uri')) { } else {
    file["transcode"] = false;
    if (file.hasOwnProperty('uri') && typeof file.uri === 'string' && file.uri.includes('Transcode')) {
      file["transcode"] = true;
    }
    if (file.hasOwnProperty('file_addr') && typeof file.file_addr === 'string' && file.file_addr.includes('Transcode')) {
      file["transcode"] = true;
    }
  }
  try {
    const transcode = file["transcode"];
    for (const sp of ['.extension', '.bitrate']) {

      if (transcode === true) {
        const elements = document.querySelectorAll(sp);
        elements.forEach(el => {
          el.style.textDecoration = 'line-through';
          el.style.textDecorationColor = "#7f7f7f";
        });
      } else {
        const elements = document.querySelectorAll(sp);
        elements.forEach(el => {
          el.style.textDecoration = 'none';
        });
      }
    }
  } catch (e) {
    for (const sp of ['.extension', '.bitrate']) {
      const elements = document.querySelectorAll(sp);
      elements.forEach(el => {
        el.style.textDecoration = 'none';
      });
    }
  }
}



function display_hidden_buttons() {

  if (window.isAdmin == false) {
    return;
  }

  Array.from(document.getElementsByClassName('button_element_hidden')).forEach(el => {
    el.style.display = 'block';
  });

  Array.from(document.getElementsByClassName('overview_element_hidden')).forEach(el => {
    el.style.display = 'flex';
  });
}

function after_Server_Get_Query_Overview_hidden() {

  try {
    var jsonresponse = JSON.parse(this.response);
  } catch (e) {
    console.error("Erreur lors de l'analyse de la réponse JSON : ", e);
    return;
  }
  response = jsonresponse["values"]
  i = 0
  var scontent = "";
  scontent += `<div class="button_element" onclick="display_hidden_buttons()" ></div>`
  for (var tag in response) {

    t = response[tag];
    value = t["common_tags"].sort().join(", ");
    if (value != "" && tag != "dirname") {
      scontent += `<div class="overview_element_hidden"><div  class="overview_tag">${translate(tag)} : </div><div>${value}</div></div>`;
    } else if (tag == "dirname") {

      var v = value.replace("Music/Disque 1/", "");
      v = "/" + v;

      if (v == "/") {
        v = t["uncommon_tags"].sort().join(", ");
      }
      scontent += `<div class="overview_element_hidden"><div  class="overview_tag">` + translate("path") + ` : </div><div>${v}</div></div>`;

    }
  }

  param = jsonresponse["param"]
  if ('query' in param) {
    q = encodeURI(param["query"])
    var l = translate("Update");
    scontent += `<div class="button_element_hidden" onclick="Server_Reimport_Btn('` + q + `')" >` + l + `<div>`
  }

  document.getElementById('query_overview_hidden').innerHTML = scontent;
}

function Server_Reimport_Btn(query) {
  Server_Reimport_Query(query, after_Server_Reimport_Query);
  reset_query_container();
  reimport_query = query;
  Goto_Browse_after_Reimport();
}

function after_Server_Reimport_Query() {

}

function after_Server_Get_Group_Query() {
  //Fills query Title
  current_ids = []
  files_queried = []
  document.getElementById('query_all').scrollTop = 0;
  var responseObject = JSON.parse(this.response);
  display = responseObject["display"];
  correctdisplay(display, "query_title");
  block = false;
  setTimeout(() => {
    Server_Get_GetValues(q, query_tags, after_Server_Get_Query_Overview, null);
  }, 5);
}

function after_Server_Get_Group_Ids() {
  //Fills query Title after tag edition
  document.getElementById('query_all').scrollTop = 0;
  var responseObject = JSON.parse(this.response);
  display = responseObject["display"];
  correctdisplay(display, "query_title");
  block = false;
}


function Set_Covers_addr(addr) {

  document.getElementById('playlist_cover').src = addr;
  document.getElementById('coverimg').src = addr;
  document.getElementById('playlist_background').src = addr;
  document.getElementById('bigcoverimg').src = addr;

  Array.from(document.getElementsByClassName('cover-bckg')).forEach(el => {
    el.src = addr;
  });
}

function Set_Covers() {
  if (queue.length != 0) {
    dirhash = queue[current_playing_position]["dirhash"];
    addr = Server_Get_Coverurl(dirhash)
    document.getElementById('playlist_cover').src = addr;
    document.getElementById('coverimg').src = addr;
    document.getElementById('playlist_background').src = addr;
    document.getElementById('bigcoverimg').src = addr;
    Array.from(document.getElementsByClassName('cover-bckg')).forEach(el => {
      el.src = addr;
    });
  }
}




function browse_to_dirhash(dirhash) {

  if (block == true) {
    return;
  }
  block = true;

  document.getElementById('query_all').scrollTop = 0;
  document.getElementById('thumbs_container').style.left = "0%";
  reset_query_container();
  document.getElementById('query_container').style.left = "-150%";

  q = encodeURIComponent(' {"$and":[ {"dirhash" : ' + dirhash + '}]}')
  lastqueryview = q;
  Server_Get_Covers(q, after_Server_Get_Covers, null)

  hidebigcover();
  document.getElementById('thumbs_container').style.left = "-150%";
  document.getElementById('playlist_container').style.left = "-150%";
  document.getElementById('query_container').style.left = "0%";
}


function query_overview_mouse_over() {
  /* var arr = Array.from(document.getElementsByClassName('overview_element_hidden'));
   arr.forEach(el => {el.style.display = 'flex'});*/

}

function query_overview_mouse_out() {
  /*var arr = Array.from(document.getElementsByClassName('overview_element_hidden'));
  arr.forEach(el => {el.style.display = 'none'});*/
}


function show_tag_editor(tag) {
  if (window.isAdmin == false) {
    return;
  }

  if (server_mode == false) {
    return;
  };

  if (noneditable.indexOf(tag) < 0) {
    window.tageditormodal.style.display = "block";

    if (current_selected_ids.length == 0) {
      ids = current_ids
    } else {
      ids = current_selected_ids
    }
    Server_GetValues(ids, tag, editor_after_get_values)
  }
}

function show_dsp_editor() {
  window.outputmodal.style.display = "block";
}

function show_outputs() {

  if (localStorage.hasOwnProperty('web_transcode_active')) {
  } else {
    localStorage.setItem('web_transcode_active', false);
  }

  if (localStorage.hasOwnProperty('web_transcode_codec')) {
  } else {
    localStorage.setItem('web_transcode_codec', 'mp3');
  }

  if (localStorage.hasOwnProperty('web_transcode_bitrate')) {
  } else {
    localStorage.setItem('web_transcode_bitrate', '128');
  }


  document.getElementById("streaming_quality").value = localStorage.getItem("web_transcode_bitrate");
  document.getElementById("activate_streaming").checked = localStorage.getItem("web_transcode_active") === "true";

  if (!isCordova()) {
    document.getElementById('activate_streaming').disabled = true;
    localStorage.setItem("web_transcode_active", true);
    document.getElementById('activate_streaming').checked = true;
    web_transcode_active = true;
  }

  if (getExecutionContext() == 'internet') {
    return;
  }

  
  window.outputmodal.style.display = "block";
  document.getElementById("output_label").classList.add("disabled");
  document.getElementById("output_label").innerHTML = translate("searching players");
  if (window.current_player !== undefined) {

    if (window.current_player["type"] == "gstreamer") {
      document.getElementById("chooseoutput").style.display = "block";
      document.getElementById("choosestreaming").style.display = "none";
    }

    if (window.current_player["type"] == "upnp") {
      document.getElementById("chooseoutput").style.display = "none";
      document.getElementById("choosestreaming").style.display = "none";
    }

    if (window.current_player == "here") {
      document.getElementById("chooseoutput").style.display = "none";
      document.getElementById("choosestreaming").style.display = "block";
    }

  } else {
    document.getElementById("chooseoutput").style.display = "none";
    document.getElementById("choosestreaming").style.display = "none";
  }

  Server_Get_Players_Detected(after_Get_Players_Detected);
  Server_Get_Ouputs(after_Get_Output);
  Server_Get_Ouput_HW_params(after_Server_Get_Ouput_HW_params)
}



function edit_tag_value_changed() {
  document.getElementById('button_set_value').disabled = false;
  tag = document.getElementById('edit_tag').value;
  tag = invtranslated[tag]
  val = document.getElementById('edit_tag_value').value;

  if (singlevalue.indexOf(tag) >= 0) {
    if (val.indexOf(';') > -1) {
      document.getElementById('button_set_value').disabled = true;
    } else {
      document.getElementById('button_set_value').disabled = false;
    }
  }
}

// Before opening the tageditor modal window ..
function editor_after_get_values() {
  res = JSON.parse(this.response);
  tag = this.responseURL.split("tags=")[1].split("&")[0];
  document.getElementById('edit_tag').value = translate(tag);
  val = res["values"][tag]["common_tags"].sort().join(';');
  document.getElementById('edit_tag_value').value = val;
}


function after_find_files_query() {
  res = JSON.parse(this.response);
  var files = res["files"]

}

function Set_tag_value() {
  tag = document.getElementById('edit_tag').value.toLowerCase();
  if (invtranslated.hasOwnProperty(tag)) {
    tag = invtranslated[tag]
  }

  value = document.getElementById('edit_tag_value').value;

  if (current_selected_ids.length == 0) {
    ids = current_ids
  } else {
    ids = current_selected_ids
  }
  Server_set_tag(ids, tag, value, after_set_tag_value);
  document.getElementById('button_set_value').disabled = true;
  window.tageditormodal.style.display = "none";
}



function after_set_tag_value() {
  Server_ClearQueries(null, null);
  //TODO :clear history ...

  if (this.status != 200) {
    error = res["response"];
    document.getElementById('window.tageditormodal_error').innerHTML = "Error";
    return;
  } else {
    res = JSON.parse(this.response);
    //window.tageditormodal.style.display = "none";
    document.getElementById('edit_tag_value').value = "";
    document.getElementById('edit_tag').value = "";
  }
  tracklist = document.getElementById('query_tracklist');
  for (var i = 0; i < tracklist.childElementCount; i++) {
    tracklist.children[i].classList.remove("query_track_item_selected")
  }
  current_selected_ids.length = 0
  ids = current_ids
  Server_GetValues(ids, query_tags, after_Server_Get_Query_Overview_and_Files, null)
  // Reload last thumnnails view ...
  q = window.queryview_last_query
  Server_Get_Covers(window.queryview_last_query, after_Server_Get_Covers, null)
}




function after_CurrentTrack2() {
  try {
    after_CurrentTrack();
  } catch {
    
  }

  try {
    Server_Get_Queue(after_Get_Queue, null);
  } catch {
    
  }


}


function after_Get_Players_Detect() {
  if (window.current_player != "here") {
    Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
  }
  after_Get_Players(this.response);
  document.getElementById("output_label").classList.remove("disabled");
  document.getElementById("output_label").innerHTML = translate("choose a player");

}


function after_Get_Players_Detected() {
  after_Get_Players(this.response);
  document.getElementById("output_label").classList.remove("disabled");
  document.getElementById("output_label").innerHTML = translate("choose a player");
  //TODO: detect upnp players
  //Server_Get_Players_Detect(after_Get_Players_Detect)
}


function after_Get_Players(response) {
  html = ""
  txt = translate("Here");
  if (isCordova()) {
    html = html + `<a class="dropdown-item" nbr=-1 player_id="android" player_name="android" player_online="no" onclick=playerschangeandroid(this)>${txt}</a>`;
  } else {
    html = html + `<a class="dropdown-item" nbr=-1 player_id="web" player_name="web" player_online="no" onclick=playerschangeweb(this)>${txt}</a>`;
  }


  if (player_change_block == true) {
    player_change_block = false
    return
  }
  res = JSON.parse(response)
  players = res["players"]

  if (localStorage.getItem("current_player") !== null) {
    document.getElementById("chooseoutput").style.display = "block";
  }

  if (localStorage.getItem("current_player") !== null) {

    c = localStorage.getItem("current_player")
    if (c !== "here") {
      window.current_player = JSON.parse(c);
    } else {
      window.current_player = "here";
    }

    player = window.current_player;
  }
  if (getExecutionContext() == "internet") {
    player = window.current_player;
    document.getElementById("param_btn").style.display = "none";
  }

  playerdrop = document.getElementById("playerdrop");
  document.getElementById("chooseoutput").style.display = "none";
  playerdrop.innerHTML = '';


  if (getExecutionContext() != "internet" && window.executionlocation != "external"){
    document.getElementById("param_btn").style.display = "block";
    for (i = 0; i < players.length; i++) {
      
      name = players[i]["name"];
      id = players[i]["id"];
      saved = players[i]["saved"];
      if (saved == "yes") {
        cls = "saved"
      } else {
        cls = "discovered"
      }
      online = ""
      if (players[i].hasOwnProperty('online')) {
        if (players[i]["online"] == true) {
          online = " (online)"
          on = "1"
        }
        if (players[i]["online"] == false) {
          online = " (offline)"
          on = "0"
        }
      } else {
        on = "1"
      }

      if (players[i]["type"] == "gstreamer") {
        on = "1"
      }


      txt = name + online;
      html = html + `<a class="dropdown-item ` + cls + `" nbr=${i} player_id=${id} player_name=${name} player_online=${on} onclick=playerschange(this)>${txt}</a>`;
    } // End For
  }

  playerdrop.innerHTML = html
  try {
    var foundPlayer = res["players"].find(p => p.id === player.id);
  } catch (error) {
    var foundPlayer = null
  }

  if (foundPlayer != null) {
    if (init_player == true && player != "here") {
      Server_Set_Player(String(player.id), after_Server_Set_Player, null);
    
    }
   

    if (foundPlayer == "here") {

      document.getElementById("chooseoutput").style.display = "none";
      document.getElementById("choosestreaming").style.display = "block";

    }

    if (foundPlayer.type == "gstreamer") {
      document.getElementById("outputgstdropbtn").disabled = false;
      document.getElementById("chooseoutput").style.display = "block";
      document.getElementById("choosestreaming").style.display = "none";
      if (foundPlayer.online == "without") {
        document.getElementById("status").innerHTML = "status : OK"
      }
    }
    if (foundPlayer.type == "upnp") {
      document.getElementById("outputgstdropbtn").disabled = true;
      document.getElementById("chooseoutput").style.display = "none";
      document.getElementById("choosestreaming").style.display = "none";
      if (foundPlayer.online == true) {
        document.getElementById("status").innerHTML = "status : OK"
      } else {
        document.getElementById("playerdropbtn").innerHTML = "?"
        // Afficher la sélection d' un player
        if (getExecutionContext() != 'internet') {
          window.outputmodal.style.display = "block";
          document.getElementById("param_btn").style.display = "block";

        }
        return
      }
    }


    Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack2, null);
    Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist, null);
    Server_Player_CurrentTrack(format_info, "", after_Format_Display, null);

  } else { // if not foundPlayer ...
    if (player == "here") {
      document.getElementById("status").innerHTML = "status : OK"
      return;
    }
    document.getElementById("playerdropbtn").innerHTML = "?"
    // Select player for the first launch
    if (getExecutionContext() != "internet") {
      window.outputmodal.style.display = "block";
      document.getElementById("param_btn").style.display = "block";

    } else {
      // Select web player if online
      playerschangeweb(this);
    }
    return
  }


}




function playerschangeweb(item) {

  browsemenu = 0;

  localStorage.setItem("start_player_js", "js/browse_web.js");
  document.getElementById("playerdropbtn").innerHTML = translate("Here");
  //loadScript("js/browse_web.js", null );
  drawlevel("-60;-60");
  clear_ui();
  window.current_address = getBaseUrl(window.serverurl);
  document.getElementById("outputgstdropbtn").disabled = true;
  document.getElementById("chooseoutput").style.display = "none";
  document.getElementById("choosestreaming").style.display = "block";
  document.getElementById("streaming_quality").value = localStorage.getItem("web_transcode_bitrate");
  document.getElementById("activate_streaming").checked = localStorage.getItem("web_transcode_active") === "true";
  if (localStorage.hasOwnProperty('web_transcode_codec')) {
    window.web_codec = localStorage.getItem('web_transcode_codec');
  }
  else {
    localStorage.setItem('web_transcode_codec', 'mp3');
    window.web_codec = 'mp3';
  }

  if (localStorage.hasOwnProperty('web_transcode_bitrate')) {
    window.web_bitrate = localStorage.getItem('web_transcode_bitrate');
  }
  else {
    localStorage.setItem('web_transcode_bitrate', '128');
    window.web_bitrate = '128';
  }
  window.current_player = "here";
  localStorage.setItem("current_player", "here");
  document.getElementById("status").innerHTML = "status : OK"
  document.getElementById('activate_streaming').checked = true;
  document.getElementById('activate_streaming').disabled = true;
  document.getElementById("streaming_quality").value = window.web_bitrate;

  loadScript("js/browse_web.js", function () {
    onload_browse();
  });
}

function playerschangeandroid(item) {

  browsemenu = 0;
  localStorage.setItem("start_player_js", "js/browse_cordova.js");
  document.getElementById("playerdropbtn").innerHTML = translate("Here");
  //loadScript("js/browse_cordova.js", null );
  drawlevel("-60;-60");
  clear_ui();
  window.current_address = getBaseUrl(window.serverurl);
  document.getElementById("outputgstdropbtn").disabled = true;
  document.getElementById("chooseoutput").style.display = "none";
  document.getElementById("choosestreaming").style.display = "block";
  document.getElementById("streaming_quality").value = localStorage.getItem("web_transcode_bitrate");
  document.getElementById("activate_streaming").checked = localStorage.getItem("web_transcode_active") === "true";
  if (localStorage.hasOwnProperty('web_transcode_codec')) {
    window.web_codec = localStorage.getItem('web_transcode_codec');
  }
  else {
    localStorage.setItem('web_transcode_codec', 'mp3');
    window.web_codec = 'mp3';
  }

  if (localStorage.hasOwnProperty('web_transcode_bitrate')) {
    window.web_bitrate = localStorage.getItem('web_transcode_bitrate');
  }
  else {
    localStorage.setItem('web_transcode_bitrate', '128');
    window.web_bitrate = '128';
  }
  document.getElementById("outputgstdropbtn").disabled = true;
  document.getElementById("chooseoutput").style.display = "none";
  window.current_player = "here";
  localStorage.setItem("current_player", "here");
  loadScript("js/browse_cordova.js", function () {
    onload_browse();
  });

}

function playerschange(item) {
  document.getElementById("choosestreaming").style.display = "none";
  //browsemenu = 0;  //fredele
  clear_ui();
  try {
    loadScript("js/browse_players.js", after_playerschange(item));
  } catch (error) { }

}

function after_playerschange(item) {
  if (mediaplayer) {
    if (isCordova()) {
      mediastop = true;
      mediaplayer.stop(); // Arrête la lecture actuelle
      mediaplayer.release(); // Libère les ressources associées à cet objet 
    } else {
      mediaplayer.pause();
    }
  }

  player_change_block = true
  drawlevel("-60;-60");
  playerid = item.getAttribute("player_id");
  player_name = item.getAttribute("player_name");
  playernbr = item.getAttribute("nbr");
  playeronline = item.getAttribute("player_online");
  document.getElementById("playerdropbtn").innerHTML = item.getAttribute("player_name");
  playerdropbtn = document.getElementById("playerdropbtn");
  Server_Set_Player(playerid, after_Server_Set_Player, null)
  document.getElementById("status").innerHTML = "status : ..."
  Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
    el.src = "img/pause.png"
  });
}


function after_Server_Set_Player() {
  drawlevel("-60;-60");
  player_change_block = false;
  res = JSON.parse(this.response)
  window.current_player = res

  id = res["id"]
  name = res["name"]
  loaded = res["loaded"]
  online = res["online"]
  type = res["type"]

  if (type == "gstreamer") {
    document.getElementById("status").innerHTML = "status : OK";
    document.getElementById("outputgstdropbtn").disabled = false;
    document.getElementById("chooseoutput").style.display = "block";
  } else {
    document.getElementById("outputgstdropbtn").disabled = true;
    document.getElementById("chooseoutput").style.display = "none";
  }
  document.getElementById("playerdropbtn").innerHTML = name;

  document.getElementById("status").innerHTML = "status : OK"

  if (init_player == true) {
    init_player = false;
  } else {
    clear_ui();
  }
  Server_Get_Queue(after_Get_Queue, null);
  Server_Player_CurrentPosition(after_Player_CurrentPosition, null);
  Server_Player_CurrentTrack(current_track_info, "json", after_CurrentTrack, null);
  Server_Player_CurrentTrack(track_info_1, "json", after_CurrentTrack_Playlist, null);
  Server_Player_CurrentTrack(format_info, "", after_Format_Display, null);

  localStorage.setItem("current_player", JSON.stringify(window.current_player));

  if (window.state == "paused") {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/pause.png"
    });
  }

  if (window.state == "stopped") {
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/stop.png"
    });
  }

  if (online == false) {
    document.getElementById("status").innerHTML = "status :  not online";
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => {
      el.src = "img/playgrey.png"
    });
  }
  
   try{
  Server_Get_State(after_Server_get_State, null)
  }catch(error){}

}

function after_Server_Get_Ouput_HW_params() {
  res = JSON.parse(this.response);
  if (res["response"] == "OK") {
    document.getElementById('current_hw_params').innerHTML = ", " + res["format"] + "/" + res["rate"];
  } else {
    document.getElementById('current_hw_params').innerHTML = "";
  }

}

function after_Get_Output() {
  if (this.response == undefined) {
    return;
  };
  res = JSON.parse(this.response);
  outputsgst = res["outputs"];
  current = res["current"]
  document.getElementById('current_pipeline').innerHTML = outputsgst[current]["comment"];
  outputgstdrop = document.getElementById("outputgstdrop");
  outputgstdrop.innerHTML = '';

  for (var i = 0; i < outputsgst.length; i++) {
    title = outputsgst[i]["name"];
    outputgstdrop.innerHTML = outputgstdrop.innerHTML +
      `<a class="dropdown-item" nbr=${i} onclick= outputgstchange(this)>${title}</a>`;
  }
  outputgstdropbtn.innerHTML = res["outputs"][res["current"]]["name"]

}

function outputgstchange(item) {
  outputgstnbr = item.getAttribute("nbr");
  outputgstdropbtn = document.getElementById("outputgstdropbtn");
  outputgstdropbtn.innerHTML = outputsgst[outputgstnbr]["name"];
  Server_Set_Ouput(outputgstnbr, after_Server_Set_Ouput_gst, null)
}

function after_Server_Set_Ouput_gst() {
  res = JSON.parse(this.response)
  nbr = res["nbr"];
  outputdropbtn = document.getElementById("outputdropbtn");
  outputgstdropbtn.innerHTML = outputsgst[nbr]["name"];
  document.getElementById('current_pipeline').innerHTML = outputsgst[nbr]["comment"];

}

function clear_ui() {
  window.current_id = null
  Array.from(document.getElementsByClassName('cover-bckg')).forEach(el => {
    el.src = "img/transparent.png"
  });
  document.getElementById('playlist').innerHTML = "";
  document.getElementById('query_background').src = "img/transparent.png";
  document.getElementById('query_tracklist').innerHTML = "";
  document.getElementById('query_cover').src = "img/cd.png"
  document.getElementById('query_bigcoverimg').src = "img/cd.png"
  document.getElementById('coverimg').src = "img/cd.png"
  document.getElementById('playlist_cover').src = "img/transparent.png"
  document.getElementById('playlist_background').src = "img/transparent.png"
  document.getElementById('cti').innerHTML = "";
  document.getElementById('time_elapsed').innerHTML = "";
  document.getElementById('time_total').innerHTML = "";
  Array.from(document.getElementsByClassName('display_str')).forEach(el => {
    el.innerHTML = "";
  })

  var playlist = document.getElementById('playlist_container');
  var thumbs = document.getElementById('thumbs_container');
  var query = document.getElementById('query_container');
  playlist.style.left = "-150%";
  thumbs.style.left = "0%";
  query.style.left = "-150%";

}

function handleQualityChange() {
  val = document.getElementById("streaming_quality").value;
  window.web_bitrate = val;
  localStorage.setItem("web_transcode_bitrate", val);
};


function toggleStreaming() {
  checked = document.getElementById("activate_streaming").checked;
  localStorage.setItem("web_transcode_active", checked);
};

function thumbsbox_overflow() {
  /*
  Completes pagination while scrolling
  */
  flexContainer = document.getElementById('thumbs_container_2');
  const isOverflowing = flexContainer.scrollHeight > flexContainer.clientHeight;
  if (isOverflowing == false) {
    //Server_find(thumb_q,field_q,sort_q,display_q, page_nbr +1,req_thumb_cout,after_Server_find,null)
  }
  const isScrolledToBottom = flexContainer.scrollTop + flexContainer.clientHeight === flexContainer.scrollHeight;
  if (isOverflowing && isScrolledToBottom) {
    // Code to execute when the flexbox is scrolled to its maximum down
    //Server_find(thumb_q,field_q,sort_q,display_q, page_nbr +1,req_thumb_cout,after_Server_find,null)
  }
}

function set_overflow() {
  /*Completes pagination on Windows sizing*/
  flexContainer = document.getElementById('thumbs_container_2');
  const isOverflowing = flexContainer.scrollHeight > flexContainer.clientHeight;
  if (isOverflowing == false) {

  }
}
