import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ 
    message: 'Auth test endpoint working',
    env: {
      AUTH0_BASE_URL: process.env.AUTH0_BASE_URL,
      AUTH0_ISSUER_BASE_URL: process.env.AUTH0_ISSUER_BASE_URL,
      AUTH0_CLIENT_ID: process.env.AUTH0_CLIENT_ID,
      hasSecret: !!process.env.AUTH0_SECRET,
      hasClientSecret: !!process.env.AUTH0_CLIENT_SECRET
    }
  });
}