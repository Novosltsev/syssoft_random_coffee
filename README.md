### Проект по рандомному кофе

Чтобы запустить проект вам нужно запустить 

web 
```bash
python admin\manage.py migrate 
python admin\manage.py createsuperuser
python admin\manage.py runserver
```

bot
```bash
python main.py
```

Чтобы отредактировать конфигурацию config.py
```python
TOKEN = 'YOUR_TOKEN'
DOMAINS = ['domain1.com', 'domain2.com', 'domain3.com']
```