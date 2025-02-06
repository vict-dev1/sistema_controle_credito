from django.urls import path
from apps.pages import views



urlpatterns = [
    path('', views.index, name='home'),
    path('home/',views.internal_index, name='interno_index'),
]