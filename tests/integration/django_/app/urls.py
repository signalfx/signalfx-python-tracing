# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index),
    url(r'^one/', views.view_one),
    url(r'^two/', views.view_two)
]
