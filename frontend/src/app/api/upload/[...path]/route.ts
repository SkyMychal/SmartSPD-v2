import { NextRequest, NextResponse } from 'next/server';

// Special handler for upload endpoints
export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  try {
    const { path } = await params;
    const backendUrl = `http://localhost:8000/api/v1/upload/${path.join('/')}`;
    
    // Forward the request as-is to preserve form data
    const response = await fetch(backendUrl, {
      method: 'POST',
      body: req.body,
      headers: {
        // Forward all headers except those that can cause issues
        ...Object.fromEntries(
          [...req.headers.entries()].filter(([key]) => 
            !['host', 'connection', 'content-length'].includes(key.toLowerCase())
          )
        ),
      },
      duplex: 'half' as const,
    });

    const responseText = await response.text();
    
    return new NextResponse(responseText, {
      status: response.status,
      headers: response.headers,
    });

  } catch (error) {
    console.error('Upload proxy error:', error);
    return NextResponse.json(
      { error: 'Upload service unavailable', details: error.message },
      { status: 503 }
    );
  }
}