import os
import truststore
truststore.inject_into_ssl()
from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

index = "code-refactor-policies"

def setup_pinecone_knowledge():
    pc = Pinecone()
    indexes = [idx["name"] for idx in pc.list_indexes()]
    if index not in indexes:
        pc.create_index(index, dimension=1024, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))

    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3" )

    policy_documents = [
        # --- Style & Clean Code ---
        Document(
            page_content="PEP 8 Imports: Unused imports should be removed from the top of Python files to maintain a clean namespace.",
            metadata={"category": "style", "rule_id": "PEP8-IMPORT"}
        ),
        Document(
            page_content="PEP 8 Naming: Function names should be lowercase, with words separated by underscores (snake_case) to improve readability.",
            metadata={"category": "style", "rule_id": "PEP8-NAMING"}
        ),
        Document(
            page_content="PEP 8 Line Length: Limit all lines to a maximum of 88 characters (Black style guideline) or 79 characters (standard PEP 8).",
            metadata={"category": "style", "rule_id": "PEP8-LINE-LENGTH"}
        ),

        # --- Security (OWASP) ---
        Document(
            page_content="OWASP SEC-01: Never hardcode sensitive parameters, credentials, API keys, or database connection strings. Always use environment variables.",
            metadata={"category": "security", "rule_id": "OWASP-01"}
        ),
        Document(
            page_content="OWASP SEC-02: Avoid raw SQL string formatting or concatenation. Always use parameterized queries or an ORM to prevent SQL Injection.",
            metadata={"category": "security", "rule_id": "OWASP-02"}
        ),
        Document(
            page_content="OWASP SEC-03: Use subprocess safely. Avoid passing 'shell=True' when calling external commands to prevent command injection vulnerabilities.",
            metadata={"category": "security", "rule_id": "OWASP-03"}
        ),

        # --- Error Handling & Testing ---
        Document(
            page_content="ERR-01: Bare Exception Clauses: Avoid using bare 'except:' clauses. Always catch specific exceptions (e.g., ValueError, KeyError) to avoid masking unexpected system signals.",
            metadata={"category": "error_handling", "rule_id": "EXCEPT-SPECIFIC"}
        ),
        Document(
            page_content="ERR-02: Resource Cleanup: Always close open file handlers or network connections explicitly, ideally using context managers ('with' statements).",
            metadata={"category": "error_handling", "rule_id": "CONTEXT-MANAGER"}
        ),
        Document(
            page_content="TEST-01: Pytest Assertions: Unit test functions must start with 'test_' and use explicit assertions comparing actual versus expected return values.",
            metadata={"category": "testing", "rule_id": "PYTEST-STRUCTURE"}
        ),

        # --- Logic & Business Bugs ---
        Document(
            page_content="MATH-ERR: Verify arithmetic operators when calculating discounts or ratios. Discount logic should subtract (price * discount_rate) from base price.",
            metadata={"category": "bugfix", "rule_id": "LOGIC-MATH"}
        ),
        Document(
            page_content="TYPE-CHECK: Ensure input parameters match expected types before performing calculations (e.g., cast numeric inputs or validate float ranges).",
            metadata={"category": "bugfix", "rule_id": "TYPE-VALIDATION"}
        ),
    ]

    PineconeVectorStore.from_documents(
        documents=policy_documents,
        embedding=embeddings,
        index_name=index
    )

setup_pinecone_knowledge()