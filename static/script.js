
function updateClock() {
  document.getElementById("clock").innerText = new Date().toLocaleString();
}
setInterval(updateClock, 1000);
updateClock();

function clockIn(type) {
  fetch('/api/attendance', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({type})
  })
  .then(res => res.json())
  .then(data => alert(data.message));
}
function logout() {
  location.href = "/logout";
}
