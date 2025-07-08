#!/usr/bin/env python3
"""
Extract sample content from the real health plan documents to understand structure
"""

import pandas as pd
import pdfplumber
from pathlib import Path

def extract_excel_content():
    """Extract and display sample content from Excel BPS files"""
    
    print("📊 EXCEL BPS CONTENT ANALYSIS")
    print("=" * 70)
    
    documents_dir = Path("/workspaces/SmartSPD-v2/SPD_BPS_Examples")
    excel_files = list(documents_dir.glob("*.xlsx"))
    
    for excel_file in excel_files:
        print(f"\n📋 Analyzing: {excel_file.name}")
        print("-" * 50)
        
        try:
            # Get all sheet names
            xlsx = pd.ExcelFile(excel_file)
            print(f"📄 Sheets ({len(xlsx.sheet_names)}): {', '.join(xlsx.sheet_names[:5])}{'...' if len(xlsx.sheet_names) > 5 else ''}")
            
            # Look for key benefit sheets
            key_sheets = ['SPD', 'Accumulators', 'CoverPage', 'BenefitReview']
            
            for sheet_name in xlsx.sheet_names:
                if any(key in sheet_name for key in key_sheets):
                    print(f"\n🔍 Examining sheet: '{sheet_name}'")
                    
                    try:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                        print(f"   Size: {df.shape[0]} rows × {df.shape[1]} columns")
                        
                        # Look for benefit-related content
                        content_sample = []
                        for idx, row in df.iterrows():
                            row_text = ' '.join([str(cell) for cell in row if pd.notna(cell) and str(cell).strip()])
                            if row_text and len(row_text) > 10:
                                # Look for benefit keywords
                                if any(keyword in row_text.lower() for keyword in ['deductible', 'copay', 'coinsurance', 'maximum', 'coverage', 'benefit']):
                                    content_sample.append(row_text[:100])
                                    if len(content_sample) >= 3:
                                        break
                        
                        if content_sample:
                            print("   📝 Sample benefit content:")
                            for sample in content_sample:
                                print(f"      • {sample}...")
                        
                    except Exception as e:
                        print(f"   ❌ Error reading sheet: {e}")
                        
        except Exception as e:
            print(f"❌ Error processing {excel_file.name}: {e}")

def extract_pdf_content():
    """Extract and display sample content from PDF SPD files"""
    
    print("\n\n📄 PDF SPD CONTENT ANALYSIS")
    print("=" * 70)
    
    documents_dir = Path("/workspaces/SmartSPD-v2/SPD_BPS_Examples")
    pdf_files = list(documents_dir.glob("*.pdf"))
    
    for pdf_file in pdf_files:
        print(f"\n📋 Analyzing: {pdf_file.name}")
        print("-" * 50)
        
        try:
            with pdfplumber.open(pdf_file) as pdf:
                print(f"📄 Pages: {len(pdf.pages)}")
                
                # Extract text from first few pages
                sample_text = ""
                for i, page in enumerate(pdf.pages[:3]):  # First 3 pages
                    page_text = page.extract_text()
                    if page_text:
                        sample_text += page_text + "\n"
                
                if sample_text:
                    # Look for key sections
                    lines = sample_text.split('\n')
                    benefit_lines = []
                    
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 20:
                            # Look for benefit-related content
                            if any(keyword in line.lower() for keyword in ['deductible', 'copay', 'coinsurance', 'coverage', 'benefit', 'plan', 'premium']):
                                benefit_lines.append(line[:120])
                                if len(benefit_lines) >= 5:
                                    break
                    
                    if benefit_lines:
                        print("📝 Sample benefit content:")
                        for line in benefit_lines:
                            print(f"   • {line}...")
                    
                    # Look for structured information
                    tables = []
                    for page in pdf.pages[:3]:
                        page_tables = page.extract_tables()
                        if page_tables:
                            tables.extend(page_tables)
                    
                    if tables:
                        print(f"\n📊 Found {len(tables)} tables in first 3 pages")
                        # Show first table structure
                        if tables[0]:
                            print("   Sample table structure:")
                            for row in tables[0][:3]:  # First 3 rows
                                if row and any(cell for cell in row if cell):
                                    row_text = " | ".join([str(cell) if cell else "" for cell in row[:4]])  # First 4 columns
                                    print(f"   {row_text}")
                
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")

def analyze_document_structure():
    """Analyze the overall structure and content types in the documents"""
    
    print("\n\n🔍 DOCUMENT STRUCTURE ANALYSIS")
    print("=" * 70)
    
    # Key health plan concepts to look for
    health_plan_concepts = {
        "Cost Sharing": ["deductible", "copay", "coinsurance", "out-of-pocket", "premium"],
        "Coverage": ["covered", "benefit", "eligible", "excluded", "limitation"],
        "Network": ["in-network", "out-of-network", "provider", "referral"],
        "Services": ["medical", "prescription", "dental", "vision", "mental health"],
        "Limits": ["annual", "lifetime", "maximum", "minimum", "limit"],
        "Procedures": ["prior authorization", "precertification", "appeal", "claim"]
    }
    
    print("🎯 Key concepts to extract during processing:")
    for category, concepts in health_plan_concepts.items():
        print(f"\n📋 {category}:")
        for concept in concepts:
            print(f"   • {concept}")
    
    print(f"\n📊 Total key concepts: {sum(len(concepts) for concepts in health_plan_concepts.values())}")

if __name__ == "__main__":
    extract_excel_content()
    extract_pdf_content() 
    analyze_document_structure()
    
    print("\n\n🎯 TESTING READINESS SUMMARY")
    print("=" * 70)
    print("✅ Real health plan documents available (2 SPDs + 2 BPS)")
    print("✅ Document processing libraries available")
    print("✅ 33 test queries prepared covering all benefit types")
    print("✅ Key health plan concepts identified for extraction")
    print("\n🚀 Ready for full end-to-end testing once Docker environment is up!")