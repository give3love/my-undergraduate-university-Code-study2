import requests

api_key = 'a826c78d2b2332820741fe82d3dd858f'
city='beijing'
url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=zh_cn"

response = requests.get(url)
data = response.json()
print(data)