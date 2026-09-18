var current_player_id = null;

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
translateUI();
 document.getElementById('add-output-btn').addEventListener('click', addEmptyOutput);
 Server_Get_Players(after_Get_Players);
 Server_Get_Ouputs(after_Get_Ouputs);
}




function escapeHtml(str) {
  return String(str).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
}


function renderUpnpPlayers(players) {
  const container = document.getElementById('upnp-fill');
  // container.innerHTML = ''; // si tu veux réinitialiser complètement, décommente

  players.forEach(p => {
    // normaliser l'adresse au besoin (trim, lowercase si ce n'est pas une IP numérique, etc.)
    const addr = String(p.address).trim();

    // si un item avec la même adresse existe déjà, on skip
    if (container.querySelector(`[data-address="${CSS.escape(addr)}"]`)) {
      return;
    }

    const item = document.createElement('div');
    item.className = 'player-item';
    item.draggable = true;
    item.dataset.id = p.id;
    item.dataset.address = addr;

    item.innerHTML = `
      <div class="handle" aria-label="réordonner">&#x2630;</div>

      <div class="field-label name-label">Name</div>
      <div class="name-input-wrapper">
        <input class="name-input" type="text" value="${escapeHtml(p.name)}" aria-label="Nom du lecteur ${escapeHtml(p.name)}" />
      </div>

      <div class="field-label gapless-label">Gapless</div>
      <label class="checkbox-field">
        <input class="gapless-checkbox" type="checkbox" ${p.gapless === true || p.gapless === 'true' ? 'checked' : ''}>
      </label>

      <div class="field-label volume-label">Volume</div>
      <label class="checkbox-field">
        <input class="volume-checkbox" type="checkbox" ${p.volume_control === true || p.volume_control === 'true' ? 'checked' : ''}>
      </label>

      <div class="field-label transcode-label">Transcode</div>
      <label class="checkbox-field">
        <input class="transcode-checkbox" type="checkbox" ${p.transcode === true || p.transcode === 'true' ? 'checked' : ''}>
      </label>

      <div class="field-label codec-label">Codec</div>
      <select class="codec-select" aria-label="Codec de transcodage">
        <option value="mp3" ${p.codec === 'mp3' || p.codec === 'MP3' ? 'selected' : ''}>mp3</option>
        <option value="ogg" ${p.codec === 'ogg' || p.codec === 'OGG' ? 'selected' : ''}>ogg</option>
      </select>

      <div class="field-label bitrate-label">Bitrate</div>
      <select class="bitrate-select" aria-label="Bitrate de transcodage">
        <option value="128" ${String(p.bitrate || '128') === '128' ? 'selected' : ''}>128</option>
        <option value="192" ${String(p.bitrate || '128') === '192' ? 'selected' : ''}>192</option>
        <option value="256" ${String(p.bitrate || '128') === '256' ? 'selected' : ''}>256</option>
        <option value="320" ${String(p.bitrate || '128') === '320' ? 'selected' : ''}>320</option>
      </select>

      <button class="remove-btn" aria-label="Supprimer">-</button>
    `;

    // Drag & Drop events
    item.addEventListener('dragstart', (e) => {
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', p.id);
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
    });

    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      const dragging = container.querySelector('.dragging');
      if (!dragging || dragging === item) return;
      const rect = item.getBoundingClientRect();
      const after = (e.clientY - rect.top) > (rect.height / 2);
      if (after) {
        item.style['border-bottom'] = '2px solid #007bff';
        item.style['border-top'] = '';
      } else {
        item.style['border-top'] = '2px solid #007bff';
        item.style['border-bottom'] = '';
      }
    });
    item.addEventListener('dragleave', () => {
      item.style['border-bottom'] = '';
      item.style['border-top'] = '';
    });
    item.addEventListener('drop', (e) => {
      e.preventDefault();
      item.style['border-bottom'] = '';
      item.style['border-top'] = '';
      const draggedId = e.dataTransfer.getData('text/plain');
      if (!draggedId) return;
      const draggedEl = container.querySelector(`[data-id="${CSS.escape(draggedId)}"]`);
      if (!draggedEl || draggedEl === item) return;

      const rect = item.getBoundingClientRect();
      const after = (e.clientY - rect.top) > (rect.height / 2);
      if (after) {
        container.insertBefore(draggedEl, item.nextSibling);
      } else {
        container.insertBefore(draggedEl, item);
      }
    });

   // suppression
    item.querySelector('.remove-btn')?.addEventListener('click', () => {
      item.remove();
    });
    // disable si c' est le player en cours
    const removeBtn = item.querySelector('.remove-btn');
    if (String(p.id) === String(window.current_player_id)) {
      removeBtn.disabled = true;
      removeBtn.classList.add('disabled');
    }
   
    container.appendChild(item);
  });
}



function after_Get_Players(){

 const data = JSON.parse(this.response) ;
 try {
  current_player_id = data.player.id; 
 } catch (error) {
   
 } 
 
 let upnpPlayers = (data.players || []).filter(p => p.type === 'upnp');
  renderUpnpPlayers(upnpPlayers);
  
}


function search_upnp(){
  Server_Get_Players_Detect(after_Get_Players);

 }


function collectUpnpPlayers() {
  const container = document.getElementById('upnp-fill');
  const items = Array.from(container.querySelectorAll('.player-item'));
  
  const list = items.map((item, index) => {
    const id = index + 1; // numérotation incrémentale
    const address = item.dataset.address;
    const nameInput = item.querySelector('.name-input');
    const gaplessCheckbox = item.querySelector('.gapless-checkbox');
    const volumeCheckbox = item.querySelector('.volume-checkbox');
    const transcodeCheckbox = item.querySelector('.transcode-checkbox');
    const codecSelect = item.querySelector('.codec-select');
    const bitrateSelect = item.querySelector('.bitrate-select');

    return {
      id: String(id),
      type: 'upnp',
      name: nameInput ? nameInput.value.trim() : '',
      address: String(address || ''),
      volume_control: volumeCheckbox ? volumeCheckbox.checked : false,
      gapless: gaplessCheckbox ? gaplessCheckbox.checked : false,
      transcode: transcodeCheckbox ? transcodeCheckbox.checked : false,
      codec: codecSelect ? codecSelect.value : 'mp3',
      bitrate: bitrateSelect ? Number(bitrateSelect.value) : 128,
    };
  });

  return list;
}


function save_upnp() {

  players = collectUpnpPlayers()
   // Créer un objet JSON en texte
  res = {}
  res["players"] = players
  const jsonText = JSON.stringify(res, null, 2);

  // Préparer l'objet FormData avec un fichier virtuel
  const formData = new FormData();
  const blob = new Blob([jsonText], { type: "application/json" });
  formData.append("players_file", blob, "players");
  formData.append("filename", "players.json");

  const xhr = new XMLHttpRequest();
  xhr.open("POST", window.serverurl  + "/v1/Players/Set", true);

  xhr.onload = function () {
    if (xhr.status === 200) {
      console.log("Envoyé avec succès :", xhr.responseText);
    
    } else {
      console.error("Erreur d'envoi :", xhr.responseText);
      alert("Erreur lors de l'envoi !");
    }
  };

  xhr.onerror = function () {
    alert("Erreur réseau");
  };

  xhr.send(formData);
}


function save_outputs() {

  outputs = collectOutputs()
   // Créer un objet JSON en texte
  res = {}
  res["outputs"] =outputs
  const jsonText = JSON.stringify(res, null, 2);

  // Préparer l'objet FormData avec un fichier virtuel
  const formData = new FormData();
  const blob = new Blob([jsonText], { type: "application/json" });
  formData.append("outputs_file", blob, "outputs");
  formData.append("filename", "outputs.json");

  const xhr = new XMLHttpRequest();
  xhr.open("POST", window.serverurl  + "/v1/Outputs/Set", true);

  xhr.onload = function () {
    if (xhr.status === 200) {
      console.log("Envoyé avec succès :", xhr.responseText);
    
    } else {
      console.error("Erreur d'envoi :", xhr.responseText);
      alert("Erreur lors de l'envoi !");
    }
  };

  xhr.onerror = function () {
    alert("Erreur réseau");
  };

  xhr.send(formData);
}

function renderOutputs(outputs) {
  const container = document.getElementById('outputs-fill');
  container.innerHTML = ''; // reset

  outputs.forEach((o, idx) => {
    const item = document.createElement('div');
    item.className = 'output-item';
    item.dataset.index = idx;
    item.draggable = true;

    item.innerHTML = `
      <div class="line line-1">
        <div class="handle" aria-label="réordonner">&#x2630;</div>
        <div class="label name-label">Name</div>
        <input class="input name-input" type="text" value="${escapeHtml(o.name)}" aria-label="Name of output ${idx+1}" />
        <div class="label comment-label">Comment</div>
        <input class="input comment-input" type="text" value="${escapeHtml(o.comment)}" aria-label="Comment of output ${idx+1}" />
        <div class="spacer"></div>
      </div>
      <div class="line line-2">
        <div class="handle" aria-label="réordonner">&#x2630;</div>
        <div class="label gst-label">GST Pipeline</div>
        <input class="input gst-input" type="text" value="${escapeHtml(o.gstpipeline)}" aria-label="GStreamer pipeline of output ${idx+1}" />
        <button class="remove-btn" aria-label="Supprimer">-</button>
      </div>
    `;

    // Drag & Drop events
    item.addEventListener('dragstart', (e) => {
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      // on stocke un identifiant (ici l'ordre actuel : on peut utiliser un timestamp pour uniqueness)
      e.dataTransfer.setData('text/plain', item.dataset.index);
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      // nettoyer les bordures éventuelles
      container.querySelectorAll('.output-item').forEach(el => {
        el.style.borderTop = '';
        el.style.borderBottom = '';
      });
    });

    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      const dragging = container.querySelector('.dragging');
      if (!dragging || dragging === item) return;
      const rect = item.getBoundingClientRect();
      const after = (e.clientY - rect.top) > (rect.height / 2);
      if (after) {
        item.style.borderBottom = '2px solid #007bff';
        item.style.borderTop = '';
      } else {
        item.style.borderTop = '2px solid #007bff';
        item.style.borderBottom = '';
      }
    });
    item.addEventListener('dragleave', () => {
      item.style.borderBottom = '';
      item.style.borderTop = '';
    });
    item.addEventListener('drop', (e) => {
      e.preventDefault();
      item.style.borderBottom = '';
      item.style.borderTop = '';
      const draggedIndex = e.dataTransfer.getData('text/plain');
      if (draggedIndex == null) return;

      const draggingEl = container.querySelector(`.output-item[data-index="${CSS.escape(draggedIndex)}"]`);
      if (!draggingEl || draggingEl === item) return;

      const rect = item.getBoundingClientRect();
      const after = (e.clientY - rect.top) > (rect.height / 2);
      if (after) {
        container.insertBefore(draggingEl, item.nextSibling);
      } else {
        container.insertBefore(draggingEl, item);
      }

      // Réindexer dataset.index pour refléter l'ordre visuel
      Array.from(container.querySelectorAll('.output-item')).forEach((el, newIdx) => {
        el.dataset.index = newIdx;
      });
    });

    // suppression
    item.querySelector('.remove-btn')?.addEventListener('click', () => {
      item.remove();
      // réindexer après suppression
      Array.from(container.querySelectorAll('.output-item')).forEach((el, newIdx) => {
        el.dataset.index = newIdx;
      });
    });

    container.appendChild(item);
  });
}



// Fonction pour collecter l'état actuel (à envoyer au serveur)
function collectOutputs() {
  const container = document.getElementById('outputs-fill');
  const items = Array.from(container.querySelectorAll('.output-item'));
  return items.map(item => {
    return {
      name: item.querySelector('.name-input')?.value.trim() || '',
      comment: item.querySelector('.comment-input')?.value.trim() || '',
      gstpipeline: item.querySelector('.gst-input')?.value.trim() || ''
    };
  });
}


function after_Get_Ouputs() {
  const data = JSON.parse(this.response) ;
  outputs = data["outputs"];
  renderOutputs(outputs);
}


function addEmptyOutput() {
  const container = document.getElementById('outputs-fill');
  const idx = container.querySelectorAll('.output-item').length;
  const item = document.createElement('div');
  item.className = 'output-item';
  item.dataset.index = idx;
  item.draggable = true;

  item.innerHTML = `
    <div class="line line-1">
      <div class="handle" aria-label="réordonner">&#x2630;</div>
      <div class="label name-label">Name</div>
      <input class="input name-input" type="text" value="" aria-label="Name of output ${idx+1}" />
      <div class="label comment-label">Comment</div>
      <input class="input comment-input" type="text" value="" aria-label="Comment of output ${idx+1}" />
      <div class="spacer"></div>
    </div>
    <div class="line line-2">
      <div class="handle" aria-label="réordonner">&#x2630;</div>
      <div class="label gst-label">GST Pipeline</div>
      <input class="input gst-input" type="text" value="" aria-label="GStreamer pipeline of output ${idx+1}" />
      <button class="remove-btn" aria-label="Supprimer">-</button>
    </div>
  `;

  // Drag & Drop
  item.addEventListener('dragstart', (e) => {
    item.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.dataset.index);
  });
  item.addEventListener('dragend', () => {
    item.classList.remove('dragging');
    // nettoyer bordures
    container.querySelectorAll('.output-item').forEach(el => {
      el.style.borderTop = '';
      el.style.borderBottom = '';
    });
  });

  item.addEventListener('dragover', (e) => {
    e.preventDefault();
    const dragging = container.querySelector('.dragging');
    if (!dragging || dragging === item) return;
    const rect = item.getBoundingClientRect();
    const after = (e.clientY - rect.top) > (rect.height / 2);
    if (after) {
      item.style.borderBottom = '2px solid #007bff';
      item.style.borderTop = '';
    } else {
      item.style.borderTop = '2px solid #007bff';
      item.style.borderBottom = '';
    }
  });
  item.addEventListener('dragleave', () => {
    item.style.borderTop = '';
    item.style.borderBottom = '';
  });
  item.addEventListener('drop', (e) => {
    e.preventDefault();
    item.style.borderTop = '';
    item.style.borderBottom = '';
    const draggedIndex = e.dataTransfer.getData('text/plain');
    if (draggedIndex == null) return;
    const draggingEl = container.querySelector(`.output-item[data-index="${CSS.escape(draggedIndex)}"]`);
    if (!draggingEl || draggingEl === item) return;
    const rect = item.getBoundingClientRect();
    const after = (e.clientY - rect.top) > (rect.height / 2);
    if (after) {
      container.insertBefore(draggingEl, item.nextSibling);
    } else {
      container.insertBefore(draggingEl, item);
    }
    // réindexer
    Array.from(container.querySelectorAll('.output-item')).forEach((el, newIdx) => {
      el.dataset.index = newIdx;
    });
  });

  // suppression
  item.querySelector('.remove-btn')?.addEventListener('click', () => {
    item.remove();
    Array.from(container.querySelectorAll('.output-item')).forEach((el, newIdx) => {
      el.dataset.index = newIdx;
    });
  });

  container.appendChild(item);
}




 




