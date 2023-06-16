from import_export import resources
from .models import BotUser


class BotUserResource(resources.ModelResource):
    class Meta:
        model = BotUser
