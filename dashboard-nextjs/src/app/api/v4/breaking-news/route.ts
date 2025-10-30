import { NextResponse } from 'next/server'

export async function GET() {
  // TEMPORARILY DISABLED - Returning empty array to prevent site breakage
  // API needs table schema fix before re-enabling
  return NextResponse.json({ 
    news: [],
    message: "Breaking news temporarily unavailable"
  });
}
