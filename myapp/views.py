from django.http import HttpResponse, FileResponse, Http404
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import *
from pathlib import Path
from .services.supabaseFile import SupabaseClient
from .services.rag_service import RAGService
from .middlewares.create_testcase_middelware import CreateTestCaseMiddleWare
from .helpers.excel_generator import ExcelGenerator

# Create your views here.
def index(request):
    return HttpResponse('<h1>Irembo QA Project</h1>')

@api_view(['POST'])
def create_document(request):
    """Create a new document with embedding"""
    try:
        testcaseFile = request.data['testcases']
        rag = RAGService()
        res = rag.process_knowledge_base_document(testcaseFile, metadata = {'document_name': testcaseFile.name})

        return Response({
            'message': 'Knowledge document created successfuly',
            'data': res,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        # print('\033[31m>>>>>>>>>>>>\033[0m', e)
        return Response({'error': 'A server error has occured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_testcase(request):
    try:
        pageId = request.data['srd_page_id']
        testcase_middleqare = CreateTestCaseMiddleWare(pageId)
        
        res = testcase_middleqare.testcase_generation()

        return Response({
            'message': 'Testcases created successfully',
            'data': res
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
