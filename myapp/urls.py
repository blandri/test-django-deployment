from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('register', views.register, name='register'),
    
    # Document management
    path('documents/create', views.create_document, name='create_document'),
    # path('documents/bulk-create/', views.bulk_create_documents, name='bulk_create_documents'),
    # path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    
    # Vector search
    # path('search/semantic/', views.semantic_search, name='semantic_search'),
    # path('search/analytics/', views.search_analytics, name='search_analytics'),
    path('agent/create/testcase', views.create_testcase, name='create_testcase')
]