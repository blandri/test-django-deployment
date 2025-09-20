from .supabaseFile import SupabaseClient
from .emdedding_service import EmbeddingService
from ..helpers.excel_processor import ExcelProcessor
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import re
import json

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_service = SupabaseClient()
        self.embedding_service = EmbeddingService()
        self.pdf_processor = ExcelProcessor()
        self.images_dir = Path('Images')
    
    def process_knowledge_base_document(self, excel_file, metadata: Dict[str, Any]) -> bool:
        try:
            text_content = self.pdf_processor.extract_text_representation(excel_file)
            
            if not text_content:
                logger.error("No text content extracted from Excel")
                return False
            
            knowledge_document = text_content
            chunks = self._enhanced_chunk_testcase_document(knowledge_document)
            
            # Generate embeddings for chunks
            embeddings = self.embedding_service.generate_embeddings_batch(chunks)
           
            # Store embeddings in vector database
            for chunk, embedding in zip(chunks, embeddings):
                chunk_metadata = {
                    **metadata,
                    'chunk_text': chunk,
                    'document_type': 'knowledge_base',
                    'chunk_type': self._classify_chunk_type(chunk)
                }
                
                success = self.vector_service.createDocument(
                    content=chunk,
                    embedding=embedding,
                    metadata=chunk_metadata
                )
                
                if not success:
                    logger.error(f"Failed to store embedding for chunk")
            
            return success
        except Exception as e:
            logger.error(f"Error processing knowledge base document: {e}")
            raise
    
    def retrieve_similar_content(self, query: str, srd_parts: Dict[str, str], limit: int) -> List[Dict]:
        try:
            # Create enhanced query with SRD context
            enhanced_query = self.create_enhanced_query(query, srd_parts)

            # Generate text embedding for query
            query_embedding = self.embedding_service.generate_embedding(enhanced_query)
            
            if not query_embedding:
                return []
            
            # Search for similar content (text-based)
            text_similar_content = self.vector_service.semanticSearch(
                query_embedding=query_embedding,
                limit=limit
            )
            
            return text_similar_content
        except Exception as e:
            logger.error(f"Error retrieving similar content: {e}")
            return []
        
    def create_enhanced_query(self, original_query: str, srd_parts: Dict[str, str]) -> str:
        query = [original_query, srd_parts]
        return " | ".join(query)
    
    def analyze_srd_data(self, srd_data: str) -> str:
        # Extract key context from SRD
        service_name = self.extract_service_details(srd_data)
        form_fields = self.extract_form_fields(srd_data)
        workflow_labels = self.extract_status_labels(srd_data)
        workflow_context = self.extract_workflow_events(srd_data)
        pricing = self.extract_pricing_details(srd_data)
        next_steps = self.extract_next_steps(srd_data)
        sla = self.extract_sla(srd_data)
        sms = self.extract_sms_notifications(srd_data)
        emails = self.extract_email_notifications(srd_data)

        # Build enhanced query
        enhanced_parts = {}
        
        if service_name:
            enhanced_parts["service details"] = service_name
        
        if form_fields:
            enhanced_parts["form fields"] = form_fields
        
        if workflow_labels:
            enhanced_parts["workflow statuses"] = workflow_labels
        
        if workflow_context:
            enhanced_parts["workflow"] = workflow_context

        if sms and emails:
            enhanced_parts["notifications"] = {"sms": sms, "emails": emails}

        if next_steps:
            enhanced_parts["next steps"] = next_steps

        if pricing:
            enhanced_parts["pricing"] = pricing

        if sla:
            enhanced_parts["sla"] = sla

        return json.dumps(enhanced_parts)
    
    def _enhanced_chunk_testcase_document(self, text_content: str) -> List[str]:
        chunks = []

        test_case_pattern = r"(Test Case\s*\d+:.*?)(?=(?:Test Case\s*\d+:)|\Z)"

        matches = re.findall(test_case_pattern, text_content, re.DOTALL)

        for match in matches:
            cleaned = match.strip()
            if len(cleaned) > 30:
                cleaned = re.sub(r"\s*\n\s*", " | ", cleaned)
                chunks.append(cleaned)

        return chunks
    
    def _classify_chunk_type(self, chunk: str) -> str:
        chunk_lower = chunk.lower()
        
        if any(keyword in chunk_lower for keyword in ['service name', 'details']):
            return 'service_description'
        elif any(keyword in chunk_lower for keyword in ['request type', 'result_code']):
            return 'API'
        elif any(keyword in chunk_lower for keyword in ['application workflow', 'application processing']):
            return 'workflow'
        elif any(keyword in chunk_lower for keyword in ['certificate']):
            return 'certificate'
        elif any(keyword in chunk_lower for keyword in ['summary', 'page']):
            return 'summary_page'
        elif any(keyword in chunk_lower for keyword in ['validation', 'rule', 'error message', 'error']):
            return 'validation_rule'
        elif any(keyword in chunk_lower for keyword in ['next steps']):
            return 'next_steps'
        elif any(keyword in chunk_lower for keyword in ['notification', 'sms', 'email']):
            return 'notifications'
        elif any(keyword in chunk_lower for keyword in ['details', 'attachments', 'phone number']):
            return 'form_specification'
        else:
            return 'general'
        
    def extract_form_fields(self, srd_text: str) -> List[Dict]:
        form_section = re.search(r"(#+\s*\**Form Elements\**)(.*?)(##|\Z)", srd_text, re.DOTALL | re.IGNORECASE)
        if not form_section:
            return []

        table_text = form_section.group(2).strip()
        rows = [row.strip() for row in table_text.split("\n") if "|" in row]

        if len(rows) < 3:
            return []

        rows = rows[2:]

        fields = []
        for row in rows:
            cols = [col.strip() for col in row.split("|")[1:-1]]
            if not cols:
                continue
            fields.append({
                "section": cols[0] if len(cols) > 0 else None,
                "block": cols[1] if len(cols) > 1 else None,
                "field_name": cols[2] if len(cols) > 2 else None,
                "type": cols[3] if len(cols) > 3 else None,
                "hint": cols[4] if len(cols) > 4 else None,
                "tooltip": cols[5] if len(cols) > 5 else None,
                "Placeholder (for inputs only)/List of values (for drop downs)": cols[6] if len(cols) > 6 else None,
                "Widget requirements": cols[7] if len(cols) > 7 else None,                         
                "Validation Rule": cols[8] if len(cols) > 8 else None,                                   
                "Display Rule": cols[9] if len(cols) > 9 else None,                                         
                "Error Message": cols[10] if len(cols) > 10 else None,
            })
        return fields

    def extract_workflow_events(self, srd_text: str) -> List[str]:
        match = re.search(r"(?:##+\s*Workflow.*?)(\d+\..*?)(?=\n##|\Z)", srd_text, re.DOTALL | re.IGNORECASE)
        if not match:
            return []

        block = match.group(1)

        # Return each numbered line exactly as-is
        events = [line for line in block.split("\n") if line.strip().startswith(tuple("123456789"))]
        return events
    
    def extract_status_labels(self, srd_text: str) -> Dict[str, str]:
        labels_section = re.search(r"### Labels of status(.*?)(###|\Z)", srd_text, re.DOTALL)
        if not labels_section:
            return {}
        table_text = labels_section.group(1)
        rows = [row.strip() for row in table_text.split("\n") if "|" in row][2:]  # skip headers
        labels = {}
        for row in rows:
            cols = [col.strip() for col in row.split("|")[1:-1]]
            if len(cols) >= 2:
                labels[cols[0]] = cols[1]
        return labels
    
    def extract_next_steps(self, srd_text: str) -> List[Dict]:
        steps_section = re.search(r"### Next steps(.*?)(##|\Z)", srd_text, re.DOTALL)
        if not steps_section:
            return []
        table_text = steps_section.group(1)
        rows = [row.strip() for row in table_text.split("\n") if "|" in row][2:]
        steps = []
        for row in rows:
            cols = [col.strip() for col in row.split("|")[1:-1]]
            if len(cols) >= 3:
                steps.append({
                    "step": cols[0],
                    "title": cols[1],
                    "description": cols[2]
                })
        return steps

    def extract_pricing_details(self, srd_text: str) -> Dict[str, List[Dict]]:
        details = {
        "Currency": None,
        "Payment Expiration Time": None,
        "Service Payment Code": None,
        "Payment merchant": None,
        "Payment account identifier": None,
        "service_pricing": None,
        }

        # --- Currency ---
        currency_match = re.search(r"##\s*\**Currency\**\s*\n+([^\n]+)", srd_text, re.IGNORECASE)
        if currency_match:
            details["Currency"] = currency_match.group(1).strip()

        # --- Payment Expiration Time ---
        pet_match = re.search(r"##\s*\**Payment Expiration Time\**\s*\n+([^\n]+)", srd_text, re.IGNORECASE)
        if pet_match:
            details["Payment Expiration Time"] = pet_match.group(1).strip()

        # --- Payment merchant ---
        merchant_match = re.search(r"##\s*Payment merchant\s*\n+([^\n]+)", srd_text, re.IGNORECASE)
        if merchant_match:
            details["Payment merchant"] = merchant_match.group(1).strip()

        # --- Payment account identifier ---
        account_match = re.search(r"Payment account identifier\s*\n+([^\n]+)", srd_text, re.IGNORECASE)
        if account_match:
            details["Payment account identifier"] = account_match.group(1).strip()

        # --- Service Payment Code (look for both bold or plain) ---
        code_match = re.search(r"(?:\*\*UAT:\*\*|UAT:)\s*([^\n]+)", srd_text, re.IGNORECASE)
        if not code_match:
            code_match = re.search(r"Service Payment Code\s*\n+([^\n]+)", srd_text, re.IGNORECASE)
        if code_match:
            details["Service Payment Code"] = code_match.group(0).strip()

        # --- Service Pricing (Dynamic / Fixed as raw markdown text) ---
        pricing_match = re.search(r"##\s*\**Service Pricing\**([\s\S]*?)(?=##\s*\**Service Payment Code|\Z)", srd_text, re.IGNORECASE)
        if pricing_match:
            pricing_text = pricing_match.group(1).strip()
            if pricing_text:
                details["service_pricing"] = pricing_text

        return details
    
    def extract_service_details(self, srd_text: str) -> List[Dict]:
        match = re.search(
            r"(#+\s*Database:\s*Service details.*?)(?=\n##|\Z)",
            srd_text,
            re.DOTALL | re.IGNORECASE
        )
        if not match:
            return []

        table_text = match.group(1)
        rows = [row.strip() for row in table_text.split("\n") if "|" in row]

        if len(rows) < 3:
            return []

        headers = [h.strip() for h in rows[0].split("|")[1:-1]]
        rows = rows[2:]

        services = []
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if not cols or all(c == "" for c in cols):
                continue
            service = {headers[i]: cols[i] for i in range(min(len(headers), len(cols)))}
            services.append(service)

        return services
    
    def extract_sla(self, srd_text: str) -> Optional[str]:
        sla_match = re.search(r"##\s*SLAs\s*\n+([\s\S]*?)(?=##\s*Notifications|\Z)", srd_text, re.IGNORECASE)
        if sla_match:
            return sla_match.group(1).strip()
        return None
    
    def extract_table(self, md_str, start_marker):
        pattern = rf"{start_marker}(.*?)(?:\n###|\Z)"
        match = re.search(pattern, md_str, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None


    def parse_markdown_table(self, table_md):
        """Parses a markdown table into rows of columns."""
        lines = [line.strip() for line in table_md.splitlines() if line.strip()]
        # Remove header and separator lines
        lines = [line for line in lines if not re.match(r"^\|[-\s|]+\|$", line)]
        rows = []
        for line in lines:
            cols = [c.strip() for c in line.split("|")[1:-1]]  # ignore edges
            rows.append(cols)
        return rows


    def extract_sms_notifications(self, md_str):
        """Extracts SMS notifications (English) into {status: message} dict."""
        table_md = self.extract_table(md_str, r"\*\*SMS\*\*")
        if not table_md:
            return {}
        rows = self.parse_markdown_table(table_md)
        notifications = {}
        for row in rows:
            if len(row) >= 2:  # status + SMS English
                status, sms_en = row[0], row[1]
                notifications[status] = sms_en
        return notifications


    def extract_email_notifications(self, md_str):
        """Extracts Email notifications (English) into {status: message} dict."""
        table_md = self.extract_table(md_str, r"\*\*Email\*\*")
        if not table_md:
            return {}
        rows = self.parse_markdown_table(table_md)
        notifications = {}
        for row in rows:
            if len(row) >= 3:  # status + subject + email body English
                status, subject, email_en = row[0], row[1], row[2]
                notifications[status] = {
                    "subject": subject,
                    "message": email_en
                }

        return notifications
