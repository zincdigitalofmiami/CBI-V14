import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  // SHAP endpoint intentionally disabled until wired to REAL BigQuery table.
  // No mock / random data is allowed in production.
  return NextResponse.json(
    {
      success: false,
      error: 'SHAP endpoint disabled: no fake data. Wire to real BigQuery SHAP table before enabling.',
    },
    { status: 501 }
  );
}

