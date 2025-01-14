from django.contrib import admin

from .models import ClUser

class UserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'email']
    list_filter = ['is_staff', 'is_superuser']
    list_display = ['username', 'email', 'is_staff', 'is_superuser']

admin.site.register(ClUser, UserAdmin)
