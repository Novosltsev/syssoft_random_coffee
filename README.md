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

Чтобы запустить проект через Docker
```python
# команда создает Docker-том для хранения данных Portainer
docker volume create portainer_data
# команда запускает контейнер с Portainer, настроенным для работы с портами 8000 и 9443, а также для доступа к Docker API через сокет /var/run/docker.sock
# Данные Portainer будут сохраняться в созданном ранее Docker-томе portainer_data
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ee:latest
# После запуска контейнера с Portainer вы сможете получить доступ к веб-интерфейсу Portainer, открыв веб-браузер и перейдя по адресу http://localhost:8000 или https://localhost:9443 (в зависимости от того, какой порт вы выбрали).
# После установки и запуска Portainer вы можете использовать его для управления вашими контейнерами и выполнения других операций с Docker.
```
