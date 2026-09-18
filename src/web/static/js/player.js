


var playing = false
var current_id = "" ;
function onload_player()
{
  token = Server_GetToken();
  if (token != null)
  {
    Server_Player_CurrentTrack("$title$ <br> $album$ / $artist$",after_CurrentTrack,null);
    Server_Get_Queue(after_Get_Queue,null);
  }
}


function on_ws_msg(data)
{
  if (olddata == data) {
    return;
    };
  olddata = data;
  if (typeof data === 'string') {  if(data.startsWith("##") == true) { 
  
  data = data.slice(2);
  c(data);
  return;
   }}

  if (typeof data === 'string') {  if(data.startsWith("#") == true) { 
  data = data.slice(1);
  //drawlevel(data);
  return;
   }}
     
  if("message" in data)
  {
  var msg = data["message"];
  var val  = data["value"];

  if (msg == "mediafile_updated")
   {

   try {cancelabletimer.cancel();} catch (error) {}
   cancelabletimer = CancelableTimer( 3000);
   }


  if (msg == "SetNextAVT")
   {
   console.log("SetNextAVT")
   setnextav = val;
   }
   
  if (msg == "playlist changed")
   {
  Server_Get_Queue(after_Get_Queue,null);
   }

  if (msg == "auto import")
   {
     clearTimeout(myTimeOut);
     document.getElementById('scanning_img').style.opacity = 1;
     myTimeOut = setTimeout(function(){ 
      document.getElementById('scanning_img').style.opacity = 0;
       }, 3000);
   }

  if (msg == "audio changed")
   {
     // Reload the infos
     Server_Player_CurrentTrack(current_track_info,"json",after_CurrentTrack,null);
     Server_Player_CurrentTrack(track_info_1,"json",after_CurrentTrack_Playlist);
     Server_Player_CurrentTrack(format_info,"",after_Format_Display);
     setTimeout(() => {  Server_Player_CurrentPosition(after_Player_CurrentPosition,null);  }, 4000); // 1000, trop court ...
     setTimeout(() => {  Server_Player_CurrentPosition(after_Player_CurrentPosition,null);  }, 10000);
     //Remise a zero en pause
    
     window.position = 0
     console.log(window.position)
     console.log("audio changed")
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
     return;
   }

   if (msg == "end of stream")
   {
    playing = false
    document.getElementById('time_total').innerHTML  = "";   
    document.getElementById('time_elapsed').innerHTML  = ""; 
    var playliste = document.getElementById('playlist');
    for (var i = 0; i < playliste.children.length; i++) {playliste.children[i].children[2].src = "img/transparent.png"}
    Array.from(document.getElementsByClassName('display_str')).forEach(el =>  { el.innerHTML = "";})
    document.getElementById('time_spacer').innerHTML = "";
    Array.from(document.getElementsByClassName('current_track_infos')).forEach(el =>  { el.innerHTML = "";})
   }
   if (msg == "Calculating query")
   {
     console.log("Calculating query for hash " + val)

   } 

  if (msg == "state changed")
   {
    // Play Btns
    if (val == "playing"){
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Play"});
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/play.png"});
    playing = true
    } 
    else if (val == "paused"){
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Pause"});
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/pause.png"});
    playing = false
    }
    else if (val == "stopped"){
    playing = false
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.innerHTML = "Stop"});
    Array.from(document.getElementsByClassName('play_btn')).forEach(el => { el.src = "img/stop.png"});
    drawlevel("-60;-60");
    }   
    else{}

    }

   if(msg =='last player found')
   {
     Server_Get_Players_Detected(after_Get_Players_Detected);
   }
   } 
}





function after_CurrentTrack()
{
  var responseObject = JSON.parse(this.response);
  

  // Set the cover for each class="cover"
    Array.from(document.getElementsByClassName('cover')).forEach(el => { el.src  = Server_Get_Coverurl(responseObject.dirhash); });
    Array.from(document.getElementsByClassName('infos')).forEach(el => { el.innerHTML  = 

    responseObject.display
    
    });
  current_id = responseObject._id
  Array.from(document.getElementsByClassName('display_str_1')).forEach(el => { el.innerHTML  = responseObject.display; });
  //Array.from(document.getElementsByClassName('display_str_2')).forEach(el => { el.innerHTML  = responseObject.playing.artist; }); 
  dirhash = responseObject.dirhash;
  let coverurl = Server_Get_Coverurl(dirhash);
  
  Array.from(document.getElementsByClassName('cover-bckg')).forEach(el => { el.src = coverurl;  }); 
  Array.from(document.getElementsByClassName('cover')).forEach(el => { el.style.src = coverurl;  }); 
  
  
  // OR : playing, paused, stopped
  if(responseObject["state"] == "playing") {playing = true } else{ playing = false }
  window.position = responseObject.position;
  let hhmmssposition = MsToMMSS(window.position);
  document.getElementById('time_elapsed').innerHTML  =hhmmssposition; 
  document.getElementById('time_total').innerHTML  = MsToMMSS(responseObject.duration); 
  
  var playliste = document.getElementById('playlist');
  if (playliste != null)
  {
    console.log(playliste)
    // Mark track
    for (var i = 0; i < playliste.children.length; i++) {
      idnbr = playliste.children[i].getAttribute("idnbr")
      if (idnbr == responseObject["_id"])
      {
        playliste.children[i].children[2].src = "img/volume.png"
      }
      else
      {
        playliste.children[i].children[2].src = "img/transparent.png"
      }

    }
  }
}

