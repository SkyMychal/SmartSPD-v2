import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();
    
    // Direct connection to backend (server-side call within Docker network)
    const backendUrl = 'http://backend:8000';
    console.log('Using backend URL:', backendUrl);
    const response = await fetch(`${backendUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { message: errorData.detail || 'Login failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Return the token and user data
    return NextResponse.json({
      token: data.access_token,
      user: data.user,
      expires_in: data.expires_in,
    });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }
}