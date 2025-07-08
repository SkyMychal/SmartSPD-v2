import { NextRequest, NextResponse } from 'next/server';

// Simple test route for now while we fix Auth0 compatibility
export async function GET(req: NextRequest, { params }: { params: Promise<{ auth0: string }> }) {
  const { auth0 } = await params;
  
  if (auth0 === 'login') {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }
  
  if (auth0 === 'logout') {
    return NextResponse.redirect(new URL('/', req.url));
  }
  
  if (auth0 === 'me') {
    return NextResponse.json({
      sub: 'test-user-123',
      name: 'Test Admin User',
      email: 'admin@test.com',
      'https://smartspd.com/role': 'tpa_admin'
    });
  }
  
  return NextResponse.json({ message: `Auth endpoint: ${auth0}` });
}

export const POST = GET;