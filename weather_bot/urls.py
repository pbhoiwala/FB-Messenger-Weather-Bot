from django.conf.urls import include, url
from .views import weatherBotView
urlpatterns = [
    url(r'^your url goes here/?$', weatherBotView.as_view())
]

