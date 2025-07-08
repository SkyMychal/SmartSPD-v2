#!/usr/bin/env python3
"""
Simple document processing test without full database setup

This test focuses on:
1. Reading the sample documents
2. Testing document processing logic
3. Verifying file parsing capabilities
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_sample_documents():
    """Test reading and analyzing the sample documents"""
    
    print("🚀 SmartSPD v2 - Document Analysis Test")
    print("=" * 60)
    
    documents_dir = Path("/workspaces/SmartSPD-v2/SPD_BPS_Examples")
    
    if not documents_dir.exists():
        print(f"❌ Documents directory not found: {documents_dir}")
        return
    
    print(f"📂 Analyzing documents in: {documents_dir}")
    print()
    
    # Get all documents
    pdf_files = list(documents_dir.glob("*.pdf"))
    excel_files = list(documents_dir.glob("*.xlsx"))
    
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        file_size = pdf_file.stat().st_size
        print(f"  • {pdf_file.name} ({file_size:,} bytes)")
    
    print(f"\n📊 Found {len(excel_files)} Excel files:")
    for excel_file in excel_files:
        file_size = excel_file.stat().st_size
        print(f"  • {excel_file.name} ({file_size:,} bytes)")
    
    print(f"\n📋 Total documents: {len(pdf_files) + len(excel_files)}")
    
    # Test PDF reading capability
    print("\n🔍 Testing PDF Reading Capability...")
    test_pdf_reading(pdf_files)
    
    # Test Excel reading capability  
    print("\n📈 Testing Excel Reading Capability...")
    test_excel_reading(excel_files)
    
    # Generate test queries
    print("\n❓ Sample Test Queries for Health Plan Documents:")
    generate_test_queries()

def test_pdf_reading(pdf_files):
    """Test if we can read PDF files"""
    
    try:
        import PyPDF2
        print("✅ PyPDF2 available for PDF processing")
        
        for pdf_file in pdf_files[:1]:  # Test first PDF
            try:
                with open(pdf_file, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    num_pages = len(reader.pages)
                    print(f"  📄 {pdf_file.name}: {num_pages} pages")
                    
                    # Try to extract some text from first page
                    if num_pages > 0:
                        first_page = reader.pages[0]
                        text = first_page.extract_text()
                        text_sample = text[:200].replace('\n', ' ').strip()
                        print(f"     Sample text: {text_sample}...")
                        
            except Exception as e:
                print(f"  ❌ Error reading {pdf_file.name}: {e}")
                
    except ImportError:
        print("⚠️  PyPDF2 not available - would need to install for PDF processing")
        
        # Check if pdfplumber is available as alternative
        try:
            import pdfplumber
            print("✅ pdfplumber available as alternative")
        except ImportError:
            print("⚠️  pdfplumber also not available")

def test_excel_reading(excel_files):
    """Test if we can read Excel files"""
    
    try:
        import pandas as pd
        print("✅ pandas available for Excel processing")
        
        for excel_file in excel_files[:1]:  # Test first Excel file
            try:
                # Read Excel file
                xlsx = pd.ExcelFile(excel_file)
                sheet_names = xlsx.sheet_names
                print(f"  📊 {excel_file.name}: {len(sheet_names)} sheets")
                print(f"     Sheets: {', '.join(sheet_names)}")
                
                # Read first sheet
                if sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_names[0])
                    print(f"     First sheet '{sheet_names[0]}': {df.shape[0]} rows, {df.shape[1]} columns")
                    
                    if not df.empty:
                        print(f"     Column names: {list(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                        
            except Exception as e:
                print(f"  ❌ Error reading {excel_file.name}: {e}")
                
    except ImportError:
        print("⚠️  pandas not available - would need to install for Excel processing")
        
        # Check if openpyxl is available
        try:
            import openpyxl
            print("✅ openpyxl available as alternative")
        except ImportError:
            print("⚠️  openpyxl also not available")

def generate_test_queries():
    """Generate comprehensive test queries for health plan documents"""
    
    queries = {
        "Deductible Inquiries": [
            "What is my deductible for medical services?",
            "How much is the individual deductible?",
            "What's the family deductible amount?",
            "Are there separate deductibles for in-network and out-of-network?",
            "When does my deductible reset?"
        ],
        
        "Copay Questions": [
            "How much is a copay for a primary care visit?",
            "What's the copay for specialist visits?",
            "How much do I pay for urgent care?",
            "What's the emergency room copay?",
            "Are there copays for preventive care?"
        ],
        
        "Coverage Questions": [
            "Does my plan cover prescription drugs?",
            "Is emergency room care covered?",
            "What preventive care is covered at 100%?",
            "Are mental health services covered?",
            "Is maternity care included in my plan?"
        ],
        
        "Out-of-Pocket Limits": [
            "What are my out-of-pocket maximums?",
            "What's the family out-of-pocket maximum?",
            "Do copays count toward my out-of-pocket maximum?",
            "When do I reach my out-of-pocket limit?"
        ],
        
        "Network Questions": [
            "How does my plan handle specialist visits?",
            "What's the difference between in-network and out-of-network costs?",
            "Do I need referrals to see specialists?",
            "How do I find in-network providers?"
        ],
        
        "Prescription Coverage": [
            "How much do generic drugs cost?",
            "What's the copay for brand name medications?",
            "Is there a separate prescription deductible?",
            "Are specialty drugs covered?",
            "Can I use mail-order pharmacy?"
        ],
        
        "Complex Scenarios": [
            "What happens if I need surgery?",
            "How much would a hospital stay cost?",
            "What if I have an emergency while traveling?",
            "Compare my deductibles across different service types",
            "What are the annual limits on physical therapy?"
        ]
    }
    
    total_queries = 0
    for category, query_list in queries.items():
        print(f"\n  📋 {category}:")
        for query in query_list:
            print(f"     • {query}")
        total_queries += len(query_list)
    
    print(f"\n📊 Total test queries: {total_queries}")
    
    return queries

def check_processing_dependencies():
    """Check what dependencies are available for document processing"""
    
    print("\n🔧 DEPENDENCY CHECK")
    print("=" * 60)
    
    dependencies = {
        "PDF Processing": ["PyPDF2", "pdfplumber", "pymupdf"],
        "Excel Processing": ["pandas", "openpyxl", "xlrd"],
        "Text Processing": ["nltk", "spacy", "transformers"],
        "Vector Embeddings": ["openai", "sentence-transformers", "faiss"],
        "Database": ["sqlalchemy", "psycopg2", "asyncpg"],
        "API Framework": ["fastapi", "uvicorn", "pydantic"]
    }
    
    for category, libs in dependencies.items():
        print(f"\n📦 {category}:")
        for lib in libs:
            try:
                __import__(lib)
                print(f"  ✅ {lib}")
            except ImportError:
                print(f"  ❌ {lib}")

if __name__ == "__main__":
    test_sample_documents()
    check_processing_dependencies()
    
    print("\n🎯 NEXT STEPS FOR FULL TESTING:")
    print("=" * 60)
    print("1. 🐳 Start Docker environment: ./start_development.sh")
    print("2. 📤 Upload documents via API: POST /api/v1/documents/upload")
    print("3. ⏳ Wait for processing: GET /api/v1/documents/{id}")
    print("4. 🔍 Test queries: POST /api/v1/chat/query")
    print("5. 📊 Check analytics: GET /api/v1/analytics/dashboard")
    
    print("\n✅ Document analysis test completed!")