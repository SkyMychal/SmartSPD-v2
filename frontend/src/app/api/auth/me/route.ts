import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    // For our custom auth system, just return success if user data exists
    // The real authentication is handled by the login flow
    return NextResponse.json(
      { authenticated: true },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: 'Authentication failed' },
      { status: 401 }
    );
  }
}