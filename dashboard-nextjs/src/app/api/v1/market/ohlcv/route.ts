import { NextResponse } from 'next/server'
import { spawn } from 'node:child_process'
import { join } from 'node:path'
import { existsSync } from 'node:fs'

export const dynamic = 'force-dynamic'

function resolveScriptPath(): string {
  const candidates = [
    'scripts/api/databento_ohlcv_range.py',
    '../scripts/api/databento_ohlcv_range.py',
    '../../scripts/api/databento_ohlcv_range.py',
  ].map((p) => join(process.cwd(), p))
  for (const p of candidates) {
    if (existsSync(p)) return p
  }
  return 'scripts/api/databento_ohlcv_range.py'
}

function runPython(params: { root: string; tf?: string; minutes?: number; hours?: number; days?: number; frontOnly?: boolean }): Promise<any> {
  return new Promise((resolve) => {
    const env = { ...process.env }
    if (!env.DATABENTO_API_KEY) {
      return resolve({ ok: false, error: 'missing_api_key' })
    }

    const script = resolveScriptPath()
    const args: string[] = [script, '--root', params.root]
    if (params.tf) args.push('--tf', params.tf)
    if (params.minutes) args.push('--minutes', String(params.minutes))
    if (params.hours) args.push('--hours', String(params.hours))
    if (params.days) args.push('--days', String(params.days))
    if (params.frontOnly) args.push('--front-only')

    const proc = spawn('python3', args, { env })
    let stdout = ''
    let stderr = ''
    proc.stdout.on('data', (d) => (stdout += d.toString()))
    proc.stderr.on('data', (d) => (stderr += d.toString()))
    proc.on('error', () => resolve({ ok: false, error: 'spawn_error' }))
    proc.on('close', () => {
      try {
        const parsed = JSON.parse(stdout || '{}')
        resolve(parsed)
      } catch (e: any) {
        resolve({ ok: false, error: 'invalid_python_output', detail: stderr || String(e) })
      }
    })
  })
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const root = (searchParams.get('root') || '').toUpperCase().trim()
    const tf = (searchParams.get('tf') || '1m').trim()
    const minutes = searchParams.get('minutes') ? parseInt(String(searchParams.get('minutes')), 10) : undefined
    const hours = searchParams.get('hours') ? parseInt(String(searchParams.get('hours')), 10) : undefined
    const days = searchParams.get('days') ? parseInt(String(searchParams.get('days')), 10) : undefined
    const frontOnly = ['1', 'true', 'yes'].includes((searchParams.get('frontOnly') || '').toLowerCase())

    if (!root || !/^[A-Z]{1,5}$/.test(root)) {
      return NextResponse.json({ ok: false, error: 'invalid_root' }, { status: 400 })
    }
    if (!['1m', '1h', '1d'].includes(tf)) {
      return NextResponse.json({ ok: false, error: 'invalid_tf' }, { status: 400 })
    }
    if (!process.env.DATABENTO_API_KEY) {
      return NextResponse.json({ ok: false, error: 'missing_api_key' }, { status: 500 })
    }

    const result = await runPython({ root, tf, minutes, hours, days, frontOnly })
    if (!result?.ok) {
      return NextResponse.json(result || { ok: false, error: 'unknown_error' }, { status: 500 })
    }

    // Add gentle caching to reduce calls while staying fresh (override in client with cache: 'no-store' if needed)
    const res = NextResponse.json(result)
    res.headers.set('Cache-Control', 'private, max-age=10')
    return res
  } catch (error: any) {
    return NextResponse.json({ ok: false, error: error?.message || 'internal_error' }, { status: 500 })
  }
}

