import { NextResponse } from 'next/server'

/**
 * POST /api/stripe/webhook
 * Stripe webhook placeholder - TODO: Implement
 */
export async function POST() {
  return NextResponse.json(
    { error: 'Not implemented', todo: 'Stripe webhook integration pending' },
    { status: 501 }
  )
}

