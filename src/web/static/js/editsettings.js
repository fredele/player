function onload_settings()
{
 if ( localStorage.hasOwnProperty('serverurl'))
  {
    window.serverurl =   localStorage.getItem("serverurl");
   }
 var browse_page = sessionStorage.getItem("browse_page");
 try{
 document.getElementById('browse_btn').setAttribute('href', browse_page);
 }catch{}
 token = localStorage.getItem('token');
 translateUI();
Server_Get_Settings(after_Server_Get_Settings);
}

function after_Server_Get_Settings()
{
 res = JSON.parse(this.response);
 document.getElementById('tags_indexes').innerHTML = res["indexes"]
 document.getElementById('tags_singlevalues').innerHTML = res["singlevalue"]
 document.getElementById('tags_customtags').innerHTML = res["txxx"]
 document.getElementById('player_volume').innerHTML = res["volume"].toString();
auto_height(document.getElementById("tags_indexes"))
auto_height(document.getElementById("tags_singlevalues"))
auto_height(document.getElementById("tags_customtags"))
auto_height(document.getElementById("player_volume"))    
}

function save_settings()
{
  Server_Set_Settings (
  document.getElementById('tags_indexes').value,
  document.getElementById('tags_singlevalues').value,
  document.getElementById('tags_customtags').value,
  document.getElementById('player_volume').value
  )  
}

