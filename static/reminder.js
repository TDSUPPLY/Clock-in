// 弹窗提示函数
function showReminder(message) {
    const reminder = document.createElement('div');
    reminder.className = 'reminder-popup';
    reminder.textContent = message;

    Object.assign(reminder.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        backgroundColor: '#222',
        color: '#fff',
        padding: '12px 18px',
        borderRadius: '8px',
        zIndex: 9999,
        boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
        fontSize: '16px',
        fontWeight: 'bold'
    });

    document.body.appendChild(reminder);

    setTimeout(() => {
        reminder.remove();
    }, 5000);
}

// 获取马来西亚时间
function getMalaysiaTime() {
    const now = new Date();
    const utc = now.getTime() + now.getTimezoneOffset() * 60000;
    return new Date(utc + 8 * 3600000); // UTC+8
}

// 检查是否到了提醒时间
function checkReminders() {
    const now = getMalaysiaTime();
    const current = now.getHours() * 60 + now.getMinutes(); // 以分钟计算

    const reminders = [
        { time: 9 * 60, message: "记得打卡啦！上班打卡开始。" },
        { time: 12 * 60, message: "午餐时间到啦！记得打卡午餐开始。" },
        { time: 12 * 60 + 30, message: "午餐结束，记得打卡返回工作状态。" },
        { time: 17 * 60 + 30, message: "下班时间到，记得打卡啦！" },
        { time: 17 * 60 + 31, message: "开始加班了吗？记得打卡加班开始。" },
    ];

    reminders.forEach(reminder => {
        if (Math.abs(current - reminder.time) <= 1) {
            if (!localStorage.getItem('reminded-' + reminder.time)) {
                showReminder(reminder.message);
                localStorage.setItem('reminded-' + reminder.time, 'true');
            }
        }
    });
}

// 每分钟检查一次提醒
setInterval(checkReminders, 60000);
checkReminders(); // 初始调用
