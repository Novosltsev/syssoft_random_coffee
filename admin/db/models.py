from django.db import models

class BotUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    activity = models.CharField(max_length=100)


    def __str__(self):
        return self.first_name