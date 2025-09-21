from typing import List, Dict
import google.generativeai as genai
from testcase_generator import settings
import logging
import json
import re
from .groq_service import GroqApi
from .conversation_memory_service import ConversationMemoryAgent

logger = logging.getLogger(__name__)

class GemmaServ:
    def __init__(self):
        self.model = "gemini-1.5-flash"
        self.token = settings.GOOGLE_GENERATIVE_AI_API_KEY
        self.memory_agent = ConversationMemoryAgent()
        genai.configure(api_key=self.token)

    def query_gemma_images(self, prompt: str, image_path: str ) -> str:
        try:
            model = genai.GenerativeModel(self.model)
            with open(image_path, "rb") as f:
              img_bytes = f.read()

            image_part = {
                "mime_type": "image/png",
                "data": img_bytes,
            }
            response = model.generate_content([prompt, image_part])
            return [x for x in response.text.split('\n') if x != '']
            
        except Exception as e:
            return f"An error occurred while interacting with Gemma: {e}"
        
    def query_gemma_text(self, prompt: str) -> str:
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt, generation_config={
            "temperature": 0.2,         # keep low for structured test cases
            "top_p": 1.0,               # full probability mass
            "max_output_tokens": 4096,  # adjust if test cases are large
            },)
            return response.text

        except Exception as e:
            return f"An error occurred while interacting with Gemma: {e}"
        
    def query_gemma_batch(self, prompts: List[str]) -> List[str]:
        model = genai.GenerativeModel(self.model)
        responses = []
        try:
            response = model.generate_content(prompts, generation_config={
            "temperature": 0.2,
            "top_p": 1.0,
            "max_output_tokens": 80000,
            })

            print('>>>', response.candidates)
            regex = r"```json\s*(\[.*?\])\s*```"
            cc = re.findall(regex, response.candidates["text"], re.DOTALL)

            for a in cc:
             responses.extend(json.loads(a))

            # for candidate in response.candidates:
            #     responses.append(candidate.text)

            return responses
        except Exception as e:
            return f"An error occurred while interacting with Gemma: {e}"
        
    def generate_cases(self, srd_content: str, similar_examples: List[Dict]) -> List[Dict]:
        """Generate test cases based on SRD and similar examples"""
        try:
            srd_content_dict = json.loads(srd_content)
            # Prepare context from similar examples
            context = self._prepare_context(similar_examples)
            
            # Create prompt for test case generation
            prompt = self.create_test_case_prompt(srd_content_dict, context)
            
            # Include chat history
            # conversation_text = self.memory_agent.get_history()
            # full_prompt = conversation_text + f"User: {prompt}\n"

            # Generate response
            # ai_model = GroqApi()
            # response = ai_model.callGroq(prompt)

            response = self.query_gemma_batch(prompt)

            # Save into memory
            self.memory_agent.add_interaction(prompt, response)

            # Parse response into test cases
            test_cases = self.parse_test_cases_response(response)
            
            return test_cases
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            return []
        
    def improve_last_response(self, query) -> str:
        """Ask Groq to improve the last AI response."""
        try:
            last_response = self.memory_agent.get_last_ai_response()
            if not last_response:
                return "No previous response found to improve."

            improve_prompt = f"{query}. update test cases:\n{last_response}"
            ai_model = GroqApi()
            response_text = ai_model.callGroq(improve_prompt)

            self.memory_agent.add_interaction(query, response_text)

            test_cases = self.parse_test_cases_response(response_text)

            return test_cases

        except Exception as e:
            return f"Error improving last response: {e}"
    
    def _prepare_context(self, similar_examples: List[Dict]) -> str:
        context = "Here are some examples of test cases from similar services:\n\n"
        
        for i, example in enumerate(similar_examples[:3], 1):
            context += f"Example {i}:\n"
            context += f"Content: {example.get('content', '')[:500]}...\n\n"
        
        return context
    
    def create_test_case_prompt(self, srd_content: str, context: str) -> str: 
        for key in srd_content:
            if (key == "service details"):
                    service_details_prompt = f""" Given the following requirements: 
                    
                            **SRD**
                            
                            - Service details: {srd_content["service details"]}.
                            - SLA (Processing time): {srd_content["sla"]}.

                            **Task:**
                            1. Analyze the provided requirements and Generate exactly one test case for every element.
                            - Generate a testcase to verify that the correct service name is displayed on the page. 
                            - Generate a testcase to verify that the correct service description is displayed on the page. 
                            - Generate a testcase to verify that the correct Institution provider is displayed on the page. 
                            - Generate a testcase to verify that the correct SLA is displayed on the page as Processing time.

                            **Column Content Requirements:**

                            - **Use Case**: A short, high-level description of what is being tested (e.g., "Verify Service Name").  

                            - **Test Scenario**: A specific scenario that explains the testing context (e.g., "Check the service name on the Service Details page").  

                            - **Preconditions**: Any setup needed before execution (e.g., "User is logged into the citizen portal").  

                            - **Input**: Actions the tester must perform (e.g., "Navigate to the service details page or System event if performed by sytem").  

                            - **Expected Results**: A **numbered list of exact expected values taken directly from the SRD** (e.g., "1. The displayed service name is 'Purchase the semen (Intanga)'"). 
                            
                            **Reference past test case structure for consistency: {context}
                            
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
                            "Expected Results": "string"
                            }}
                    """
            elif (key == "form fields"):
                    form_fields_prompt = f"""
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
                        "Expected Results": "string (error messages, field behaviours, e.t.c)"
                        }}
                    """
            elif (key == "workflow"): 
                    workflow_context_and_labels_prompt = f"""
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
                    pricing_prompt = f"""
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
                    next_steps_prompt = f"""Given the following next steps array: {srd_content["next steps"]}.  

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
                    notifications_prompt = f"""Based on the provided email notifications: {srd_content["notifications"]["emails"]} and SMS notifications: {srd_content["notifications"]["sms"]}. 
                    
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

        return [service_details_prompt, form_fields_prompt, workflow_context_and_labels_prompt, pricing_prompt, next_steps_prompt, notifications_prompt]
    
    def parse_test_cases_response(self, response: str) -> List[Dict]:
        try:
            json_start = response.find('[')
            json_end = response.rfind(']')
            
            if json_start == -1 or json_end == -1 or json_end <= json_start:
                print("Error: Could not find a valid JSON array in the response.")
                return []
                
            json_string = response[json_start : json_end + 1]
            
            test_cases = json.loads(json_string)
            
            refactored_test_cases = []
            for case in test_cases:
                refactored_case = {
                    "use_case": case.get("Use Case"),
                    "test_scenario": case.get("Test Scenario"),
                    "priority": case.get("Priority"),
                    "preconditions": case.get("Preconditions"),
                    "input_data": case.get("Input"),
                    "expected_result": case.get("Expected Result"),
                    "test_type": case.get("Test Type")
                }
                refactored_test_cases.append(refactored_case)
                
            return refactored_test_cases
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []