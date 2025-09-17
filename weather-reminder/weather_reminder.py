from email.mime.multipart import MIMEMultipart

import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
import configparser
import os
from plyer import notification
import time


def load_config():
    config = configparser.ConfigParser()

    if not os.path.exists('config.ini'):
        config['WEATHER_API'] = {
            'api_key': 'a826c78d2b2332820741fe82d3dd858f',
            'city': 'chongqing'
        }
        config['EMAIL'] = {
            'smtp_server': 'smtp.qq.com',
            'smtp_port': '587',
            'sender_email': '2010872257@qq.com',
            'sender_password': 'xkfajdojdrgyjfhe',
            'receiver_email': '2010872257@qq.com'
        }
        config['NOTIFICATION'] = {
            'enabled': 'True',
            'timeout': '10'
        }

        with open('config.ini', 'w') as f:
            config.write(f)
        print("已创建默认配置文件config.ini,请填写你的API秘钥和邮箱信息")
    config.read('config.ini')
    return config


class WeatherReminder:
  

    def __init__(self):
        self.config= load_config()
        #  从配置中提取"天气API"相关的设置，存到实例变量里
        self.api_key = self.config['WEATHER_API']['api_key']#API密钥
        self.city = self.config['WEATHER_API']['city']      #城市
        # 拼接API请求地址（把城市和密钥填到链接里）
        self.api_url = f"http://api.openweathermap.org/data/2.5/forecast?q={self.city}&appid={self.api_key}&units=metric&lang=zh_cn"

        # 3. 提取"邮件"相关的设置
        self.smtp_server = self.config['EMAIL']['smtp_server']#邮件服务器
        self.smtp_port = int(self.config['EMAIL']['smtp_port'])#端口
        self.sender_email = self.config['EMAIL']['sender_email']#发件人
        self.sender_password = self.config['EMAIL']['sender_password']#密码
        self.receiver_email = self.config['EMAIL']['receiver_email']#收件人

        # 4. 提取"通知"相关的设置
        self.notification_enable = self.config.getboolean('NOTIFICATION','enabled',fallback=True)
        self.notification_timeout = int(self.config['NOTIFICATION']['timeout'])

    def get_tomorrow_weather(self):
        """获取明天的天气信息"""
        try:
            #发送请求获取天气数据
            response = requests.get(self.api_url)
            data = response.json()

            #检查请求是否成功
            if response.status_code != 200:
                print(f"获取天气数据失败:{data.get('message','未知错误')}")
                return None

            #计算明天的日期
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

            #查找明天的天气数据
            for item in data['list']:
                if tomorrow in item['dt_txt']:
                    rain_prob=round(item.get('pop',0)*100 , 1)

                    weather = {
                        'date': item['dt_txt'],
                        'temp_min': item['main']['temp_min'],
                        'temp_max': item['main']['temp_max'],
                        'description': item['weather'][0]['description'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': item['wind']['speed'],
                        'rain_prob': rain_prob
                    }
                    return weather
            print("未找到明天的天气数据")
            return None
        except Exception as e:
            print(f"获取天气时发生错误:{str(e)}")
            return None
    def get_umbrella_weather(self,rain_prob):
        """根据降雨概率返回带伞提醒（可自定义阈值）"""
        if rain_prob >= 60:  # 高概率降雨（≥60%）：强制提醒带伞
            return f"⚠️ 降雨概率较高（{rain_prob}%），出门请务必携带雨伞！"
        elif 30 <= rain_prob < 60:  # 中概率降雨（30%-60%）：建议带伞
            return f"🔸 降雨概率中等（{rain_prob}%），建议携带雨伞备用。"
        else:  # 低概率降雨（<30%）：无需带伞
            return f"✅ 降雨概率较低（{rain_prob}%），出门无需携带雨伞。"


    def send_email_reminder(self, weather_data):
        """发送天气提醒邮件"""
        if not weather_data:
            print("没有天气数据可发送")
            return False
        try:
            #构建邮件内容
            subject = f"明天({weather_data['date'].split()[0]})的天气提醒"
            umbrella_weather = self.get_umbrella_weather(weather_data['rain_prob'])
            content = f"""
            明天天气情况如下：
            日期：{weather_data['date']}
            天气: {weather_data['description']}
            温度范围: {weather_data['temp_min']}°C 至 {weather_data['temp_max']}°C 
            湿度: {weather_data['humidity']}%
            风速: {weather_data['wind_speed']}m/s
            降雨概率: {weather_data['rain_prob']}%     
            {umbrella_weather}    
            """

            #创建邮件信息
            msg = MIMEMultipart()  # 先创建多部分邮件对象
            msg.attach(MIMEText(content, 'plain', 'utf-8'))  # 再添加文本内容
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = Header(subject)

            #发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls() # 启用TLS加密
            server.login(self.sender_email, self.sender_password)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()

            print("天气提醒邮件发送成功")
            return True
        except Exception as e:
            print(f"发送邮件时发生错误：:{str(e)}")
            return False


    def send_desktop_notification(self, weather_data):
        """发送桌面通知"""
        print("进入发送桌面通知方法")
        if not weather_data or not self.notification_enable:
            print(f"不发送通知：天气数据存在？{bool(weather_data)},通知已启用？{self.notification_enable}")
            return False

        try:
            #构建通知标题和内容
            umbrella_weather = self.get_umbrella_weather(weather_data['rain_prob'])
            title=f"明天的天气提醒({weather_data['date'].split()[0]})"
            message = f"""{weather_data['description']}
            温度: {weather_data['temp_min']}°C ~ {weather_data['temp_max']}°C
            降雨概率：: {weather_data['rain_prob']}%
            {umbrella_weather}
            
            """
            print(f"准备发送通知，标题为：{title}，内容为：{message}")
            #发送通知
            notification.notify(
                title=title,
                message=message,
                app_name="天气提醒",
                timeout=int(self.notification_timeout)
            )

            #等待通知发送完成
            time.sleep(1)
            print('通知发送语句已完成')
            return True
        except Exception as e:
            print(f"发送桌面通知时发生错误:{str(e)}")
            return False

    def run(self):
        """运行主流程"""
        print("开始获取明天的天气信息。。。")
        weather_data = self.get_tomorrow_weather()

        if weather_data:
            print("获取天气信息成功，准备发送提醒。。。")
            #发送邮件提醒
            #self.send_email_reminder(weather_data)
            #发送桌面通知
            self.send_desktop_notification(weather_data)
    pass
    
if __name__=='__main__':
    reminder = WeatherReminder()
    reminder.run()

