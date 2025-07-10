import { NextRequest, NextResponse } from 'next/server'
import { requireAdmin } from '@/lib/auth'
import { getGameSettings, updateGameSettings } from '@/lib/database'

export const runtime = 'nodejs'

export async function GET() {
  try {
    const settings = await getGameSettings()
    return NextResponse.json(settings)
  } catch (error) {
    console.error('Get settings error:', error)
    return NextResponse.json({ error: 'Failed to get settings' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    await requireAdmin(request)
    const { entry_fee, buyback_multiplier } = await request.json()
    
    const updates: any = {}
    if (entry_fee !== undefined) updates.entry_fee = entry_fee
    if (buyback_multiplier !== undefined) updates.buyback_multiplier = buyback_multiplier
    
    const settings = await updateGameSettings(updates)
    return NextResponse.json(settings)
  } catch (error) {
    console.error('Update settings error:', error)
    return NextResponse.json({ error: 'Failed to update settings' }, { status: 500 })
  }
}
