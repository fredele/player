const API_KEY = "whisper-7c0436e42e515ca2ca686ba0e3a25ad8e8ad12765b84f03e"; // ta clé
const WHISPER_URL = "http://localhost:9000/v1/audio/transcriptions";

const btn = document.getElementById("mic_img");
//const status = document.getElementById("status");

let mediaRecorder;
let chunks = [];

btn.addEventListener("mousedown", startRecording);
btn.addEventListener("mouseup", stopRecording);
// Aussi pour le tactile
btn.addEventListener("touchstart", (e) => { e.preventDefault(); startRecording(); });
btn.addEventListener("touchend", (e) => { e.preventDefault(); stopRecording(); });



async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
  chunks = [];

  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) {
      chunks.push(e.data);
    }
  };

  mediaRecorder.onstop = () => {
    // Création du Blob ici
    const blob = new Blob(chunks, { type: "audio/webm" });
    console.log("Blob créé, taille :", blob.size);

    sendToMyServer(blob);

    // Arrêter le micro
    stream.getTracks().forEach(track => track.stop());
  };

  mediaRecorder.start();
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
}



async function sendToMyServer(blob) {
  // Vérification
  if (!(blob instanceof Blob)) {
    console.error("Ce n'est pas un Blob :", blob);
    return;
  }

  const formData = new FormData();
  formData.append("file", blob, "commande.webm");  // ← blob obligatoire
  formData.append("player", window.id);

  const response = await fetch("/api/transcribe", {
    method: "POST",
    body: formData
  });



}