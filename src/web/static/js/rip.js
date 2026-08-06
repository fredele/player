function onload_rip()
{
    var browse_page = sessionStorage.getItem("browse_page");
 try{
 document.getElementById('browse_btn').setAttribute('href', browse_page);
 }catch{}
 token = localStorage.getItem('token');
  translateUI(); 
}