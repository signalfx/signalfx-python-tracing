# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from django.http import HttpResponse


def index(request):
    return HttpResponse("index")


def view_one(request):
    return HttpResponse("view_one")


def view_two(request):
    return HttpResponse("view_two")
