import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path, 'GET');
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path, 'POST');
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path, 'PUT');
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(req, path, 'DELETE');
}

async function proxyRequest(req: NextRequest, path: string[], method: string) {
  try {
    // Determine backend URL based on environment
    let backendUrl: string;
    
    if (process.env.NODE_ENV === 'production') {
      // Production: use internal Docker service name
      backendUrl = `http://backend:8000/api/v1/${path.join('/')}/`;
    } else if (process.env.CODESPACE_NAME) {
      // GitHub Codespace: use internal localhost (frontend runs in same environment)
      backendUrl = `http://localhost:8000/api/v1/${path.join('/')}/`;
    } else {
      // Local development: use localhost
      backendUrl = `http://localhost:8000/api/v1/${path.join('/')}/`;
    }
    
    const url = new URL(req.url);
    const searchParams = url.searchParams.toString();
    const finalUrl = searchParams ? `${backendUrl}?${searchParams}` : backendUrl;
    
    console.log(`Proxying ${method} request to: ${finalUrl}`);

    // Get headers from the request
    const headers: Record<string, string> = {};
    const contentType = req.headers.get('content-type');
    req.headers.forEach((value, key) => {
      // Don't forward certain headers that can cause issues
      const lowerKey = key.toLowerCase();
      if (!['host', 'connection', 'transfer-encoding', 'content-length'].includes(lowerKey)) {
        // For multipart/form-data, don't forward content-type - let fetch set it with boundary
        if (contentType?.includes('multipart/form-data') && lowerKey === 'content-type') {
          return;
        }
        headers[key] = value;
      }
    });

    // Get body for POST/PUT requests
    let body = undefined;
    if (['POST', 'PUT'].includes(method)) {
      const contentType = req.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        try {
          body = JSON.stringify(await req.json());
        } catch (error) {
          // If JSON parsing fails, try as text
          body = await req.text();
        }
      } else if (contentType?.includes('multipart/form-data')) {
        // For file uploads, use the formData directly
        body = await req.formData();
      } else {
        body = await req.text();
      }
    }

    const fetchOptions: RequestInit = {
      method,
      headers,
    };

    // Only add body if it exists
    if (body) {
      fetchOptions.body = body;
    }

    const response = await fetch(finalUrl, fetchOptions);

    // Get the response data
    const responseData = await response.text();
    let jsonData;
    
    try {
      jsonData = JSON.parse(responseData);
    } catch (error) {
      jsonData = responseData;
    }
    
    // Create the response with proper headers
    const nextResponse = NextResponse.json(jsonData, {
      status: response.status,
      statusText: response.statusText,
    });

    return nextResponse;

  } catch (error) {
    console.error('Proxy error:', error);
    console.error('Backend URL was:', finalUrl);
    return NextResponse.json(
      { error: 'Backend service unavailable', details: error.message },
      { status: 503 }
    );
  }
}