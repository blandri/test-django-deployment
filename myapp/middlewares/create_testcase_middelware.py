from ..services.notion_service import NotionClient
from ..services.rag_service import RAGService

from ..helpers.excel_generator import ExcelGenerator

from mysite import settings
import os
import shutil

class CreateTestCaseMiddleWare:
    def __init__(self, pageId):
        self.notionPageId = pageId
        self.notionClient = NotionClient(settings.NOTION_API_KEY)
        self.rag = RAGService()
        # self.gemma = GemmaServ()
        # self.groq = GroqApi()
        self.excelGenerator = ExcelGenerator()
        self.imagesDir = "images"
        self.testcasesDir = "files"

    def testcase_generation (self):
        # shutil.rmtree(self.testcasesDir)

        # res = self.notionClient.notion_to_markdown(self.notionPageId)

        # files = os.listdir(self.imagesDir)
        
        # workflowInfo = self.gemma.query_gemma('Analyse this workflow diagram and generate texts explaining all the actions and events in it, respond with a numbered list.', f"{self.imagesDir}/{files[0]}")

        # new_res = res.replace('Image_placeholder', f'''{workflowInfo}''')

        
        analysed_srd = self.rag.analyze_srd_data('jk')

        similarDocuments = self.rag.retrieve_similar_content("Find similar testcases with this service", analysed_srd, 20)
        # print('++++', similarDocuments)
        # Gemma
        

        # groq
        # cases = self.groq.generate_testcases(analysed_srd, similarDocuments)
        
        

        # shutil.rmtree(self.imagesDir)

        return 'excelFile'