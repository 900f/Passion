// app/api/stripe/prices/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth'
import Stripe from 'stripe'

// GET — list active prices with their products
export async function GET() {
  const session = await getSession()
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2026-02-25.clover',
  })

  const prices = await stripe.prices.list({ active: true, expand: ['data.product'], limit: 50 })

  const result = prices.data.map(p => {
    const product = p.product as Stripe.Product
    return {
      id:          p.id,
      amount:      p.unit_amount,
      currency:    p.currency,
      recurring:   p.recurring,
      productId:   product.id,
      productName: product.name,
      productDesc: product.description,
      active:      p.active && product.active,
    }
  })

  return NextResponse.json(result)
}