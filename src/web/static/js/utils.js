function CancelableTimer( delay) {
  let timerId;

  const timer = setTimeout(() => {
   
  if(document.getElementById('query_container').style.left == "0%"){
    if (current_selected_ids.length == 0) { ids=current_ids} else{ids= current_selected_ids}
    // correct display once DB has been updated
    Server_GetValues(ids, query_tags, after_Server_Get_Query_Overview_and_Files,null);
    Server_find(lastquery, lastfield, lastsort, lastdisplay,0,req_thumb_cout, after_Server_find, null);
    Server_Get_Queue(after_Get_Queue,null);  // Reload Queue ...


}
  }, delay);

  const cancel = () => {
    clearTimeout(timer);
  };

  return {
    cancel,
  };
}

function sleep(millis) {
  var date = new Date();
  var curDate = null;
  do {
    curDate = new Date();
  }
  while (curDate - date < millis);
}

function clone(obj) {
    if (null == obj || "object" != typeof obj) return obj;
    var copy = new obj.constructor;
    for (var attr in obj) {
        if (obj.hasOwnProperty(attr)) copy[attr] = obj[attr];
    }
    return copy;
}

function ifUrlExist(url,el, callback) {
    let request = new XMLHttpRequest;
    request.open('GET', url, true);
    request.send();
    request.onload = function() {
    status = request.status;
    if (request.status == 200) //if(statusText == OK)
    {
      console.log("url exists");
      return callback(url,el);
    } else {
      
      return callback("");
    }
    };
};



function getJsonFromUrl(url) {
  if(!url) url = location.href;
  var question = url.indexOf("?");
  var hash = url.indexOf("#");
  if(hash==-1 && question==-1) return {};
  if(hash==-1) hash = url.length;
  var query = question==-1 || hash==question+1 ? url.substring(hash) : 
  url.substring(question+1,hash);
  var result = {};
  query.split("&").forEach(function(part) {
    if(!part) return;
    part = part.split("+").join(" "); // replace every + with space, regexp-free version
    var eq = part.indexOf("=");
    var key = eq>-1 ? part.substr(0,eq) : part;
    var val = eq>-1 ? decodeURIComponent(part.substr(eq+1)) : "";
    var from = key.indexOf("[");
    if(from==-1) result[decodeURIComponent(key)] = val;
    else {
      var to = key.indexOf("]",from);
      var index = decodeURIComponent(key.substring(from+1,to));
      key = decodeURIComponent(key.substring(0,from));
      if(!result[key]) result[key] = [];
      if(!index) result[key].push(val);
      else result[key][index] = val;
    }
  });
  return result;
}

function replaceAll(s, find, replace) {
  return s.replace(new RegExp(find, 'g'), replace);
}


function BBCodeToHtml(str)
{   
    str = str.replace(/(?:\r\n|\r|\n)/g, '<br>');
    str = str.split('[').join('<');
    str = str.split(']').join('>');
    return str;
}

function EncodePercentString(s)
{
    // python eq : urllib.quote( query.encode(<value>))
    s = encodeURIComponent(JSON.stringify(s))
    // !! 
    s = replaceAll(s,"true","True")
    s = replaceAll(s,"false","False")
    return s
}

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}


function translateUI(){
read_vars();



var translateids = document.getElementsByClassName("to_translate");
for (let i = 0; i < translateids.length; i++ ) {

translateids[i].innerHTML = translate(translateids[i].innerHTML);
}
document.body.style.visibility = "visible";
}


function auto_height(elem) {  
    val = elem.scrollHeight
    valint = parseInt(val, 10) +5;
    val = valint.toString()
    elem.style.height = val+"px";
}





function isCordova() {
    return (typeof window.cordova !== "undefined");
  }
  
  
function getExecutionContext() {
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;

  // Cas 1 : exécuté depuis un fichier local
  if (protocol === "file:") {
    return "local_file";
  }

  // Cas 2 : localhost ou 127.0.0.1
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "local_host";
  }

  // Cas 3 : réseau local IP privé (192.168.x.x ou 10.x.x.x ou 172.16-31.x.x)
  const isPrivateIP =
    /^192\.168\./.test(hostname) ||
    /^10\./.test(hostname) ||
    /^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(hostname);

  if (isPrivateIP) {
    return "local_network";
  }

  // Cas 4 : accessible depuis Internet
  return "internet";
}


function normalizeCssUrl(value) {
  const match = value.match(/url\(["']?(.+?)["']?\)/);
  return match ? match[1] : value;
}
