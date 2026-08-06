from django.contrib import admin
from django.urls import path
from core import views  # Убедись, что импортируешь views из своего приложения

# Обязательно должен быть список (list), а не что-то другое
urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
]