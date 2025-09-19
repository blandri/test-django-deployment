from django.http import HttpResponse, FileResponse, Http404
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import *
from pathlib import Path
from .helpers.excel_generator import ExcelGenerator

# Create your views here.
def index(request):
    return HttpResponse('<h1>Irembo QA Project</h1>')

@api_view(['POST'])
def create_document(request):
    """Create a new document with embedding"""
    try:
        testcaseFile = request.data['testcases']

        return Response({
            'message': 'Knowledge document created successfuly',
            'data': 'ok',
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        # print('\033[31m>>>>>>>>>>>>\033[0m', e)
        return Response({'error': 'A server error has occured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
