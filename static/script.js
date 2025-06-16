// static/script.js
function submit(type) {
  fetch('/api/attendance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type })
  })
  .then(res => res.json())
  .then(data => {
    const msgDiv = document.getElementById('message');
    msgDiv.innerText = data.message || data.error;
    if (data.message && (
        data.message.includes('午餐已超过30分钟') ||
        data.message.includes('午餐超时') ||
        data.message.includes('下班打卡')
      )) {
      document.getElementById('alertSound').play();
      alert(data.message);
    }
  })
  .catch(err => {
    document.getElementById('message').innerText = '请求失败';
    console.error(err);
  });
}
