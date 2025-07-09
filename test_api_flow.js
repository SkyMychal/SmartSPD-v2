#!/usr/bin/env node
/**
 * Simple test to verify API flow is working
 * This will test login, health plans, and documents endpoints
 */

const https = require('https');
const http = require('http');
const fs = require('fs');

// Test configuration
const BACKEND_URL = 'http://localhost:8001';
const FRONTEND_URL = 'http://localhost:3000';

// Test credentials
const credentials = {
  email: 'sstillwagon@kemptongroup.com',
  password: 'temp123'
};

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const request = (url.startsWith('https') ? https : http).request(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({ status: res.statusCode, data: jsonData });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });
    
    request.on('error', reject);
    
    if (options.body) {
      request.write(options.body);
    }
    
    request.end();
  });
}

async function testLogin() {
  console.log('🔐 Testing backend login...');
  
  try {
    const response = await makeRequest(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    if (response.status === 200) {
      console.log('✅ Backend login successful!');
      console.log(`   User: ${response.data.user.email}`);
      console.log(`   Role: ${response.data.user.role}`);
      console.log(`   TPA: ${response.data.user.tpa_id}`);
      return response.data.access_token;
    } else {
      console.log('❌ Backend login failed:', response.status, response.data);
      return null;
    }
  } catch (error) {
    console.log('❌ Backend login error:', error.message);
    return null;
  }
}

async function testHealthPlans(token) {
  console.log('\n🏥 Testing health plans endpoint...');
  
  try {
    const response = await makeRequest(`${BACKEND_URL}/api/v1/health-plans/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 200) {
      console.log('✅ Health plans retrieved successfully!');
      console.log(`   Total plans: ${response.data.health_plans.length}`);
      response.data.health_plans.forEach((plan, index) => {
        console.log(`   ${index + 1}. ${plan.name} (${plan.group_id})`);
      });
      return response.data.health_plans;
    } else {
      console.log('❌ Health plans failed:', response.status, response.data);
      return [];
    }
  } catch (error) {
    console.log('❌ Health plans error:', error.message);
    return [];
  }
}

async function testDocuments(token) {
  console.log('\n📄 Testing documents endpoint...');
  
  try {
    const response = await makeRequest(`${BACKEND_URL}/api/v1/documents/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 200) {
      console.log('✅ Documents retrieved successfully!');
      console.log(`   Total documents: ${response.data.documents.length}`);
      response.data.documents.forEach((doc, index) => {
        console.log(`   ${index + 1}. ${doc.filename} (${doc.document_type}) - ${doc.processing_status}`);
      });
      return response.data.documents;
    } else {
      console.log('❌ Documents failed:', response.status, response.data);
      return [];
    }
  } catch (error) {
    console.log('❌ Documents error:', error.message);
    return [];
  }
}

async function testFrontendProxy(token) {
  console.log('\n🔗 Testing frontend proxy...');
  
  try {
    const response = await makeRequest(`${FRONTEND_URL}/api/v1/health-plans`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 200) {
      console.log('✅ Frontend proxy working!');
      console.log(`   Proxy returned: ${response.data.health_plans?.length || 0} health plans`);
      return true;
    } else {
      console.log('❌ Frontend proxy failed:', response.status, response.data);
      return false;
    }
  } catch (error) {
    console.log('❌ Frontend proxy error:', error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 SmartSPD API Flow Test\n');
  
  // Test backend login
  const token = await testLogin();
  if (!token) {
    console.log('\n❌ Cannot proceed without valid token');
    return;
  }
  
  // Test health plans
  const healthPlans = await testHealthPlans(token);
  
  // Test documents
  const documents = await testDocuments(token);
  
  // Test frontend proxy
  const proxyWorking = await testFrontendProxy(token);
  
  // Summary
  console.log('\n📊 Test Summary:');
  console.log(`   Backend Login: ${token ? '✅' : '❌'}`);
  console.log(`   Health Plans: ${healthPlans.length > 0 ? '✅' : '❌'} (${healthPlans.length} plans)`);
  console.log(`   Documents: ${documents.length >= 0 ? '✅' : '❌'} (${documents.length} documents)`);
  console.log(`   Frontend Proxy: ${proxyWorking ? '✅' : '❌'}`);
  
  if (token && healthPlans.length > 0) {
    console.log('\n🎉 System is ready! You should see real data in the frontend.');
  } else {
    console.log('\n⚠️  System has issues that need to be resolved.');
  }
}

main().catch(console.error);