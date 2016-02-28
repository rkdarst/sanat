from django.conf.urls import patterns, include, url
from django.contrib import admin

from . import views
urlpatterns = [
    # Examples:
    # url(r'^$', 'sanat_site.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

     url(r'^$', views.select, name='select'),
     url(r'^run/$',    views.run,    name='run'),

]
