from django.db import models


class BotUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    STATUS_CHOICES = (
        ('active', 'Активна'),
        ('inactive', 'Отключена'),
    )
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    ACTIVITY_CHOICES = (
        ('registered', 'Зарегистрирован'),
        ('game', 'Играет'),
        ('pause', 'Пауза'),
        ('removed', 'Удален'),
    )
    activity = models.CharField(max_length=100, choices=ACTIVITY_CHOICES)

    def __str__(self):
        return self.first_name
