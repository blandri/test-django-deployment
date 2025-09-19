from django.http import HttpResponse, FileResponse, Http404
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import *
from pathlib import Path
from .services.supabaseFile import SupabaseClient
from .services.rag_service import RAGService
from .services.gemma_service import GemmaServ
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
        
        res = "ok"

        return Response({
            'message': 'Testcases created successfully',
            'data': res
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def improve_testcase(request):
    try:
        user_query = request.data['prompt']
        
        gemma = GemmaServ()
        excel_generator = ExcelGenerator()

        improved_res = gemma.improve_last_response(user_query)
        res = excel_generator.generate_testcase_excel(improved_res, "Semen")

        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])  
def download_file(request):
    try:
        file_path = Path.cwd() / "files" / "testcases.xlsx"
        if file_path.exists():
            response = FileResponse(open(file_path, "rb"), as_attachment=True, filename="testcases")
            return response
        raise Http404("File not found")
    except Exception as e:
        print(e)
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_documents(request):
    try:
        client = SupabaseClient()
        res = client.getDocuments()
        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
