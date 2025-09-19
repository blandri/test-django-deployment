from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('register', views.register, name='register'),
    
    # Document management
    path('documents', views.create_document, name='list_documents')
]