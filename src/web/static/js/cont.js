function onload_control()
{
 var browse_page = sessionStorage.getItem("browse_page");
 try{
 document.getElementById('browse_btn').setAttribute('href', browse_page);
 }catch{}
 
  token = localStorage.getItem('token');
  translateUI();
  Server_Get_Commands(after_get_commands);
}

function after_get_commands()
{
 container = document.getElementById('maincontainer')
 res = JSON.parse(this.response);
 html = ""
 if (res.response == "OK")
 {
   commands =res.commands;
   for (var i = 0; i <commands.length; i++) {
     description = commands[i]["description"]
     command = commands[i]["command"]
   html += `<button type="button"  class="to_translate mt-2 btn  btn-lg bc"   onclick=Server_Run_Command("`+encodeURIComponent(command)+`") onsubmit="return false">`+description+`</button><br>`
   }

 container.innerHTML = html
 }
}

function after_run_commands()
{
  //
}