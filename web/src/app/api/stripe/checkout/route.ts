import { NextResponse } from 'next/server'

/**
 * POST /api/stripe/checkout
 * Stripe checkout placeholder - TODO: Implement
 */
export async function POST() {
  return NextResponse.json(
    { error: 'Not implemented', todo: 'Stripe checkout integration pending' },
    { status: 501 }
  )
}

