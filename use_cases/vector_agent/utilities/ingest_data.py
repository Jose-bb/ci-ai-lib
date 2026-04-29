import os
import sys
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from use_cases.vector_agent.src.vector_engine import VectorEngine

def main():
    print("Starting ChromaDB data ingestion process...\n")
    
    load_dotenv()
    
    try:
        engine = VectorEngine()
        print("Vector Engine initialized successfully.")
    except Exception as e:
        print(f"Error initializing Vector Engine: {e}")
        return

    hr_collection = "hr_manual_docs"
    hr_texts = [
        "Vacation Policy: All employees are entitled to 25 days of paid vacation per year. Vacation requests must be approved by the direct manager at least two weeks in advance.",
        "Remote Work: Employees are allowed to work remotely up to 3 days a week. The core mandatory office days are Tuesday and Thursday.",
        "Equipment Allowance: The company provides a $500 one-time stipend for home office equipment setup upon passing the probation period."
    ]
    hr_metadata = [{"source": "hr_policy_v2.pdf", "page": 1}, {"source": "hr_policy_v2.pdf", "page": 2}, {"source": "benefits.pdf", "page": 1}]

    it_collection = "it_support_docs"
    it_texts = [
        "VPN Setup: To connect to the corporate VPN, open the Cisco AnyConnect client, enter 'vpn.company.com', and authenticate using your Single Sign-On (SSO) credentials and Duo MFA.",
        "Password Reset: IT will never ask for your password. To reset your password, visit password.company.local. Passwords must be at least 14 characters long and include numbers and symbols.",
        "Hardware Requests: If your laptop needs repair or replacement, open a ticket in Jira Service Desk under the 'Hardware Asset' category. Loaner laptops are available at the IT desk."
    ]
    it_metadata = [{"source": "it_wiki", "topic": "network"}, {"source": "it_wiki", "topic": "security"}, {"source": "it_wiki", "topic": "hardware"}]

    legal_collection = "legal_archive_docs"
    legal_texts = [
        "Non-Disclosure Agreement (NDA): The receiving party agrees to keep all proprietary information strictly confidential for a period of 5 years from the date of disclosure.",
        "Liability Limitation: Under no circumstances shall the software provider be liable for indirect, incidental, or consequential damages arising out of the use of the platform. Maximum liability is capped at the annual subscription fee.",
        "Termination Clause: Either party may terminate this agreement with a 30-day written notice. In the event of material breach, termination is immediate."
    ]
    legal_metadata = [{"source": "standard_nda.docx", "type": "confidentiality"}, {"source": "saas_terms.pdf", "type": "liability"}, {"source": "vendor_agreement.pdf", "type": "termination"}]

    print(f"\nInjecting data into collection '{hr_collection}'...")
    print(engine.add_documents(texts=hr_texts, collection_name=hr_collection, metadatas=hr_metadata))

    print(f"\nInjecting data into collection '{it_collection}'...")
    print(engine.add_documents(texts=it_texts, collection_name=it_collection, metadatas=it_metadata))

    print(f"\nInjecting data into collection '{legal_collection}'...")
    print(engine.add_documents(texts=legal_texts, collection_name=legal_collection, metadatas=legal_metadata))

    print("\nProcess completed! The ChromaDB vector database is now populated with knowledge.")

if __name__ == "__main__":
    main()