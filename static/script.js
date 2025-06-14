<script>
function showReminder(message) {
  alert(message);  // 或改用 Swal.fire(message) 弹窗更美观
}

// 定时触发提醒
function scheduleReminders() {
  const reminders = [
    { time: "09:00", message: "记得打卡啦！上班打卡开始。" },
    { time: "12:00", message: "午餐时间到啦！记得打卡午餐开始。" },
    { time: "12:30", message: "午餐结束，记得打卡返回工作状态。" },
    { time: "17:30", message: "下班时间到，记得打卡啦！" },
    { time: "17:30", message: "开始加班了吗？记得打卡加班开始。" },
    // 加班结束弹窗需通过按钮手动触发
  ];

  setInterval(() => {
    const now = new Date();
    const current = now.toTimeString().slice(0, 5); // 格式 HH:MM
    reminders.forEach(reminder => {
      if (current === reminder.time) {
        showReminder(reminder.message);
      }
    });
  }, 60000); // 每分钟检查一次
}

window.onload = scheduleReminders;
</script>
