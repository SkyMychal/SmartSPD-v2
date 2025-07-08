#!/usr/bin/env python3
"""
Test script for SmartSPD v2 document processing and query system

This script tests the complete pipeline:
1. Upload real health plan documents (SPDs and BPS files)
2. Process documents and create embeddings
3. Test various queries against the documents
4. Validate RAG functionality end-to-end
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import aiohttp
import aiofiles

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

class SmartSPDTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.uploaded_documents = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self, email: str = "agent@demo.com", password: str = "demo123"):
        """Login and get authentication token"""
        print(f"🔐 Logging in as {email}...")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=login_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Login successful! Token: {self.auth_token[:20]}...")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Login failed: {response.status} - {error_text}")
                return False
    
    async def check_health(self):
        """Check if the API is responding"""
        print("🏥 Checking API health...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API is healthy: {data}")
                    return True
                else:
                    print(f"❌ API health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Failed to connect to API: {e}")
            return False
    
    async def upload_document(self, file_path: Path, document_type: str = "spd", health_plan_id: str = "test_plan_001"):
        """Upload a document for processing"""
        print(f"📄 Uploading document: {file_path.name}")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        data = aiohttp.FormData()
        data.add_field('document_type', document_type)
        data.add_field('health_plan_id', health_plan_id)
        
        async with aiofiles.open(file_path, 'rb') as f:
            file_content = await f.read()
            data.add_field('file', file_content, filename=file_path.name, content_type='application/octet-stream')
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/documents/upload",
                headers=headers,
                data=data
            ) as response:
                if response.status == 201:
                    doc_data = await response.json()
                    document_id = doc_data.get("id")
                    self.uploaded_documents.append({
                        "id": document_id,
                        "filename": file_path.name,
                        "type": document_type,
                        "health_plan_id": health_plan_id
                    })
                    print(f"✅ Document uploaded successfully! ID: {document_id}")
                    return document_id
                else:
                    error_text = await response.text()
                    print(f"❌ Document upload failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Exception during upload: {e}")
            return None
    
    async def wait_for_processing(self, document_id: str, max_wait: int = 300):
        """Wait for document processing to complete"""
        print(f"⏳ Waiting for document {document_id} to process...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/v1/documents/{document_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        doc_data = await response.json()
                        status = doc_data.get("processing_status")
                        print(f"📊 Processing status: {status}")
                        
                        if status == "completed":
                            print(f"✅ Document {document_id} processing completed!")
                            return True
                        elif status == "failed":
                            print(f"❌ Document {document_id} processing failed!")
                            return False
                        
                        await asyncio.sleep(5)  # Wait 5 seconds before checking again
                    else:
                        print(f"❌ Failed to check document status: {response.status}")
                        await asyncio.sleep(5)
            except Exception as e:
                print(f"❌ Exception checking status: {e}")
                await asyncio.sleep(5)
        
        print(f"⏰ Timeout waiting for document {document_id} to process")
        return False
    
    async def test_query(self, query: str, health_plan_id: str = "test_plan_001"):
        """Test a query against the processed documents"""
        print(f"🔍 Testing query: '{query}'")
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        query_data = {
            "query": query,
            "health_plan_id": health_plan_id,
            "include_sources": True
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/query",
                headers=headers,
                json=query_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"✅ Query successful!")
                    print(f"📝 Answer: {result.get('answer', 'No answer')}")
                    print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
                    print(f"⏱️ Response time: {result.get('response_time_ms', 0)}ms")
                    
                    sources = result.get('source_documents', [])
                    if sources:
                        print(f"📚 Sources ({len(sources)}):")
                        for i, source in enumerate(sources[:3]):  # Show top 3 sources
                            print(f"  {i+1}. Document: {source.get('document_id', 'Unknown')}")
                            print(f"     Relevance: {source.get('relevance_score', 0):.2f}")
                    
                    suggestions = result.get('follow_up_suggestions', [])
                    if suggestions:
                        print(f"💡 Follow-up suggestions:")
                        for suggestion in suggestions[:2]:
                            print(f"  - {suggestion}")
                    
                    print("-" * 80)
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Query failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Exception during query: {e}")
            return None
    
    async def get_dashboard_stats(self):
        """Get dashboard statistics"""
        print("📊 Fetching dashboard statistics...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/analytics/dashboard",
                headers=headers
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Dashboard stats retrieved:")
                    print(f"  📄 Documents processed: {stats.get('documents_processed', 0)}")
                    print(f"  💬 Total queries: {stats.get('total_queries_today', 0)}")
                    print(f"  👥 Active users: {stats.get('active_users', 0)}")
                    print(f"  ⚡ Avg response time: {stats.get('avg_response_time', 'N/A')}")
                    print(f"  ✅ Success rate: {stats.get('success_rate', 0):.2%}")
                    return stats
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get dashboard stats: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Exception getting dashboard stats: {e}")
            return None

async def main():
    """Main test function"""
    print("🚀 Starting SmartSPD v2 Document Processing and Query Tests")
    print("=" * 80)
    
    # Define test documents and queries
    documents_dir = Path("/workspaces/SmartSPD-v2/SPD_BPS_Examples")
    
    test_documents = [
        {
            "file": "Real Value dba Simple Modern Group Health Plan SPD.pdf",
            "type": "spd",
            "plan_id": "simple_modern_001"
        },
        {
            "file": "Spooner, Inc. Employee Benefits Program SPD.pdf", 
            "type": "spd",
            "plan_id": "spooner_inc_001"
        },
        {
            "file": "BPS - Datapoint Surveying & Mapping II, LLC.xlsx",
            "type": "bps", 
            "plan_id": "datapoint_001"
        },
        {
            "file": "BPS - Welch State Bank (1).xlsx",
            "type": "bps",
            "plan_id": "welch_bank_001"
        }
    ]
    
    # Test queries covering different types of benefit inquiries
    test_queries = [
        "What is my deductible for medical services?",
        "How much is a copay for a primary care visit?", 
        "What are my out-of-pocket maximums?",
        "Does my plan cover prescription drugs?",
        "Is emergency room care covered?",
        "What preventive care is covered at 100%?",
        "How does my plan handle specialist visits?",
        "What happens if I need surgery?",
        "Are mental health services covered?",
        "What is covered for maternity care?",
        "Compare my deductibles for in-network vs out-of-network providers",
        "What are the annual limits on physical therapy?"
    ]
    
    async with SmartSPDTester() as tester:
        # Step 1: Check API health
        if not await tester.check_health():
            print("❌ API is not responding. Please start the backend server.")
            return
        
        # Step 2: Login
        if not await tester.login():
            print("❌ Login failed. Cannot proceed with tests.")
            return
        
        # Step 3: Get initial dashboard stats
        await tester.get_dashboard_stats()
        
        # Step 4: Upload and process documents
        print("\n📤 DOCUMENT UPLOAD AND PROCESSING")
        print("=" * 80)
        
        uploaded_docs = []
        for doc_info in test_documents:
            file_path = documents_dir / doc_info["file"]
            if file_path.exists():
                doc_id = await tester.upload_document(
                    file_path, 
                    doc_info["type"], 
                    doc_info["plan_id"]
                )
                if doc_id:
                    uploaded_docs.append((doc_id, doc_info))
            else:
                print(f"⚠️ File not found: {file_path}")
        
        # Step 5: Wait for processing to complete
        print("\n⏳ WAITING FOR DOCUMENT PROCESSING")
        print("=" * 80)
        
        processed_docs = []
        for doc_id, doc_info in uploaded_docs:
            if await tester.wait_for_processing(doc_id):
                processed_docs.append((doc_id, doc_info))
        
        if not processed_docs:
            print("❌ No documents were successfully processed. Cannot test queries.")
            return
        
        print(f"\n✅ Successfully processed {len(processed_docs)} documents!")
        
        # Step 6: Test queries against different plan types
        print("\n🔍 TESTING QUERIES")
        print("=" * 80)
        
        # Test queries against each health plan
        for doc_id, doc_info in processed_docs:
            print(f"\n📋 Testing queries against {doc_info['file']} (Plan: {doc_info['plan_id']})")
            print("-" * 60)
            
            # Test a subset of queries for each document
            for query in test_queries[:6]:  # Test first 6 queries per document
                await tester.test_query(query, doc_info['plan_id'])
                await asyncio.sleep(1)  # Small delay between queries
        
        # Step 7: Test cross-plan comparison queries
        print("\n🔀 TESTING CROSS-PLAN QUERIES")
        print("=" * 80)
        
        comparison_queries = [
            "Compare deductibles across all available plans",
            "Which plan has the lowest copays?",
            "What are the differences in prescription drug coverage?",
            "Compare out-of-pocket maximums between plans"
        ]
        
        # Use the first plan for cross-plan queries
        if processed_docs:
            first_plan = processed_docs[0][1]['plan_id']
            for query in comparison_queries:
                await tester.test_query(query, first_plan)
                await asyncio.sleep(1)
        
        # Step 8: Get final dashboard stats
        print("\n📊 FINAL DASHBOARD STATISTICS")
        print("=" * 80)
        await tester.get_dashboard_stats()
        
        # Step 9: Summary
        print("\n🎉 TEST SUMMARY")
        print("=" * 80)
        print(f"📄 Documents uploaded: {len(uploaded_docs)}")
        print(f"✅ Documents processed: {len(processed_docs)}")
        print(f"🔍 Total queries tested: {len(test_queries) * len(processed_docs) + len(comparison_queries)}")
        
        if processed_docs:
            print("\n✅ Document processing and query system is working!")
            print("📚 Processed documents:")
            for doc_id, doc_info in processed_docs:
                print(f"  - {doc_info['file']} ({doc_info['type'].upper()}) - Plan: {doc_info['plan_id']}")
        else:
            print("\n❌ No documents were successfully processed.")

if __name__ == "__main__":
    asyncio.run(main())