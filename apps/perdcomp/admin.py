from django.contrib import admin
from .models import Empresa, PER, Dcomp, DcompDebitos

admin.site.register(Empresa)
admin.site.register(PER)
admin.site.register(Dcomp)
admin.site.register(DcompDebitos)