import { NextResponse } from "next/server";
import { getBigQueryClient } from "@/lib/bigquery";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ horizon: string }> }
) {
  const resolvedParams = await params;
  const h = (resolvedParams.horizon || "").toUpperCase();
  
  if (!["1W", "1M", "3M", "6M"].includes(h)) {
    return NextResponse.json(
      { error: "Invalid horizon. Must be 1w, 1m, 3m, or 6m" },
      { status: 400 }
    );
  }

  try {
    // Use the latest view for efficient querying
    const query = `
      SELECT 
        feature,
        importance_abs as importance,
        raw_contribution,
        prediction_date,
        model_id
      FROM \`cbi-v14.predictions_uc1.vw_feature_importance_latest\`
      WHERE horizon = @h
      QUALIFY ROW_NUMBER() OVER(ORDER BY importance_abs DESC) <= 25
      ORDER BY importance_abs DESC
    `;

    const client = getBigQueryClient();
    const [rows] = await client.query({
      query,
      location: "us-central1",
      params: { h },
    });

    return NextResponse.json({ horizon: h, rows: rows || [] });
  } catch (error: any) {
    console.error("Feature importance error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to fetch feature importance" },
      { status: 500 }
    );
  }
}

