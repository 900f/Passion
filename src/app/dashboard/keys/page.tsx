// app/dashboard/keys/page.tsx

'use client'
import { useState, useEffect, useCallback } from 'react'

type Key = {
  id: number
  key_value: string
  label: string | null
  status: string
  hwid: string | null
  uses: number
  max_uses: number | null
  expires_at: string | null
  duration_days: number | null
  created_at: string
  last_used: string | null
}

const STATUS_COLORS: Record<string, string> = {
  active:   '#16a34a',
  disabled: '#dc2625',
  expired:  '#5d585c',
}

function Badge({ status }: { status: string }) {
  return (
    <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide"
          style={{
            background: STATUS_COLORS[status] + '22',
            color: STATUS_COLORS[status],
            border: `1px solid ${STATUS_COLORS[status]}55`,
          }}>
      {status}
    </span>
  )
}

function DurationBadge({ duration_days }: { duration_days: number | null }) {
  const map: Record<number, { label: string; color: string }> = {
    1:  { label: 'Daily',   color: '#c97c30' },
    7:  { label: 'Weekly',  color: '#7060a8' },
    30: { label: 'Monthly', color: '#4090c8' },
  }
  const info  = duration_days !== null ? map[duration_days] : null
  const label = info?.label ?? (duration_days === null ? 'Lifetime' : `${duration_days}d`)
  const color = info?.color ?? (duration_days === null ? '#16a34a' : '#868283')

  return (
    <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide"
          style={{ background: color + '22', color, border: `1px solid ${color}55` }}>
      {label}
    </span>
  )
}

function fmt(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleString()
}

function fmtExpiry(expires_at: string | null, duration_days: number | null) {
  if (duration_days === null) return <span style={{ color: '#16a34a' }}>Never</span>
  if (!expires_at) return <span style={{ color: '#5d585c' }}>On activation</span>
  return <span style={{ color: '#868283' }}>{fmt(expires_at)}</span>
}

const DURATION_OPTIONS = [
  { label: 'Lifetime',      value: ''   },
  { label: 'Daily (1 day)', value: '1'  },
  { label: 'Weekly (7 days)', value: '7' },
  { label: 'Monthly (30 days)', value: '30' },
]

export default function KeysPage() {
  const [keys, setKeys]         = useState<Key[]>([])
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState('')
  const [filter, setFilter]     = useState('')
  const [showCreate, setCreate] = useState(false)
  const [copied, setCopied]     = useState<number | null>(null)
  const [newKey, setNewKey]     = useState<Key | null>(null)

  // Create form
  const [label, setLabel]           = useState('')
  const [maxUses, setMaxUses]       = useState('')
  const [durationDays, setDuration] = useState('')
  const [creating, setCreating]     = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const p = new URLSearchParams()
    if (search) p.set('q', search)
    if (filter) p.set('status', filter)
    const r = await fetch('/api/keys?' + p)
    setKeys(await r.json())
    setLoading(false)
  }, [search, filter])

  useEffect(() => { load() }, [load])

  async function createKey() {
    setCreating(true)
    const body: Record<string, unknown> = {}
    if (label)        body.label         = label
    if (maxUses)      body.max_uses      = Number(maxUses)
    if (durationDays) body.duration_days = Number(durationDays)
    const r = await fetch('/api/keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const k = await r.json()
    setCreating(false)
    setNewKey(k)
    setCreate(false)
    setLabel(''); setMaxUses(''); setDuration('')
    load()
  }

  async function deleteKey(id: number) {
    if (!confirm('Delete this key permanently?')) return
    await fetch(`/api/keys/${id}`, { method: 'DELETE' })
    load()
  }

  async function toggleStatus(k: Key) {
    const next = k.status === 'active' ? 'disabled' : 'active'
    await fetch(`/api/keys/${k.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: next }),
    })
    load()
  }

  async function resetHwid(id: number) {
    await fetch(`/api/keys/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reset_hwid: true }),
    })
    load()
  }

  function copy(id: number, val: string) {
    navigator.clipboard.writeText(val)
    setCopied(id)
    setTimeout(() => setCopied(null), 1500)
  }

  const inputCls   = 'h-[38px] rounded-[7px] px-3 text-[13px] outline-none transition-colors'
  const inputStyle = { background: '#2a2024', border: '1px solid #352c2f', color: '#c5c0c2' }
  const selectStyle = { ...inputStyle, colorScheme: 'dark' }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#e5e3e4' }}>License Keys</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#5d585c' }}>{keys.length} keys</p>
        </div>
        <button
          onClick={() => setCreate(true)}
          className="h-[38px] px-4 rounded-[8px] text-[13px] font-semibold text-white"
          style={{ background: '#dc2625', boxShadow: '0 0 14px rgba(220,38,37,0.35)' }}
          onMouseEnter={e => (e.currentTarget.style.background = '#e42d2c')}
          onMouseLeave={e => (e.currentTarget.style.background = '#dc2625')}>
          + Create Key
        </button>
      </div>

      {/* New key banner */}
      {newKey && (
        <div className="mb-4 p-4 rounded-[10px] flex items-center justify-between"
             style={{ background: '#16a34a18', border: '1px solid #16a34a44' }}>
          <div>
            <p className="text-[12px] mb-1" style={{ color: '#16a34a' }}>Key created successfully</p>
            <code className="text-[13px] font-mono mr-3" style={{ color: '#e5e3e4' }}>{newKey.key_value}</code>
            <DurationBadge duration_days={newKey.duration_days} />
          </div>
          <div className="flex gap-2">
            <button onClick={() => copy(-1, newKey.key_value)}
                    className="px-3 py-1.5 rounded-[6px] text-[12px]"
                    style={{ background: '#16a34a33', color: '#16a34a' }}>
              {copied === -1 ? 'Copied!' : 'Copy'}
            </button>
            <button onClick={() => setNewKey(null)} style={{ color: '#5d585c' }}>✕</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <input
          placeholder="Search keys or labels…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className={inputCls + ' flex-1 max-w-xs'}
          style={inputStyle}
        />
        <select value={filter} onChange={e => setFilter(e.target.value)}
                className={inputCls} style={selectStyle}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="disabled">Disabled</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-[12px] overflow-hidden border" style={{ borderColor: '#352f31' }}>
        <table className="w-full text-[13px]">
          <thead>
            <tr style={{ background: '#1a1218', borderBottom: '1px solid #352f31' }}>
              {['ID', 'Key', 'Label', 'Status', 'Duration', 'Expires', 'HWID', 'Uses', 'Created', 'Actions'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-semibold uppercase tracking-widest text-[11px]"
                    style={{ color: '#5d585c' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={10} className="px-4 py-8 text-center" style={{ color: '#5d585c' }}>Loading…</td></tr>
            )}
            {!loading && keys.length === 0 && (
              <tr><td colSpan={10} className="px-4 py-8 text-center" style={{ color: '#5d585c' }}>No keys found</td></tr>
            )}
            {keys.map((k, i) => (
              <tr key={k.id}
                  style={{ background: i % 2 === 0 ? '#1c1318' : '#1a1216', borderBottom: '1px solid #2a2226' }}>
                <td className="px-4 py-3" style={{ color: '#5d585c' }}>{k.id}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <code className="font-mono text-[12px]" style={{ color: '#c5c0c2' }}>
                      {k.key_value.slice(0, 14)}…
                    </code>
                    <button onClick={() => copy(k.id, k.key_value)}
                            className="text-[11px] px-2 py-0.5 rounded"
                            style={{ color: copied === k.id ? '#16a34a' : '#5d585c', background: '#2a2024' }}>
                      {copied === k.id ? '✓' : 'copy'}
                    </button>
                  </div>
                </td>
                <td className="px-4 py-3" style={{ color: '#868283' }}>{k.label || '—'}</td>
                <td className="px-4 py-3"><Badge status={k.status} /></td>
                <td className="px-4 py-3"><DurationBadge duration_days={k.duration_days} /></td>
                <td className="px-4 py-3 text-[12px]">{fmtExpiry(k.expires_at, k.duration_days)}</td>
                <td className="px-4 py-3">
                  {k.hwid
                    ? <div className="flex items-center gap-1.5">
                        <code className="text-[11px] font-mono" style={{ color: '#868283' }}>{k.hwid.slice(0, 8)}…</code>
                        <button onClick={() => resetHwid(k.id)} title="Reset HWID"
                                className="text-[10px] px-1.5 py-0.5 rounded"
                                style={{ color: '#dc2625', background: '#dc262522' }}>↺</button>
                      </div>
                    : <span style={{ color: '#5d585c' }}>—</span>}
                </td>
                <td className="px-4 py-3" style={{ color: '#868283' }}>
                  {k.uses}{k.max_uses ? `/${k.max_uses}` : ''}
                </td>
                <td className="px-4 py-3" style={{ color: '#868283' }}>{fmt(k.created_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button onClick={() => toggleStatus(k)}
                            className="text-[11px] px-2 py-1 rounded"
                            style={{
                              color: k.status === 'active' ? '#dc2625' : '#16a34a',
                              background: k.status === 'active' ? '#dc262518' : '#16a34a18',
                            }}>
                      {k.status === 'active' ? 'Disable' : 'Enable'}
                    </button>
                    <button onClick={() => deleteKey(k.id)}
                            className="text-[11px] px-2 py-1 rounded"
                            style={{ color: '#dc2625', background: '#dc262518' }}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 flex items-center justify-center z-50"
             style={{ background: 'rgba(0,0,0,0.7)' }}
             onClick={e => e.target === e.currentTarget && setCreate(false)}>
          <div className="w-[420px] rounded-[17px] p-8"
               style={{ background: 'linear-gradient(180deg,#21161a 0%,#161014 100%)', border: '1px solid #352f31', boxShadow: '0 12px 55px rgba(0,0,0,0.8)' }}>
            <h2 className="text-[18px] font-bold mb-1" style={{ color: '#e5e3e4' }}>Create Key</h2>
            <p className="text-[12px] mb-6" style={{ color: '#5d585c' }}>
              Timer starts on first activation, not on creation.
            </p>

            <label className="text-[12px] mb-1.5 block" style={{ color: '#888485' }}>Duration</label>
            <select value={durationDays} onChange={e => setDuration(e.target.value)}
                    className={inputCls + ' w-full mb-4'} style={selectStyle}>
              {DURATION_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>

            <label className="text-[12px] mb-1.5 block" style={{ color: '#888485' }}>Label (optional)</label>
            <input value={label} onChange={e => setLabel(e.target.value)} placeholder="e.g. Customer name"
                   className={inputCls + ' w-full mb-4'} style={inputStyle} />

            <label className="text-[12px] mb-1.5 block" style={{ color: '#888485' }}>Max Uses (optional)</label>
            <input value={maxUses} onChange={e => setMaxUses(e.target.value)} type="number" min="1" placeholder="Unlimited"
                   className={inputCls + ' w-full mb-6'} style={inputStyle} />

            <div className="flex gap-3">
              <button onClick={() => setCreate(false)}
                      className="flex-1 h-[40px] rounded-[8px] text-[13px]"
                      style={{ background: '#2a2024', color: '#868283', border: '1px solid #352c2f' }}>
                Cancel
              </button>
              <button onClick={createKey} disabled={creating}
                      className="flex-1 h-[40px] rounded-[8px] text-[13px] font-semibold text-white"
                      style={{ background: '#dc2625', boxShadow: '0 0 14px rgba(220,38,37,0.35)' }}>
                {creating ? 'Creating…' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}