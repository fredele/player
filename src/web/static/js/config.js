var token;
var addr;


function onload_config()
{
   var browse_page = sessionStorage.getItem("browse_page");
 try{
 document.getElementById('browse_btn').setAttribute('href', browse_page);
 }catch{}
 
  if (localStorage.getItem('username')!= null && localStorage.getItem('password')!= null) {
document.getElementById('username').value = localStorage.getItem('username');
document.getElementById('password').value = localStorage.getItem('password');
translateUI();
onload_server();
Server_Ports(after_server_ports);

}
}
  
function on_ws_msg(data)
{
  
}

function setToken()
{
  current_address = window.location.href;
  if (current_address.includes("https")) {var prot = "https://"} else {var prot = "http://"}
  var loginUrl = prot +document.location.hostname+":"+ document.location.port + "/v1/Login"
  var user = document.getElementById('username').value;
  var password = document.getElementById('password').value;
  var hash = btoa(user + ":" + password); 
  var authorizationBasic  = "Basic " + hash;
  var request = new XMLHttpRequest();
  request.open('GET', loginUrl , true)
  request.setRequestHeader('Authorization', authorizationBasic);
  request.addEventListener('load',after_setToken );
  request.send()
}


function after_setToken()
{
  var response = JSON.parse(this.response);
  if (response["response"] =="Error in login : {user:token} required ")
  { 
    Array.from(document.getElementsByClassName('configinfo')).forEach(el => { el.innerHTML = "No credentials for this user / password !"});
  }
  else
  {

  localStorage.setItem('username', document.getElementById('username').value);
  localStorage.setItem('password', document.getElementById('password').value);

  
  addr = "http://" +document.location.hostname+":"+ document.location.ip;
  localStorage.setItem('token', response.token);
  Array.from(document.getElementsByClassName('configinfo')).forEach(el => { el.innerHTML = "Authentication Token Set"});
  
  }
  
}

function after_server_ports()
{
 res = this.response;
 res = JSON.parse(res)
 addr = "Player Address : " +res.ip + ":" + res.httpport + "<br>" + "websocket on port : " + res.wsport
 try{
 document.getElementById('address').innerHTML = addr 
 }catch (e) {
  //console.error("Erreur lors de l'affichage de l'adresse du serveur : ", e);
}

}