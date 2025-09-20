from ..helpers.excel_generator import ExcelGenerator

from mysite import settings
import os
import shutil

class CreateTestCaseMiddleWare:
    def __init__(self, pageId):
        self.notionPageId = pageId
        # self.rag = RAGService()
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

        
        
        # Gemma
        

        # groq
        # cases = self.groq.generate_testcases(analysed_srd, similarDocuments)
        
        

        # shutil.rmtree(self.imagesDir)

        return 'excelFile'