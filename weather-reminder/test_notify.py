from plyer import notification
import time

# 发送测试通知
notification.notify(
    title="测试通知",
    message="桌面通知能正常显示啦！",
    app_name="测试",
    timeout=5
)
time.sleep(5)  # 等待通知显示