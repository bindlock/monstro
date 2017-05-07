from tornado.web import url

from . import views


patterns = [
    url(r'^/$', views.IndexView, name='index')
]
