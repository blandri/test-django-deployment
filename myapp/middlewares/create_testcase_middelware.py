from ..services.notion_service import NotionClient
from ..services.rag_service import RAGService
from ..services.gemma_service import GemmaServ
from ..helpers.excel_generator import ExcelGenerator
from ..services.groq_service import GroqApi
from testcase_generator import settings
import os
import shutil

class CreateTestCaseMiddleWare:
    def __init__(self, pageId):
        self.notionPageId = pageId
        # self.notionClient = NotionClient(settings.NOTION_API_KEY)
        self.rag = RAGService()
        self.gemma = GemmaServ()
        self.groq = GroqApi()
        self.excelGenerator = ExcelGenerator()
        self.imagesDir = "images"
        self.testcasesDir = "files"

    def testcase_generation (self):
        # shutil.rmtree(self.testcasesDir)

        # res = self.notionClient.notion_to_markdown(self.notionPageId)

        # files = os.listdir(self.imagesDir)
        
        # workflowInfo = self.gemma.query_gemma('Analyse this workflow diagram and generate texts explaining all the actions and events in it, respond with a numbered list.', f"{self.imagesDir}/{files[0]}")

        # new_res = res.replace('Image_placeholder', f'''{workflowInfo}''')

        jk = f"""# Document History


| **#Version** |   **Date**   |    **Author**    | **Change Description** | **Link to document** |
| ------------ | ------------ | ---------------- | ---------------------- | -------------------- |
| 1            | Jan 16, 2024 | @Miracle Mbionwu |                        |                      |
|              |              |                  |                        |                      |


# **Overview**


Service details (1)


## Service details (1)


## **Activity Diagram**





## **Use-case Diagram**





# **Form Information**


### Form Elements


_A is a group of 1 or more blocks_


|      **Section**       |       **Block**        |                       **Field name**                       |        **Type**         |       **Hint**       | **Tooltip** |                                                           **Placeholder (for inputs only)/List of values (for drop downs)**                                                           |                                 **Widget requirements**                                 |                                         **Validation Rule**                                          |                                                           **Display Rule**                                                           |    **Error Message**     |
| ---------------------- | ---------------------- | ---------------------------------------------------------- | ----------------------- | -------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------ |
| Applicant details      | Applicant details      | ID number                                                  | NID widget              | Enter your ID number | N/A         |                                                                                                                                                                                       | *** Surname**Field destination:  Surname*** Other names**Field destination: Other names | - Required-The national ID must be valid and exist in the NIDA system - ID Number must be 16 digits. | - Sorry, we can’t find your identification data from NIDA system. Please contact NIDA for more details.- ID number must be 16 digits | This field is required   |
|                        |                        | Surname                                                    | Information list widget | N/A                  | N/A         | N/A                                                                                                                                                                                   |                                                                                         | Required                                                                                             | This is displayed when the NID is fetched                                                                                            |                          |
|                        |                        | Other names                                                | Information list widget | N/A                  | N/A         | N/A                                                                                                                                                                                   |                                                                                         | RequiredDisabled                                                                                     | This is displayed when the NID is fetched                                                                                            |                          |
|                        |                        | Email address                                              | Input field             |                      |             | Enter email address                                                                                                                                                                   |                                                                                         | - Required- The system should validate the right email format validation (eg: Example@mail.com)      |                                                                                                                                      | Email format not correct |
|                        |                        | District                                                   | Location widget         |                      | N/A         | **Placeholder:** Select district                                                                                                                                                      | Rwandan districts                                                                       | Required                                                                                             |                                                                                                                                      | This field is required   |
|                        |                        | Designation                                                | Input Field             |                      | N/A         | Enter your designation                                                                                                                                                                |                                                                                         | Required                                                                                             |                                                                                                                                      | This field is required   |
| Semen purchase details | Semen purchase details | Type of Semen                                              | Multi select            |                      | N/A         | **Placeholder:** Select the type of Semen for purchase:- Sexed Semen (Intanga z’inyana)- Procured outside(Friesian, Jersey, other breeds)- Ordinary semen(Friesian, Jersey)- Ordinary |                                                                                         | Required                                                                                             | a user should be able to select multiple products                                                                                    | This field is required   |
|                        |                        | Quantity Sexed Semen (Intanga z’inyana)                    | Number field            | N/A                  | N/A         | Enter Quantity for selected semen purchase                                                                                                                                            |                                                                                         | Required                                                                                             | Display when - Sexed Semen (Intanga z’inyana) is selected                                                                            | This field is required   |
|                        |                        | Quantity Procured Outside (Friesian, Jersey, other breeds) | Number field            | N/A                  | N/A         | Enter Quantity for selected semen purchase                                                                                                                                            |                                                                                         | Required                                                                                             | Display, when Procured outside, is selected                                                                                          | This field is required   |
|                        |                        | Quantity Ordinary Semen (Friesian, Jersey)                 | Number field            | N/A                  | N/A         | Enter Quantity for selected semen purchase                                                                                                                                            |                                                                                         | Required                                                                                             | Dsiplay when  Ordinary semen is selected                                                                                             | This field is required   |
|                        |                        | Quantity Ordinary                                          | Number field            | N/A                  | N/A         | Enter Quantity for selected semen purchase                                                                                                                                            |                                                                                         | Required                                                                                             | Display when Ordinary is selected                                                                                                    | This field is required   |
|                        |                        | Total Price                                                | Number                  |                      | N/A         |                                                                                                                                                                                       | (Quantity *unity price)  + other selected types of semen                                | - Required- Disabled                                                                                 | Depending on the type of Semen and quantity                                                                                          | This field is required   |
| RAB station            | RAB station            | RAB station                                                |                         | N/A                  | N/A         | Select RAB Station{'RUBIRIZIMULINDIMUSANZERWERERENYAMAGABERUBONASONGAMUHANGANYAGATARENGOMANTENDEZIGAKUTAGISHWATITAMIRA'}                                                                |                                                                                         | Required                                                                                             |                                                                                                                                      | This field is required   |


## **Pricing**


## **Currency**


RWF


## **Payment Expiration Time**


30 days


## **Service Pricing**


### **Dynamic**


|                **Type of semen**                 | **Amount(RWF)** |
| ------------------------------------------------ | --------------: |
| Sexed Semen (Intanga z’inyana)                   |           26000 |
| Procured outside(Friesian, Jersey, other breeds) |           16000 |
| Ordinary semen(Friesian, Jersey)                 |            5000 |
| Ordinary                                         |            1500 |


### **Fixed**


**Service Payment Code**


## **Service Payment Code**


**UAT:** RRA-c9d30ff7c3


**Prod**


## Payment merchant


GOR


### Payment account identifier


GOR-CG-RWF


**Service PowerBI details**


|          Service name           |                                                                Purchase the bovine semen                                                                 |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Service payment code            | RRA-c9d30ff7c3                                                                                                                                           |
| Application type                | JSON_FORM_2238                                                                                                                                           |
| Tables the service is utilizing | service_change_request, service_change_request_details, irembo_service, application, application_preference, grouped_service, service_category, category |


# **Workflow**


## Workflow configuration


### Workflow selection


Apply- Validate - Pay


["Here's a numbered list explaining the actions and events in the workflow diagram:", '1. **Start:** The process begins with an applicant initiating an application.', '2. **Apply:** The applicant submits an application.  A "Submitted" document is generated.', '3. **Assign application to office:** The IremboGov engine automatically assigns the submitted application to a relevant office or officer. A "Pending approval" document is generated.', '4. **Reject:** An officer reviews the application and rejects it. A "Rejected" document is generated, ending the application process for this instance.', '5. **Approve:** An officer reviews the application and approves it. A "Payment pending" document is generated.', '6. **RFA (Request for Additional Information):** An officer reviews the application and requests further information from the applicant. A "Pending resubmission" document is generated.', '7. **Update application:** The applicant provides the requested information and updates their application.  A "Resubmitted" document is generated and the process loops back for review.', '8. **Bill ID:** After approval, a bill ID is generated.', '9. **Pay:** The applicant pays the bill using the generated Bill ID. A "Paid" document is generated.', '10. **End:** The process concludes successfully after payment.', 'The diagram shows a clear path for application processing, including rejection, approval, and request for additional information scenarios.  The use of documents at various stages highlights the documentation trail throughout the process.']


### Labels of status


These are labels that the end-user will see.


|   Workflow Status    |        Label         |
| -------------------- | -------------------- |
| Submitted            | Submitted            |
| Pending approval     | Pending approval     |
| Payment pending      | Payment pending      |
| Rejected             | Rejected             |
| Pending resubmission | Pending resubmission |
| Resubmitted          | Resubmitted          |
| Paid                 | Paid                 |


### Next steps


| Step |                          Title                           |                                                                                                                                                              Description                                                                                                                                                              |
| ---- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Payment                                                  | Use your bill ID to pay for your services using any of the methods provided in the “Payment options” section.                                                                                                                                                                                                                         |
| 2    | When should you expect the notification of getting semen | Upon submission, you will receive another SMS and/or email to confirm the payment. Once Veterinary receives and approves your application you will receive your notification via email. If you don’t receive an SMS notifying your application status within three working days after submission, please contact or visit RAB office. |


## SLAs


3 days


## Notifications


_What notifications should be expected at each transition?_


### For citizens


**SMS**


|      **Status**                                                                                                                                                                                                                                                                                       **SMS Notification (English)**                                                                                                                                                                                                                                                                                                      |      **SMS Notification (French)**      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| Submitted            | Dear ($applicant_name), Your application for ($service_name) was successfully submitted! You can track your application with the following details: Application number: ($application_number) Status: Submitted Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this email by mistake, please ignore it!                                                                                                                                                                                                       | remarks: $RFA_remarks You can make thes |
| Payment pending      | Dear ($applicant_name) Your application for: **$Service name** with billing number **$billing_number** was successfully approved! **Billing number:** $billing_number **Status**: Payment pending **Fees to be paid**: $price RWF **Pay Before**: DD-MM-YYYY HH:MM • ***Thank you for using IremboGov! For support, call 9099 If you are receiving this e-mail by mistake, please ignore it!                                                                                                                                                                                                                       | remarks: $RFA_remarks You can make thes |
| Rejected             | Dear ($applicant_name), Your application for ($service_name) ****was rejected! These are your application details: Application number: $application_number Status: Rejected Reason for rejection: $reason_for_rejection Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this email by mistake, please ignore it!                                                                                                                                                                                               | remarks: $RFA_remarks You can make thes |
| Pending resubmission | Dear ($applicant_name), Your application for ($service_name) necessitates further action. Please follow the instructions according to the officer's remarks listed below: These are your application details: Application number: $application_number Status: Request for action Officer's remarks: $RFA_remarks You can make these changes by finding your application on IremboGov, or through an IremboGov agent. Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this e-mail by mistake, please ignore it. | remarks: $RFA_remarks You can make thes |
| Resubmitted          | Dear ($applicant_name), Your application for ($service_name) was successfully resubmitted! These are your application details: Application number: $application_number Status: Resubmitted Your application will be processed and you will be notified regarding any change in the status of your application. Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this e-mail by mistake, please ignore it.                                                                                                       |                                         |
| Paid                 | Dear ($applicant_name)**,**  Your application for: **$Service name** with billing number **$billing_number** was successfully paid! **Application number:** $application_number **Status**: Paid **Fees paid**: $price RWF Thank you for using IremboGov! For support, call 9099 If you are receiving this e-mail by mistake, please ignore it!                                                                                                                                                                                                                                                                    |                                         |


**Email**


|      **Status**      |                         **Email Subject**                         |                                                                                                                                                                                                                                                                                           **Email Body (English)**                                                                                                                                                                                                                                                                                                 |         **Email Body (French)**        |
| -------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------- |
| Submitted            | _Application Submitted_ **for “Service name”**                    | Dear ($applicant_name), Your application for ($service_name) was successfully submitted! You can track your application with the following details: Application number: ($application_number) Status: Submitted Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this email by mistake, please ignore it!                                                                                                                                                                                                       | remarks: $RFA_remarks You can make thes|
| Payment pending      | Payment pending ****for “Service name”**                          | Dear ($applicant_name) Your application for: **$Service name** with billing number **$billing_number** was successfully approved! **Billing number:** $billing_number **Status**: Payment pending **Fees to be paid**: $price RWF **Pay Before**: DD-MM-YYYY HH:MM • ***Thank you for using IremboGov! For support, call 9099 If you are receiving this e-mail by mistake, please ignore it!                                                                                                                                                                                                                       | remarks: $RFA_remarks You can make thes|
| Rejected             | _Application rejected_ **for “Service name”**                     | Dear ($applicant_name), Your application for ($service_name) ****was rejected! These are your application details: Application number: $application_number Status: Rejected Reason for rejection: $reason_for_rejection Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this email by mistake, please ignore it!                                                                                                                                                                                               | remarks: $RFA_remarks You can make thes|
| Pending resubmission | _Application requested for further action_ **for “Service name”** | Dear ($applicant_name), Your application for ($service_name) necessitates further action. Please follow the instructions according to the officer's remarks listed below: These are your application details: Application number: $application_number Status: Request for action Officer's remarks: $RFA_remarks You can make these changes by finding your application on IremboGov, or through an IremboGov agent. Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this e-mail by mistake, please ignore it. | remarks: $RFA_remarks You can make thes|
| Resubmitted          | _Application resubmitted_ **for “Service name”**                  | Dear ($applicant_name), Your application for ($service_name) was successfully resubmitted! These are your application details: Application number: $application_number Status: Resubmitted Your application will be processed and you will be notified regarding any change in the status of your application. Thank you for using IremboGov! Need help? Email us at [support@irembo.com](mailto:support@irembo.com) Visit our Support Center If you are receiving this e-mail by mistake, please ignore it.                                                                                                       | remarks: $RFA_remarks You can make thes|
| Paid                 | Successful payment **for “Service name”**                         | Dear ($applicant_name)**,**  Your application for: **$Service name** with billing number **$billing_number** was successfully paid! **Application number:** $application_number **Status**: Paid **Fees paid**: $price RWF Thank you for using IremboGov! For support, call 9099 If you are receiving this e-mail by mistake, please ignore it!                                                                                                                                                                                                                                                                    | remarks: $RFA_remarks You can make thes|



### Database: Service details (1)

| Disclaimer | Institution | Service group | Service summary | Service name | Service Category | # |
| --- | --- | --- | --- | --- | --- | --- |
|  | Rwanda Agriculture and Animal Resources Development Board (RAB) | Purchase the semen (Intanga) | This service is for a district to purchase Semen from RAB. | Purchase the semen (Intanga) | Agriculture | 1 |"""

        analysed_srd = self.rag.analyze_srd_data(jk)

        similarDocuments = self.rag.retrieve_similar_content("Find similar testcases with this service", analysed_srd, 20)
        # print('++++', similarDocuments)
        # Gemma
        cases = self.gemma.generate_cases(analysed_srd, similarDocuments)

        # groq
        # cases = self.groq.generate_testcases(analysed_srd, similarDocuments)
        print('>>>', cases)
        excelFile = self.excelGenerator.generate_testcase_excel(cases, "Semen")

        # shutil.rmtree(self.imagesDir)

        return excelFile