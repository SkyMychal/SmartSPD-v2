import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  // Redirect to a login page instead of directly to dashboard
  return NextResponse.redirect(new URL('/login', req.url));
}