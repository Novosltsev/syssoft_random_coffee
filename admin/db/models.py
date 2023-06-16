from django.db import models


class BotUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=100, null=True)
    username = models.CharField(max_length=100, null=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=100, null=True)
    code = models.CharField(max_length=100, null=True)
    STATUS_CHOICES = (
        ('active', 'Активна'),
        ('inactive', 'Отключена'),
    )
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, null=True)
    ACTIVITY_CHOICES = (
        ('registered', 'Зарегистрирован'),
        ('game', 'Играет'),
        ('pause', 'Пауза'),
        ('removed', 'Удален'),
    )
    activity = models.CharField(max_length=100, choices=ACTIVITY_CHOICES, null=True)

    def __str__(self):
        return self.first_name
