from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import *

# Create your views here.
def index(request):
    return HttpResponse('<h1>Irembo QA Project</h1>')

@api_view(['POST'])
def create_document(request):
    return Response({
            'message': 'Knowledge document created successfuly',
            'data': 'ok',
        }, status=status.HTTP_201_CREATED)
