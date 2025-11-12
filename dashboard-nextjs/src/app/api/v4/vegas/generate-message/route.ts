import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const { opportunity } = await request.json()
    
    // FREE TEMPLATE-BASED MESSAGE GENERATION (No OpenAI required)
    // Professional, context-aware message using template system
    
    const message = generateTemplateMessage(opportunity)
    
    return NextResponse.json({ message })
  } catch (error: any) {
    console.error('Message generation error:', error)
    return NextResponse.json(
      { error: 'Failed to generate message' },
      { status: 500 }
    )
  }
}

function generateTemplateMessage(opportunity: any): string {
  const {
    venue_name,
    event_name,
    event_date,
    expected_attendance,
    oil_demand_surge_gal,
    revenue_opportunity,
    distance_km,
  } = opportunity
  
  const eventDate = new Date(event_date)
  const formattedDate = eventDate.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
  
  // Generate personalized message based on event type and impact
  const eventType = event_name.toLowerCase()
  
  let opening = ''
  let context = ''
  let action = ''
  
  // Context-aware opening
  if (eventType.includes('formula 1') || eventType.includes('f1')) {
    opening = `Hi ${venue_name} team,`
    context = `With the Formula 1 Grand Prix coming up on ${formattedDate}, we're seeing unprecedented demand across the Strip. Your location ${distance_km < 1 ? 'is right in the action zone' : `is ${distance_km.toFixed(1)}km from the event`}, and we're forecasting a ${oil_demand_surge_gal}-gallon surge in oil demand.`
  } else if (eventType.includes('raiders') || eventType.includes('golden knights')) {
    opening = `Hi ${venue_name},`
    context = `Game day is approaching (${formattedDate}), and with ${expected_attendance?.toLocaleString() || 'thousands of'} fans heading to the venue, we anticipate a ${oil_demand_surge_gal}-gallon increase in your oil needs.`
  } else if (eventType.includes('ces') || eventType.includes('convention')) {
    opening = `Hi ${venue_name},`
    context = `The ${event_name} (${formattedDate}) will bring ${expected_attendance?.toLocaleString() || 'over 100,000'} attendees to Las Vegas. Given your proximity to the convention center, we're projecting a ${oil_demand_surge_gal}-gallon surge during the event.`
  } else {
    opening = `Hi ${venue_name},`
    context = `With the upcoming ${event_name} on ${formattedDate}, we're forecasting a ${oil_demand_surge_gal}-gallon increase in oil demand at your location.`
  }
  
  // Call to action
  const deliveryDate = new Date(eventDate)
  deliveryDate.setDate(deliveryDate.getDate() - 7)
  const deliveryDateStr = deliveryDate.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
  })
  
  action = `We'd like to schedule a proactive delivery around ${deliveryDateStr} to ensure you're fully stocked. This represents approximately $${revenue_opportunity?.toLocaleString() || '0'} in incremental revenue opportunity for us both.`
  
  const closing = `Can we schedule a brief call this week to discuss?\n\nBest regards,\nUS Oil Solutions Team`
  
  return `${opening}\n\n${context}\n\n${action}\n\n${closing}`
}







