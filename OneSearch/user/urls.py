from django.urls import path
from .views import transcribe_audio
from . import views

urlpatterns = [
    path("", views.home),
    path("test/", views.test),
    path("search/", views.search),
    path('transcribe/', transcribe_audio, name='transcribe_audio'),
    path("response/", views.response_view, name="response_view"),
]   