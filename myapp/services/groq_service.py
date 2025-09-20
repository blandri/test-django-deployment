from typing import List, Dict
from groq import Groq
import base64
import json
from mysite import settings
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq._exceptions import APIStatusError

logger = logging.getLogger(__name__)

class GroqApi:
    def __init__(self):
        self.client = Groq(
            api_key=settings.SECRET_KEY
        )
        self.reasoning_map = {
            "form fields": "high", 
            "pricing": "high",        
            "workflow": "medium",   
            "notifications": "medium", 
            "service details": "low", 
            "next steps": "low",
        }
    
    def callGroq (self, section, prompt):
        try:
            chat_completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                top_p=1.0, # Controls diversity of token selection
                max_completion_tokens= 8000,
                temperature=0.15, # Controls randomness
                reasoning_effort = self.reasoning_map[section],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "testcase_schema",
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "Use Case": {"type": "string"},
                                    "Test Scenario": {"type": "string"},
                                    "Preconditions": {"type": "string"},
                                    "Input": {"type": "string"},
                                    "Expected Results": {"type": "string"}
                                },
                                "required": ["Use Case", "Test Scenario", "Expected Results"]
                            }
                        }
                    }
                }
            )
            # print('+++++', chat_completion.choices[0].message.content)
            return json.loads(chat_completion.choices[0].message.content)
        except APIStatusError as e:
            if e.status_code == 429:
                logger.warning(f"Rate Limit exceeded")
            else:
                raise 
        except Exception as e:
            logger.error(f"Error interacting with groq: {e}")
            raise
    
    def callGroqForImages (self, image_path):
        base64_image = self.encode_image(image_path)

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyse this workflow diagram and generate texts explaining all the actions and events in it, respond with a numbered list."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )

        return chat_completion.choices[0].message.content

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def generate_testcases(self, srd_content: str, past_examples: List[Dict]):
        try:
            srd_content_dict = json.loads(srd_content)
            prompts = self.create_test_case_prompt(srd_content_dict, past_examples)

            responses = []

            with ThreadPoolExecutor(max_workers=3) as executor:  # limit concurrency
                futures = {executor.submit(self.callGroq, key, value): key for key, value in prompts.items()}
                for future in as_completed(futures):
                    try:
                        responses.append(future.result())
                    except Exception as e:
                        logger.error(f"Error on {futures[future]}: {e}")
 
            return responses
        except Exception as e:
            logger.error(f"Error generating testcases: {e}")
            raise

        
   
    def create_test_case_prompt(self, srd_content: Dict[str, str], context: List[Dict]) -> Dict[str, str]: 
        prompts = {
            "service details": None,
            "form fields": None,
            "pricing": None, 
            "next steps": None,     
            "workflow": None,   
            "notifications": None
        }

        try:
            for key in srd_content:
                if (key == "service details"):
                    prompts["service details"] = f""" Given the following requirements: 
                    
                            **Requirements**
                            
                            - Service details: {srd_content["service details"]}.
                            - SLA (Processing time): {srd_content["sla"]}.

                            **Task:**
                            1. Analyze the provided requirements and Generate exactly one test case for every element.
                            - Generate a testcase to verify that the correct service name is displayed on the page. 
                            - Generate a testcase to verify that the correct service description is displayed on the page. 
                            - Generate a testcase to verify that the correct Institution provider is displayed on the page. 
                            - Generate a testcase to verify that the correct SLA is displayed on the page as Processing time.

                            ** Reference past test case structure for consistency: {context}
                            
                            **Output Requirements:**
                            - Respond ONLY with a valid JSON array of objects enclosed in a ```json code block.
                            - Do not include any explanations or extra text outside the JSON.
                            - Each object must strictly follow this schema:

                            ```json
                            {{
                            "Use Case": "string",
                            "Test Scenario": "string",
                            "Preconditions": "string",
                            "Input": "string",
                            "Expected Results": "string (a numbered list of all expected results)"
                            }}
                    """
                elif (key == "form fields"):
                    prompts["form fields"] = f"""
                        Given the following form field requirements array: {srd_content["form fields"]}.  

                        **Task:**  
                        Generate a **thorough and complete set of test cases**.  
                        - Every field in the array must have its own test cases.  
                        - Cover **all validation rules, required fields, widget-specific rules, tooltips, placeholders, display rules, and error messages**.  
                        - Include **both positive and negative scenarios** for each field.  
                        - Do not skip any field or validation detail.  
                        - The final JSON array length must equal the total number of generated test cases across all fields.  

                        **Instructions for Generating Test Cases:**  
                        1. **Field-by-Field Analysis:** For each field object in the array, carefully read all its properties (Section, Block, Field name, Type, Hint, Tooltip, Placeholder/List of values, Widget requirements, Validation Rule, Display Rule, Error Message).  
                        2. **Reference Past Examples:** Follow the structure and level of detail from previous test case examples: {context}. 
                        3. **Test Case Generation:** For every field, create multiple test cases to cover:  
                        - **Functional Testing:** Verify correct input behavior (valid ID numbers, dropdown selections, etc.).  
                        - **Positive Validation:** Confirm system accepts valid inputs.  
                        - **Negative Validation:** Confirm system rejects invalid inputs (wrong length, wrong format, missing required).  
                        - **Error Handling:** Verify error messages appear exactly as specified in the requirements.  
                        - **Display Rules:** Confirm the field behaves correctly under different display conditions (e.g., error message from external system).  
                        - **Widget-Specific Logic:** Validate requirements like auto-population or field dependencies.  
                        
                        4. **Output Format:**  
                        - Respond **only** with a valid JSON array enclosed in a ```json code block.  
                        - Do not include explanations, markdown headers, or extra text outside the JSON.  
                        - Each object must strictly follow this schema:  

                        ```json
                        {{
                        "Use Case": "string",
                        "Test Scenario": "string",
                        "Preconditions": "string",
                        "Input": "string (a numbered list of the inputs for a certain scenario)",
                        "Expected Results": "string (a numbered list of all expected results)"
                        }}
                    """
                elif (key == "workflow"): 
                    prompts["workflow"] = f"""
                        You are given the following workflow description and status labels:

                        **Workflow Steps:** {srd_content["workflow"]}

                        **Status Labels (end-user facing):** {srd_content["workflow statuses"]}

                        **Task:**  
                        Generate a **comprehensive but atomic set of test cases** to validate the workflow. Each test must focus on a single scenario or transition, without combining multiple unrelated checks.  

                        **Coverage Requirements:**  
                        - Cover the **happy path** (the full sequence from start to successful completion if such a path exists).  
                        - Cover any **alternative flows** present (e.g., rejection, request for further action, skipping payment, etc.), but only if they are explicitly part of the workflow.  
                        - Cover **edge cases** relevant to this workflow (e.g., payment expiration or duplicate payments, but only if payment is part of this service).  
                        - For every status, include a test case that verifies the **UI label** matches exactly the label provided in the status labels list.  
                        - Tests must remain **atomic**: one scenario per test case. 

                        **Instructions for Generating Test Cases:**  
                        - Tests should be **atomic and focused** (1 scenario per test).  
                        - Avoid redundancy, but ensure all required flows and edge cases are covered.  
                        - Each test case must explicitly reference both the workflow step and the expected **UI label**.  
                        - Reference past test case structure for consistency: {context}.  

                        **Output Requirements:**  
                        - Respond ONLY with a valid JSON array enclosed in a ```json code block.  
                        - Do not include any explanations or text outside the JSON.  
                        - Each object must strictly follow this schema:  

                        ```json
                        {{
                        "Use Case": "string",
                        "Test Scenario": "string",
                        "Preconditions": "string",
                        "Input": "string (actions or data inputs required)",
                        "Expected Result": "string (expected system outcome, including correct UI label)"
                        }}
                    """
                elif (key == "pricing"):
                    prompts["pricing"] = f"""
                        Based on the following pricing information: {srd_content["pricing"]}.

                        **Task:**  
                        Generate **concise but complete test cases** to verify the correct handling of pricing. Avoid redundant or repetitive cases that only differ by data values. Instead, focus on **unique functional and logical scenarios**.

                        **Instructions for Generating Test Cases:**

                        1. **Free or Fixed Price:**  
                        - Generate exactly one test case to confirm that the displayed price matches the documented price.  
                        - If a payment expiration time is specified, generate one test case to confirm that expiration is enforced correctly.  

                        2. **Dynamic or Logic-Based Pricing:**  
                        - Generate a set of test cases that fully verify the logic, each input and it's pricing.  
                        - Include representative positive and negative inputs to confirm that calculations are correct across categories.  
                        - Include edge cases if applicable.  
                        - Generate a testcase to verify that payment expiration time is handled correctly.  

                        3. **Avoid Redundancy:** 

                        4. **Reference Past Examples:** Follow the structre in past test cases: {context}.  

                        **Output Requirements:**  
                        - Respond ONLY with a valid JSON array enclosed in a ```json code block.  
                        - Do not include any explanations or extra text outside the JSON.  
                        - Each object must strictly follow this schema:  

                        ```json
                        {{
                        "Use Case": "string",
                        "Test Scenario": "string",
                        "Preconditions": "string",
                        "Input": "string (a numbered list of inputs, or representative values for pricing)",
                        "Expected Result": "string (a numbered list of all expected outcomes, including correct price and expiration handling)"
                        }}
                    """ 
                elif (key == "next steps"):
                    prompts["next steps"] = f"""Given the following next steps array: {srd_content["next steps"]}.  

                        **Task:**
                        1. **Reference Past Examples:** Follow the exact structure and level of detail from previous test case examples: {context}.
                        2. Generate a **comprehensive set of test cases** to verify that each step (Title + Description) is correctly displayed and behaves according to the requirements.  
                        - Every step in the array must have at least one test case.  
                        - The test cases must validate **title text, description text, sequence order, and display conditions**.

                        4. **Output Format:**  
                        - Respond **only** with a valid JSON array enclosed in a ```json code block.  
                        - Do not include explanations, markdown headers, or extra text outside the JSON.  
                        - Each object must strictly follow this schema:  

                        ```json
                        {{
                        "Use Case": "string",
                        "Test Scenario": "string",
                        "Preconditions": "string",
                        "Input": "string (if applicable; a numbered list of the inputs to trigger different scenario)",
                        "Expected Results": "string (a numbered list of all expected results)"
                        }}
                    """ 
                elif (key == "notifications"):
                    prompts["notifications"] = f"""Based on the provided email notifications: {srd_content["notifications"]["emails"]} and SMS notifications: {srd_content["notifications"]["sms"]}. 
                    
                        **Task:**  
                        1. **Reference Past Examples:** Follow the exact structure and level of detail from previous test case examples: {context}.  
                        2. Generate a complete set of test cases.  
                        - There must be **one test case for every notification described** (both Email and SMS).  
                        - Do not skip or summarize.  
                        - Each notification (email or SMS) must have its own distinct JSON object.  
                        - Cover both the subject and the body content, including all dynamic variables (e.g., application number, billing number, applicant name, officer remarks).  
                        
                        **Output Format:**

                        - Respond **only** with a valid JSON array enclosed in a ```json code block.  
                        - Do not include explanations, markdown headers, or extra text outside the JSON.  
                        - Each object must strictly follow this schema:

                        ```json
                        {{
                        "Use Case": "string",
                        "Test Scenario": "string",
                        "Preconditions": "string",
                        "Input": "string",
                        "Expected Results": "string (a numbered list of all expected results)",
                        }}
                    """

            return prompts
        except Exception as e:
            logger.error(f"Error creating prompts: {e}")
            raise
        
def main():
    dd = GroqApi()
    sd = dd.callGroq("Hello")

    print('>>>>', sd)

if __name__ == "__main__":
    result = main()