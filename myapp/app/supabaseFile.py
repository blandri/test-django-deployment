from supabase import create_client, Client
import logging
from typing import Dict, Any, Optional
import uuid
from mysite import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.supabase = self.initiateConnection()

    def initiateConnection (self) -> Optional[Any]:
        try:
            SUPABASE_URL = settings.SUPABASE_URL
            SUPABASE_KEY = settings.SUPABASE_API_KEY
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            return supabase
        except Exception as e:
            logger.error(f"Error with supabase: {e}")
        
    def createDocument (self, content, embedding, metadata) -> Dict[str, Any]:
        try:
            document_id = str(uuid.uuid4())
            response = (
            self.supabase.table("documents")
            .insert({
                "id": document_id, 
                "content": content,
                "embedding": embedding,
                "metadata": metadata
                })
            .execute()
            )
            return response
        except Exception as e:
            logger.error(f"Error creating document: {e}")

    def getDocuments (self) -> Dict[str, Any]:
        try:
            response = self.supabase.rpc("get_all_documents", {}).execute()
            return response
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")

    def semanticSearch (self, query_embedding, limit: int, similarity_threshold: float = 0.4) -> Dict[str, Any]:
        try:
            response = self.supabase.rpc(
                "semantic_search",
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit
                }
            ).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error doing semantic search: {e}")

    def hybridSearch (self, query_embedding, similarity_threshold, max_results, keyword_filter) -> Dict[str, Any]:
        try:
            response = self.supabase.rpc(
                "hybrid_search_documents",
                {
                    'query_embedding': query_embedding,
                    'keyword_filter': keyword_filter,
                    'match_threshold': similarity_threshold,
                    'match_count': max_results
                }
            ).execute()

            return response
        except Exception as e:
            logger.error(f"Error doing hybrid search: {e}")

    # def searchAnalytics () -> Dict[str, Any]:
    def deleteDocument (self, id) -> Dict[str, Any]:
        try:
            response = (
            self.supabase.table("documents")
            .delete()
            .eq("id", id)
            .execute()
            )

            return response
        except Exception as e:
            logger.error(f"Error deleting document: {e}")