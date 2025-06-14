
function clockIn(type) {
    fetch('/api/attendance', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: type })
    }).then(res => {
        if (res.ok) {
            alert('打卡成功: ' + type);
        } else {
            alert('已打过卡或失败');
        }
    });
}
