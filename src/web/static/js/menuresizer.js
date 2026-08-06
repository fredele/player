// Redimensionnement vertical (item)
const verticalResizer = document.getElementById("vertical-resizer");
const item = document.getElementById("item");
const rightPanel = document.getElementById("right-panel");

verticalResizer.addEventListener("mousedown", function (e) {
  e.preventDefault();
  document.addEventListener("mousemove", resizeHorizontally);
  document.addEventListener("mouseup", stopHorizontalResize);
});

function resizeHorizontally(e) {
  const newWidth = e.clientX;
  item.style.width = newWidth + "px";
}

function stopHorizontalResize() {
  document.removeEventListener("mousemove", resizeHorizontally);
  document.removeEventListener("mouseup", stopHorizontalResize);
}

// Redimensionnement horizontal (query/levels)
const horizontalResizer = document.getElementById("horizontal-resizer");
const query = document.getElementById("query");
const levels = document.getElementById("levels");

horizontalResizer.addEventListener("mousedown", function (e) {
  e.preventDefault();
  document.addEventListener("mousemove", resizeVertically);
  document.addEventListener("mouseup", stopVerticalResize);
});

function resizeVertically(e) {
  const containerTop = query.parentElement.getBoundingClientRect().top;
  const newHeight = e.clientY - containerTop;
  query.style.height = newHeight + "px";
}

function stopVerticalResize() {
  document.removeEventListener("mousemove", resizeVertically);
  document.removeEventListener("mouseup", stopVerticalResize);
}

