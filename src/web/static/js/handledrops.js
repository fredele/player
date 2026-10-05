function handleDrop_query(e) {
    e.preventDefault();
    e.stopPropagation();

    const files = e.dataTransfer.files;

    if (files.length > 0) {
        for (const file of files) {
            if (file.type.startsWith("image/")) {
                uploadImage(file);
            } else if (file.type === "text/plain" || file.type === "text/markdown") {
                uploadTextFile(file);
            } 
        }
        return;
    }

    const text = e.dataTransfer.getData("text/plain");

    if (text) {
        processText(text);
    }
}



function uploadImage(file) {

 authorizationBasic = ``;
  if (token != null ) {
  authorizationBasic = `Bearer ` + token;
  }
  let url = window.addr + "/v1/UpdateCover?query=" + window.queryview_last_query;

  let formData = new FormData()

  formData.append('file', file)
  fetch(url, {
    method: 'POST',
    body: formData,
     headers: {
      'Authorization': authorizationBasic
    }
  })
    .then(response => {
      // réponse HTTP
      const url = new URL(response.url);
      const query = url.searchParams.get('query');
      //Server_Get_SideFiles(query, after_Server_Get_SideFiles, null);
      Server_Get_UpdatedImages(after_Upload_Image, null);
    })
    .catch(error => {
      /* Error. Inform the user */
    })
}

function uploadTextFile(file) {

    authorizationBasic = '';

    if (token != null) {
        authorizationBasic = 'Bearer ' + token;
    }

    let url = window.addr + "/v1/UpdateInfos?query=" +
              window.queryview_last_query;

    let formData = new FormData();

    formData.append('file', file);

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': authorizationBasic
        }
    })
    .then(response => {
        // réponse HTTP
        const url = new URL(response.url);
        const query = url.search.match(/[?&]query=([^&]*)/)?.[1];
        Server_Get_SideFiles(query, after_Server_Get_SideFiles, null);
    })
    .catch(error => {
        // erreur réseau
        console.error(error);
    });
}
