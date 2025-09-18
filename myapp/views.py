from django.shortcuts import render
from django.http import HttpResponse, FileResponse, Http404
from rest_framework import status
from rest_framework.response import Response

# Create your views here.
def index(request):
    try:
        return HttpResponse('<h1>QA AI App</h1>')
    except Exception as e:
        print(e)