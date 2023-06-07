### Проект по рандомному кофе

Чтобы запустить проект вам нужно запустить 

web 
```bash
python manage.py migrate 
python manage.py createsuperuser
python manage.py runserver
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

После установки Docker:
```bash
docker volume create portainer_data
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ee:latest
```
