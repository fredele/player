
function Get_translation()
{
Server_Get_Lang(after_Server_Get_Lang);
}

function after_Server_Get_Lang()
{
res = JSON.parse(this.response);
document.getElementById("translations").innerHTML = ""
document.getElementById("translations").innerHTML = JSON.stringify(res["lang"])
}


function retrieve_var(variable){
    content = localStorage.getItem(variable);
    document.getElementById(variable).value =  content;
}

function save_var(variable){
try{
val =  document.getElementById(variable).value;
localStorage.setItem(variable,val);
}catch(error){console.log("Error saving this variable")}
}


function onload(){

 if ( localStorage.hasOwnProperty('serverurl'))
  {
    window.serverurl =   localStorage.getItem("serverurl");
   }
   
 var browse_page = sessionStorage.getItem("browse_page");
 try{
 document.getElementById('browse_btn').setAttribute('href', browse_page);
 }catch{}
retrieve_vars();
translateUI();
}

function retrieve_vars(){

retrieve_var("sideimage_width");
retrieve_var("thumb_width");
retrieve_var("thumb_nbrs");
retrieve_var("query_track_info");
retrieve_var("track_info_1");
retrieve_var("queue_track_info");
retrieve_var("query_album_info");
retrieve_var("current_track_info");
retrieve_var("query_tags");
retrieve_var("singlevalue");
retrieve_var("noneditable");
if (localStorage.getItem('translations') != null) {
val  = localStorage.getItem('translations' );

document.getElementById('translations').innerHTML =  val;
}


auto_height(document.getElementById("query_track_info"))
auto_height(document.getElementById("track_info_1"))
auto_height(document.getElementById("queue_track_info"))
auto_height(document.getElementById("query_album_info"))
auto_height(document.getElementById("current_track_info"))
auto_height(document.getElementById("query_tags"))
auto_height(document.getElementById("singlevalue"))
auto_height(document.getElementById("noneditable"))
auto_height(document.getElementById("translations"))

}


function save_vars(){
username =  localStorage.getItem('username');
if(username != "admin"){
    el =document.getElementById("alert_error_span");
    el.innerHTML = "Not logged as admin !"

}

save_var("thumb_width");
save_var("thumb_nbrs");
save_var("sideimage_width");
save_var("query_track_info");
save_var("track_info_1");
save_var("queue_track_info");
save_var("query_album_info");
save_var("current_track_info");
save_var("query_tags");
save_var("singlevalue");
save_var("noneditable");

var trans =document.getElementById('translations').innerHTML;
trans = trans.replace(/(<|&lt;)br\s*\/*(>|&gt;)/g,' ');
localStorage.setItem('translations',trans);



retrieve_vars();
}



