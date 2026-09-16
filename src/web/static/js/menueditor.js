let currentSelectedIndex = null;
let previousItem = null;
let draging = false;
let query_tags = null;

function onload_menu()
{
    var browse_page = sessionStorage.getItem("browse_page");
 try{
 document.getElementById('browse_btn').setAttribute('href', browse_page);
 }catch{}
 token = localStorage.getItem('token');
  translateUI();
  Server_Get_Menu("views.json", after_Get_Menu_Library, null);
}


function parseBool(value) {
  if (value === "true") return true;
  if (value === "false") return false;
  return value; // keep as-is if not a boolean string
}

function parseIntIfPossible(value) {
  if (typeof value !== "string") return value;

  const trimmed = value.trim();

  // Vérifie que c'est une chaîne représentant un entier (positif ou négatif)
  if (/^-?\d+$/.test(trimmed)) {
    return parseInt(trimmed, 10);
  }

  return value;
}
function bbcodeToHtml(text) {
  return text.replace(/\[size=(.+?)\](.*?)\[\/size\]/g, '<span class="size-$1">$2</span>');
}

function editableTagSelect(options = [], defaultValue = "") {
  const el = document.createElement("div");
  el.className = "select-editable";

  const sel = document.createElement("select");
  sel.className = "select-el";

  const inp = document.createElement("input");
  inp.type = "text";
  inp.name = "format";
  inp.value = defaultValue || "";
  inp.className = "select-input";

  // Synchroniser input quand on change de sélection
  sel.addEventListener("change", () => {
    inp.value = sel.value;
  });

  // Ajouter les options
  for (const optText of options) {
    const option = document.createElement("option");
    option.value = optText;
    option.textContent = optText;
    sel.appendChild(option);
  }

  el.appendChild(sel);
  el.appendChild(inp);
  return el;
} 

function after_Get_Menu_Library() {
  try {
    query_tags = localStorage.getItem("query_tags").split(';').filter(item => item !== "");
    
    const jsonText = this.response;
    const menu = JSON.parse(jsonText);
    console.log("Menu JSON chargé :", menu);
    currentMenu = menu;
    renderItems(menu);
    
    // Select first item
    currentSelectedIndex = 0
    renderQuery(menu.music[0]);
    renderLevels(menu.music[0]);
    document.querySelectorAll(".item-entry")[0].classList.add("selected");


    // "+" button for item
    document.querySelector("#item .add-button-item").addEventListener("click", () => {
      if (!currentMenu) return;

      // Détermine le hub courant (par défaut 'music')
      const hub = (window.current_hub || 'music');

      if (hub === 'videos') {
        // Assure l'existence du tableau videos
        if (!Array.isArray(currentMenu.videos)) currentMenu.videos = [];
        currentMenu.videos.push({ name: "", query: {}, levels: [] });
        // renderItems attend un objet avec la clé 'music'
        renderItems({ music: currentMenu.videos });
        // sélectionner le nouvel item si présent
        const idx = currentMenu.videos.length - 1;
        if (idx >= 0) {
          currentSelectedIndex = idx;
          renderQuery(currentMenu.videos[idx]);
          renderLevels(currentMenu.videos[idx]);
          const entries = document.querySelectorAll(".item-entry");
          if (entries[idx]) entries[idx].classList.add("selected");
        }
      } else {
        // hub 'music' ou autre -> comportement historique
        if (!Array.isArray(currentMenu.music)) currentMenu.music = [];
        currentMenu.music.push({ name: "", query: {}, levels: [] });
        renderItems(currentMenu);
        const idx = currentMenu.music.length - 1;
        if (idx >= 0) {
          currentSelectedIndex = idx;
          renderQuery(currentMenu.music[idx]);
          renderLevels(currentMenu.music[idx]);
          const entries = document.querySelectorAll(".item-entry");
          if (entries[idx]) entries[idx].classList.add("selected");
        }
      }
    });
  } catch (e) {
    console.error("Erreur lors du parsing du menu JSON :", e);
  }
}

function renderQuery(item) {
  const container = document.querySelector("#query-body");
  container.innerHTML = "";

  const queryList = item.query?.$and || [];

  queryList.forEach((condition, index) => {
    const line = document.createElement("div");
    line.className = "query-line";

    // Préparation de l'entrée
    const fieldName = Object.keys(condition)[0];
    const value = condition[fieldName];

    // Déterminer opérateur + valeur
    let operator = "";
    let val = "";

    if (typeof value === "object" && value !== null) {
      if ("$exists" in value) {
        operator = "exists"
        val = value["$exists"];
      } else if ("$gt" in value) {
        operator = ">";
        val = value["$gt"];
      } else if ("$lt" in value) {
        operator = "<";
        val = value["$lt"];
      } else if ("$gte" in value) {
        operator = ">=";
        val = value["$gte"];
      } else if ("$lte" in value) {
        operator = "<=";
        val = value["$lte"];
      }
    } else {
      operator = "=";
      val = value;
    }

    // Créer les composants éditables
    const fieldSelect = editableTagSelect(query_tags, "");
    fieldSelect.classList.add("query-field");
    fieldSelect.querySelector("input").value = fieldName;

    const operatorSelect = editableTagSelect([ "=",">","<",">=","<=","exists"],"");
    operatorSelect.classList.add("query-operator");
    operatorSelect.querySelector("input").value = operator;
    if (operator === "exists"){
    var valueSelect = editableTagSelect(["true","false"],"");
    }
    else{
    var valueSelect = editableTagSelect([],"");  
    }
    valueSelect.classList.add("query-value");
    valueSelect.querySelector("input").value = val;

    // Bouton "-"
    const removeBtn = document.createElement("button");
    removeBtn.className = "query-remove";
    removeBtn.textContent = "−";
    removeBtn.onclick = () => {
      line.remove(); 
    };
    line.appendChild(fieldSelect);
    line.appendChild(operatorSelect);
    line.appendChild(valueSelect);
    line.appendChild(removeBtn);

    container.appendChild(line);
  });

  const addBtn = document.querySelector("#query .add-button");
if (addBtn) {
  addBtn.onclick = () => {
    // Créer une ligne vide
    const line = document.createElement("div");
    line.className = "query-line";

    const field = editableTagSelect();
    field.classList.add("query-field");

    const operator = editableTagSelect();
    operator.classList.add("query-operator");
    operator.querySelector("input").value = "=";

    const value = editableTagSelect();
    value.classList.add("query-value");

    const removeBtn = document.createElement("button");
    removeBtn.className = "query-remove";
    removeBtn.textContent = "−";
    removeBtn.onclick = () => {
      line.remove();
    };
    line.appendChild(field);
    line.appendChild(operator);
    line.appendChild(value);
    line.appendChild(removeBtn);

    const container = document.querySelector("#query-body");
    container.appendChild(line);
  };
}

}


function renderLevels(item) {
  const container = document.querySelector("#levels-body");
  container.innerHTML = "";

  const levelsList = item.levels || [];

  levelsList.forEach((level, index) => {
    const levelelement = document.createElement("div");
    levelelement.className = "level-line";

    const line = document.createElement("div");
    line.className = "level-line1";

    const tag = level[0] || "";
    const sort = level[1] || "";
    const format = level[2] || "";

    // 1re ligne : tag, sort, sorttag
    const inputTag = editableTagSelect(query_tags, "");
    inputTag.classList.add("level-tag");
    inputTag.querySelector("input").value = tag;

    const selectSort = editableTagSelect(["ASC","DESC"],"");
    selectSort.classList.add("level-sort");
    selectSort.querySelector("input").value = sort.split("$")[1].substring(0,3);

    const inputSortTag = editableTagSelect(query_tags, "");
    inputSortTag.classList.add("level-sorttag");
    inputSortTag.querySelector("input").value = sort.replace(/\$ASCENDING|\$DESCENDING/, "");

    const spacer = document.createElement("div");
    spacer.className = "level-spacer";
    
    line.appendChild(inputTag);
    line.appendChild(selectSort);
    line.appendChild(inputSortTag);
    line.appendChild(spacer);
    levelelement.appendChild(line);

    // 2e ligne : affichage format + bouton
    const line2 = document.createElement("div");
    line2.className = "level-line2";

    const displayTag = document.createElement("input");
    displayTag.className = "level-display";
    displayTag.value = format;

    const removeBtn = document.createElement("button");
    removeBtn.className = "level-remove";
    removeBtn.textContent = "−";
    removeBtn.onclick = () => levelelement.remove();
    line2.appendChild(displayTag);
    line2.appendChild(removeBtn);

    levelelement.appendChild(line2);

    container.appendChild(levelelement);
  });

  const addBtn = document.querySelector("#levels .add-button");
if (addBtn) {
  addBtn.onclick = () => {
    const levelelement = document.createElement("div");
    levelelement.className = "level-line";

    const line1 = document.createElement("div");
    line1.className = "level-line1";

    const tag = editableTagSelect();
    tag.classList.add("level-tag");

    const sort = editableTagSelect();
    sort.classList.add("level-sort");
    sort.querySelector("input").value = "ASC";

    const sortTag = editableTagSelect();
    sortTag.classList.add("level-sorttag");

    line1.appendChild(tag);
    line1.appendChild(sort);
    line1.appendChild(sortTag);
    levelelement.appendChild(line1);

    const line2 = document.createElement("div");
    line2.className = "level-line2";

    const display = document.createElement("input");
    display.className = "level-display";

    const removeBtn = document.createElement("button");
    removeBtn.className = "level-remove";
    removeBtn.textContent = "−";
    removeBtn.onclick = () => levelelement.remove();

    line2.appendChild(display);
    line2.appendChild(removeBtn);

    levelelement.appendChild(line2);

    const container = document.querySelector("#levels-body");
    container.appendChild(levelelement);
  };
}

}

function handleItemClick(itemDiv, index, item, menu) {
  // Supprime la classe "selected" de tous les items
  document.querySelectorAll(".item-entry").forEach(el => {
    el.classList.remove("selected");
  });

  // Ajoute la classe "selected" à l'item cliqué
  itemDiv.classList.add("selected");

  // Mémorise l'index sélectionné
  selectedItemIndex = index;

}

function renderItems(menu) {
  const itemList = document.getElementById("item-list");
  itemList.innerHTML = "";
  var items = menu.music; // ou menu.video / menu.image selon besoin

items.forEach((item, index) => {
  const entry = document.createElement("div");
  entry.className = "item-entry";
  entry.draggable = true;
  entry.dataset.index = index;

  // Zone content
  const content = document.createElement("div");
  content.className = "item-content";

  const inputTitle = document.createElement("input");
  inputTitle.className = "item-title";
  inputTitle.value = item.name.split('\n')[0] || "";

  const inputDesc = document.createElement("input");
  inputDesc.className = "item-description";
  inputDesc.value = (item.name.split('\n')[1]) || "";

  content.appendChild(inputTitle);
  content.appendChild(inputDesc);

  // Zone bouton
  const buttonZone = document.createElement("div");
  buttonZone.className = "item-button";

  const removeBtn = document.createElement("button");
  
  removeBtn.className = "item-remove";
  removeBtn.textContent = "−";
  removeBtn.addEventListener("click", () => {
    event.stopPropagation();
    items.splice(index, 1); // supprime l'item
    renderItems(menu); // recharge la liste
    if(index == currentSelectedIndex){
    document.getElementById("query-body").innerHTML = "";
    document.getElementById("levels-body").innerHTML = "";
    }
  });

  buttonZone.appendChild(removeBtn);

  // Assembler tout
  entry.appendChild(content);
  entry.appendChild(buttonZone);4
  itemList.appendChild(entry);

  // Drag & drop (inchangé)
  entry.addEventListener("dragstart", (e) => {
    var container = document.querySelector("#query-body");
    draging = true;

    if(index == currentSelectedIndex){
    item.query = extractQueryFromDOM();
    item.levels = extractLevelsFromDOM();
    }

    e.dataTransfer.setData("text/plain", index);
  });
  
/*
  entry.addEventListener("dragover", (e) => {
    e.preventDefault();
    entry.style.borderTop = "2px solid black";
  });

  entry.addEventListener("dragleave", () => {
    entry.style.borderTop = "";
  });
*/
  
  entry.addEventListener("drop", (e) => {
    e.preventDefault();
    entry.style.borderTop = "";
    const fromIndex = parseInt(e.dataTransfer.getData("text/plain"));
    const toIndex = parseInt(entry.dataset.index);
    if (fromIndex !== toIndex) {
      const moved = items.splice(fromIndex, 1)[0];
      items.splice(toIndex, 0, moved);
      renderItems(menu);
       
    }
  });
  
  entry.addEventListener("click", function () {
  handleItemClick(entry, index, item, menu);
  if (currentSelectedIndex !== null) {
    // Sauvegarder les modifications de l'item précédent
    previousItem = items[currentSelectedIndex];
    if (typeof(previousItem)!= "undefined")
    {
    if(draging == false){
    previousItem.query = extractQueryFromDOM();
    previousItem.levels = extractLevelsFromDOM();
    }
    else
    {
    draging = false;
    }
      
    }
  }

  // Mettre à jour l’index courant
  currentSelectedIndex = index;

  // Afficher le nouvel item
  renderQuery(item);
  renderLevels(item);
});
  
  
 });
}

function extractNameAndDescription() {
  const itemEntries = document.querySelectorAll("#item-list .item-entry");
  return Array.from(itemEntries).map(entry => {
    const title = entry.querySelector(".item-title").value.trim();
    const desc = entry.querySelector(".item-description").value.trim();

    return (desc ? `${title}\n${desc}` : title);
  });
}

function extractQueryFromDOM() {
  const lines = document.querySelectorAll("#query-body .query-line");
  const conditions = [];

  lines.forEach(line => {
    const field = line.querySelector(".query-field input").value.trim();
    const op = line.querySelector(".query-operator input").value.trim();
    var val = line.querySelector(".query-value input").value.trim();
    val = parseBool(val);
    val = parseIntIfPossible(val);
    if (!field) return;

    let condition = {};

    switch (op) {
      case "exists":
        condition[field] = { "$exists": val };
        break;
      case ">":
        condition[field] = { "$gt": val };
        break;
      case "<":
        condition[field] = { "$lt": val };
        break;
      case ">=":
        condition[field] = { "$gte": val };
        break;
      case "<=":
        condition[field] = { "$lte": val };
        break;
      case "=":
      default:
        condition[field] = val;
        break;
    }

    conditions.push(condition);
  });

  return conditions.length ? { "$and": conditions } : {};
}


function extractLevelsFromDOM() {
  const levelElements = document.querySelectorAll("#levels-body .level-line");
  const levels = [];

  levelElements.forEach(el => {
    const tag = el.querySelector(".level-tag input").value.trim();
    const sortShort = el.querySelector(".level-sort input").value.trim().toUpperCase(); // ASC or DESC
    const sortTag = el.querySelector(".level-sorttag input").value.trim();
    const format = el.querySelector(".level-display").value.trim();

    if (!tag) return;

    const sort = `${sortTag}$${sortShort === "ASC" ? "ASCENDING" : "DESCENDING"}`;
    levels.push([tag, sort, format]);
  });

  return levels;
}


function updateNamesInCurrentMenu() {
  if (!currentMenu) {
    console.warn("currentMenu est invalide");
    return;
  }

  const hub = (window.current_hub || 'music');
  const itemEntries = document.querySelectorAll("#item-list .item-entry");
  const items = Array.isArray(currentMenu[hub]) ? currentMenu[hub] : [];

  itemEntries.forEach((entry, index) => {
    const title = entry.querySelector(".item-title").value.trim();
    const desc = entry.querySelector(".item-description").value.trim();
    const fullName = desc ? `${title}\n${desc}` : title;

    if (items[index]) {
      items[index].name = fullName;
    }
  });
}


function saveMenuToServer(filename) {

  updateNamesInCurrentMenu();
  if (!currentMenu) return;
  
  // Restaurer query/levels de l'item sélectionné
  var hubForSave = (window.current_hub || 'music');
  var saveItems = Array.isArray(currentMenu[hubForSave]) ? currentMenu[hubForSave] : null;
  if (currentSelectedIndex !== null && saveItems && saveItems[currentSelectedIndex]) {
    saveItems[currentSelectedIndex].query = extractQueryFromDOM();
    saveItems[currentSelectedIndex].levels = extractLevelsFromDOM();
  }


  // Créer un objet JSON en texte
  const jsonText = JSON.stringify(currentMenu, null, 2);

  // Préparer l'objet FormData avec un fichier virtuel
  const formData = new FormData();
  const blob = new Blob([jsonText], { type: "application/json" });
  formData.append("menu_file", blob, filename);
  formData.append("filename", filename+".json");

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/v1/Menu/Set", true);

  xhr.onload = function () {
    if (xhr.status === 200) {
      console.log("Menu envoyé avec succès :", xhr.responseText);
    
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



function change_hub(val) {
  try {
    var hubKey = (val === 'music') ? 'music' : (val === 'videos' ? 'videos' : val);
    // Met à jour le flag global
    window.current_hub = hubKey;

    // Si le menu est chargé, déclenche le rendu des items correspondant au hub
    if (typeof currentMenu !== 'undefined' && currentMenu !== null) {
      if (hubKey === 'music') {
        renderItems(currentMenu);
        // sélectionner premier item si présent
        if (currentMenu.music && currentMenu.music.length > 0) {
          currentSelectedIndex = 0;
          renderQuery(currentMenu.music[0]);
          renderLevels(currentMenu.music[0]);
          try {
            const entries = document.querySelectorAll('.item-entry');
            entries.forEach(e => e.classList.remove('selected'));
            if (entries[0]) entries[0].classList.add('selected');
          } catch (e) { console.log(e); }
          
        }
        else {
          // Si aucun item vidéos, vider les panneaux query et levels
          try {
            document.getElementById("query-body").innerHTML = "";
            document.getElementById("levels-body").innerHTML = "";
            currentSelectedIndex = null;
          } catch (e) {
            console.log(e);
          }
        }
      } else if (hubKey === 'videos') {
        // renderItems s'attend à un objet contenant la clé 'music'
        renderItems({ music: currentMenu.videos || [] });
        if (currentMenu.videos && currentMenu.videos.length > 0) {
          currentSelectedIndex = 0;
          renderQuery(currentMenu.videos[0]);
          renderLevels(currentMenu.videos[0]);
          try {
            const entries = document.querySelectorAll('.item-entry');
            entries.forEach(e => e.classList.remove('selected'));
            if (entries[0]) entries[0].classList.add('selected');
          } catch (e) { console.log(e); }
        } else {
          // Si aucun item vidéos, vider les panneaux query et levels
          try {
            document.getElementById("query-body").innerHTML = "";
            document.getElementById("levels-body").innerHTML = "";
            currentSelectedIndex = null;
          } catch (e) {
            console.log(e);
          }
        }
      }
    }

    window.dispatchEvent(new CustomEvent('hubChanged', { detail: { hub: hubKey } }));
    console.log('change_hub ->', hubKey);
  } catch (e) {
    console.log(e);
  }
}

