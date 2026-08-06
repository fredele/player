var query = "%7B%27%24and%27%3A%20%5B%7B%27mediatype%27%3A%20%27audio%27%7D%2C%20%7B%27genre%27%3A%20%7B%27%24exists%27%3A%20True%7D%7D%2C%20%7B%27album%27%3A%20%7B%27%24exists%27%3A%20True%7D%7D%2C%20%7B%27artist%27%3A%20%7B%27%24exists%27%3A%20True%7D%7D%2C%20%7B%27genre%27%3A%20%27Test%27%7D%2C%20%7B%27artist_alphabet%27%3A%20%27T%27%7D%2C%20%7B%27artist%27%3A%20%27The%20Test%27%7D%2C%20%7B%27dirhash%27%3A%20413577495%7D%5D%7D"
var  current_ids
var tag="album"

function onload_tageditor()
{

// Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("myBtn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];


// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
    document.getElementById('edit_tag_value').value ="";
    document.getElementById('edit_tag').value ="";
  }
}




  if (token == null) //?
  {
  token = Server_GetToken();
  }
  if (token != null)
  {
   current_ids =["6204dd5b27dbf199f0856ba8", "6204dd5e27dbf199f0856bd2", "6204dd6027dbf199f0856bfb", "6204dd6227dbf199f0856c23", "6204dd6527dbf199f0856c4b", "6204dd6727dbf199f0856c73", "6204dd6a27dbf199f0856c9c", "6204dd6c27dbf199f0856cc5", "6204dd6f27dbf199f0856cef", "6204dd7227dbf199f0856d18"]
   Server_GetValues( current_ids, tag, editor_after_get_values)
  }
  
}
