from django.contrib import admin
from .models import BotUser
from import_export.admin import ImportExportModelAdmin
from .resources import BotUserResource


class BotUserAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user_id', 'username', 'first_name', 'last_name', 'email', 'code', 'status', 'activity')
    search_fields = ('id', 'user_id', 'username', 'first_name', 'last_name', 'email', 'code', 'status', 'activity')


admin.site.register(BotUser, BotUserAdmin)
