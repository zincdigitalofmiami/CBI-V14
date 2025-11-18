import { NextResponse } from 'next/server'
import { spawn } from 'node:child_process'
import { join } from 'node:path'
import { existsSync } from 'node:fs'

// Minimal API: GET /api/v1/market/latest-1m?root=ES[&minutes=60]
// Server-only: requires process.env.DATABENTO_API_KEY set on server runtime

export const dynamic = 'force-dynamic'

function resolveScriptPath(): string {
  const candidates = [
    'scripts/api/databento_latest_1m.py',
    '../scripts/api/databento_latest_1m.py',
    '../../scripts/api/databento_latest_1m.py',
  ].map((p) => join(process.cwd(), p))
  for (const p of candidates) {
    if (existsSync(p)) return p
  }
  // Fallback to bare relative path (may work depending on cwd)
  return 'scripts/api/databento_latest_1m.py'
}

function runPython(root: string, minutes?: number): Promise<any> {
  return new Promise((resolve, reject) => {
    const env = { ...process.env }
    if (!env.DATABENTO_API_KEY) {
      return resolve({ ok: false, error: 'missing_api_key' })
    }

    const script = resolveScriptPath()
    const args = [script, '--root', root]
    if (minutes && Number.isFinite(minutes)) {
      args.push('--minutes', String(minutes))
    }

    const proc = spawn('python3', args, { env })
    let stdout = ''
    let stderr = ''
    proc.stdout.on('data', (d) => (stdout += d.toString()))
    proc.stderr.on('data', (d) => (stderr += d.toString()))
    proc.on('error', (err) => reject(err))
    proc.on('close', (_code) => {
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
    const minutes = searchParams.get('minutes')
      ? parseInt(searchParams.get('minutes') as string, 10)
      : undefined

    if (!root || !/^[A-Z]{1,5}$/.test(root)) {
      return NextResponse.json(
        { ok: false, error: 'invalid_root', hint: 'Use roots like ES, MES, ZL' },
        { status: 400 }
      )
    }

    if (!process.env.DATABENTO_API_KEY) {
      return NextResponse.json(
        { ok: false, error: 'missing_api_key', hint: 'Set DATABENTO_API_KEY on the server' },
        { status: 500 }
      )
    }

    const result = await runPython(root, minutes)
    if (!result?.ok) {
      return NextResponse.json(result || { ok: false, error: 'unknown_error' }, { status: 500 })
    }
    return NextResponse.json(result)
  } catch (error: any) {
    return NextResponse.json(
      { ok: false, error: error?.message || 'internal_error' },
      { status: 500 }
    )
  }
}
