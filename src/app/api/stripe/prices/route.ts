// app/api/stripe/prices/route.ts

import { NextResponse } from 'next/server'
import Stripe from 'stripe'

// Public route — no auth needed, customers need to see prices
export async function GET() {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2026-02-25.clover',
  })

  const prices = await stripe.prices.list({
    active: true,
    expand: ['data.product'],
    limit: 50,
  })

  const result = prices.data
    .filter(p => {
      const product = p.product as Stripe.Product
      // Filter out archived/inactive products
      return p.active && product.active && !product.deleted
    })
    .map(p => {
      const product = p.product as Stripe.Product
      return {
        id:          p.id,
        amount:      p.unit_amount,
        currency:    p.currency,
        recurring:   p.recurring,
        productId:   product.id,
        productName: product.name,
        productDesc: product.description,
        active:      true,
      }
    })

  return NextResponse.json(result)
}