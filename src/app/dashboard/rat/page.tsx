// app/dashboard/rat/page.tsx
'use client'
import { useEffect, useState, useRef, useCallback } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Agent {
  id: string
  hostname: string
  username: string
  platform: string
  ip: string
  alias: string | null
  last_seen: string
  connected: boolean
}

interface AgentDetail extends Agent {
  screenshot_b64?: string
  stream_frame?: string
  stream_updated_at?: string
  blocked_sites: string[]
  messages: Message[]
  files?: FileEntry[]
  file_cwd?: string
  processes?: Process[]
}

interface Message {
  id: number
  sender: 'admin' | 'agent'
  body: string
  created_at: string
}

interface FileEntry {
  name: string
  path: string
  is_dir: boolean
  size: number
  modified: string
}

interface Process {
  pid: number
  name: string
  cpu: number
  mem: number
  status: string
}

type Tab = 'screen' | 'stream' | 'files' | 'processes' | 'sites' | 'chat' | 'info'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function ago(iso: string) {
  const d = Date.now() - new Date(iso).getTime()
  if (d < 10000) return 'just now'
  if (d < 60000) return `${Math.floor(d / 1000)}s ago`
  if (d < 3600000) return `${Math.floor(d / 60000)}m ago`
  return `${Math.floor(d / 3600000)}h ago`
}

function fmtBytes(b: number) {
  if (!b) return '—'
  if (b < 1024) return `${b} B`
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1073741824) return `${(b / 1048576).toFixed(1)} MB`
  return `${(b / 1073741824).toFixed(2)} GB`
}

/** Ensures raw base64 gets the correct data URI prefix for display as an image. */
function toImgSrc(raw: string | undefined | null): string | null {
  if (!raw) return null
  if (raw.startsWith('data:')) return raw
  return `data:image/jpeg;base64,${raw}`
}

/** Returns the parent directory of a path, handling both Windows and Unix separators. */
function parentPath(p: string): string {
  const norm = p.replace(/\\/g, '/')
  const parts = norm.split('/').filter(Boolean)
  if (parts.length <= 1) {
    // Already at root
    return /^[a-zA-Z]:/.test(p) ? parts[0] + '\\' : '/'
  }
  parts.pop()
  const joined = parts.join('/')
  // Re-apply backslash for Windows paths
  if (/^[a-zA-Z]:/.test(joined)) return joined.replace(/\//g, '\\')
  return joined || '/'
}

async function sendCommand(agentId: string, type: string, payload: Record<string, unknown> = {}) {
  const res = await fetch(`/api/rat/agents/${encodeURIComponent(agentId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, payload }),
  })
  if (res.ok) return res.json()
  return null
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

function Dot({ on }: { on: boolean }) {
  return (
    <span className="inline-block w-[7px] h-[7px] rounded-full shrink-0"
      style={{ background: on ? '#22c55e' : '#3a3537', boxShadow: on ? '0 0 6px #22c55e88' : 'none' }} />
  )
}

function Btn({ children, onClick, danger, active, small, disabled, title }: {
  children: React.ReactNode; onClick?: () => void; danger?: boolean
  active?: boolean; small?: boolean; disabled?: boolean; title?: string
}) {
  const sz = small ? 'text-[11px] px-2.5 py-1' : 'text-[12px] px-4 py-2'
  const fg = active || danger ? '#dc2625' : '#868283'
  const bc = active || danger ? '#dc262544' : '#2e292b'
  return (
    <button title={title} onClick={onClick} disabled={disabled}
      className={`${sz} rounded-[7px] border transition-all disabled:opacity-40 shrink-0`}
      style={{ background: active ? 'rgba(220,38,37,0.12)' : danger ? 'rgba(220,38,37,0.06)' : '#1c1418', color: fg, borderColor: bc }}
      onMouseEnter={e => { if (!disabled) { e.currentTarget.style.color = '#e5e3e4'; e.currentTarget.style.borderColor = '#4a4448' } }}
      onMouseLeave={e => { e.currentTarget.style.color = fg; e.currentTarget.style.borderColor = bc }}>
      {children}
    </button>
  )
}

function Card({ children, className = '', style }: {
  children: React.ReactNode; className?: string; style?: React.CSSProperties
}) {
  return (
    <div className={`rounded-[10px] border ${className}`}
      style={{ borderColor: '#2e292b', background: 'linear-gradient(180deg,#1c1418 0%,#181114 100%)', ...style }}>
      {children}
    </div>
  )
}

function PanelHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 border-b shrink-0"
      style={{ borderColor: '#2e292b' }}>
      {children}
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] uppercase tracking-widest mb-3" style={{ color: '#3a3537' }}>{children}</p>
}

function Input({ value, onChange, placeholder, onKeyDown, className = '' }: {
  value: string; onChange: (v: string) => void; placeholder?: string
  onKeyDown?: React.KeyboardEventHandler<HTMLInputElement>; className?: string
}) {
  return (
    <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      onKeyDown={onKeyDown}
      className={`h-[36px] rounded-[8px] px-3 text-[12px] outline-none ${className}`}
      style={{ background: '#0f0b0c', border: '1px solid #2e292b', color: '#c5c0c2' }}
      onFocus={e => { e.target.style.borderColor = '#4e4447' }}
      onBlur={e => { e.target.style.borderColor = '#2e292b' }} />
  )
}

// ─── Agent sidebar card ───────────────────────────────────────────────────────

function AgentCard({ agent, selected, onSelect }: { agent: Agent; selected: boolean; onSelect: () => void }) {
  const label = agent.alias || agent.hostname
  return (
    <button onClick={onSelect} className="w-full text-left rounded-[10px] p-3 border transition-all"
      style={{
        background: selected ? 'linear-gradient(180deg,#2a1a1b 0%,#211417 100%)' : 'linear-gradient(180deg,#1c1418 0%,#181114 100%)',
        borderColor: selected ? '#dc2625' : '#2e292b',
        boxShadow: selected ? '0 0 0 1px #dc262522' : 'none',
      }}>
      <div className="flex items-center gap-2 mb-0.5">
        <Dot on={agent.connected} />
        <span className="text-[13px] font-semibold truncate" style={{ color: '#e5e3e4' }}>{label}</span>
        {agent.alias && (
          <span className="text-[10px] shrink-0" style={{ color: '#5d585c' }}>({agent.hostname})</span>
        )}
      </div>
      <p className="text-[11px] truncate" style={{ color: '#5d585c' }}>{agent.username} · {agent.platform.split(' ')[0]}</p>
      <div className="flex items-center justify-between mt-0.5">
        <span className="text-[11px] font-mono" style={{ color: '#dc262566' }}>{agent.ip}</span>
        <span className="text-[10px]" style={{ color: '#3a3537' }}>{ago(agent.last_seen)}</span>
      </div>
    </button>
  )
}

// ─── Tab bar ─────────────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'screen',    label: 'Screenshot', icon: '📷' },
  { id: 'stream',    label: 'Live',       icon: '📺' },
  { id: 'files',     label: 'Files',      icon: '📁' },
  { id: 'processes', label: 'Processes',  icon: '⚙️' },
  { id: 'sites',     label: 'Blocker',    icon: '🚫' },
  { id: 'chat',      label: 'Message',    icon: '💬' },
  { id: 'info',      label: 'Info',       icon: '🖥' },
]

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <div className="flex gap-1 mb-4 flex-wrap">
      {TABS.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)}
          className="text-[12px] px-3 py-1.5 rounded-[7px] border transition-all flex items-center gap-1.5"
          style={{
            background: active === t.id ? 'rgba(220,38,37,0.1)' : '#161014',
            color: active === t.id ? '#dc2625' : '#5d585c',
            borderColor: active === t.id ? '#dc262533' : '#2e292b',
          }}>
          <span>{t.icon}</span>{t.label}
        </button>
      ))}
    </div>
  )
}

// ─── Screenshot tab ───────────────────────────────────────────────────────────

function ScreenshotTab({ agent, detail, onRefresh }: { agent: Agent; detail: AgentDetail | null; onRefresh: () => void }) {
  const [requesting, setRequesting] = useState(false)

  async function request() {
    setRequesting(true)
    await sendCommand(agent.id, 'screenshot')
    let attempts = 0
    const poll = setInterval(() => {
      attempts++; onRefresh()
      if (attempts > 20) { clearInterval(poll); setRequesting(false) }
    }, 800)
    setTimeout(() => { clearInterval(poll); setRequesting(false) }, 18000)
  }

  // FIX: always prepend data URI prefix — raw base64 can't be used as img src directly
  const src = toImgSrc(detail?.screenshot_b64)

  return (
    <Card>
      <PanelHeader>
        <span className="text-[12px]" style={{ color: '#5d585c' }}>Screenshot · {agent.alias || agent.hostname}</span>
        <Btn onClick={request} disabled={requesting}>{requesting ? 'Waiting…' : 'Take Screenshot'}</Btn>
      </PanelHeader>
      <div className="flex items-center justify-center p-4" style={{ minHeight: 320 }}>
        {src
          ? <img src={src} alt="Screenshot" className="w-full rounded-[6px] object-contain" style={{ maxHeight: 520 }} />
          : <p className="text-[13px]" style={{ color: '#3a3537' }}>No screenshot yet — click Take Screenshot</p>}
      </div>
    </Card>
  )
}

// ─── Live stream tab ──────────────────────────────────────────────────────────

function StreamTab({ agent, detail, onRefresh }: { agent: Agent; detail: AgentDetail | null; onRefresh: () => void }) {
  const [streaming, setStreaming] = useState(false)
  const iRef = useRef<NodeJS.Timeout | null>(null)

  async function startStream() {
    await sendCommand(agent.id, 'stream_start')
    setStreaming(true)
    // Poll at 400ms — client sends frames every 250ms so this keeps up
    iRef.current = setInterval(onRefresh, 400)
  }
  async function stopStream() {
    await sendCommand(agent.id, 'stream_stop')
    setStreaming(false)
    if (iRef.current) clearInterval(iRef.current)
  }
  useEffect(() => () => { if (iRef.current) clearInterval(iRef.current) }, [])

  const updatedAt = detail?.stream_updated_at ? ago(detail.stream_updated_at) : null
  // FIX: prepend data URI prefix — this was causing 400 errors
  const frameSrc = toImgSrc(detail?.stream_frame)

  return (
    <Card>
      <PanelHeader>
        <div className="flex items-center gap-3">
          <span className="text-[12px]" style={{ color: '#5d585c' }}>Live Stream · {agent.alias || agent.hostname}</span>
          {streaming && (
            <span className="flex items-center gap-1.5 text-[11px]" style={{ color: '#22c55e' }}>
              <span className="inline-block w-[6px] h-[6px] rounded-full bg-[#22c55e] animate-pulse" />
              LIVE{updatedAt && ` · ${updatedAt}`}
            </span>
          )}
        </div>
        {!streaming
          ? <Btn onClick={startStream}>Start Stream</Btn>
          : <Btn onClick={stopStream} danger>Stop Stream</Btn>}
      </PanelHeader>
      <div className="flex items-center justify-center p-4" style={{ minHeight: 320 }}>
        {frameSrc
          ? <img src={frameSrc} alt="Live" className="w-full rounded-[6px] object-contain" style={{ maxHeight: 520 }} />
          : (
            <div className="text-center">
              <p className="text-[13px] mb-1" style={{ color: '#3a3537' }}>{streaming ? 'Waiting for first frame…' : 'Stream not started'}</p>
              {!streaming && <p className="text-[11px]" style={{ color: '#2a2527' }}>Click Start Stream to begin</p>}
            </div>
          )}
      </div>
    </Card>
  )
}

// ─── File explorer tab ────────────────────────────────────────────────────────

function FilesTab({ agent, detail, onRefresh }: { agent: Agent; detail: AgentDetail | null; onRefresh: () => void }) {
  const [cwd, setCwd] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<{ header: string; content: string } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const files = detail?.files ?? []
  const currentDir = detail?.file_cwd ?? cwd

  // FIX: poll multiple times to get the updated listing back from the client
  async function browse(path: string) {
    setLoading(true)
    setCwd(path)
    setFileContent(null)
    await sendCommand(agent.id, 'file_list', { path })
    let attempts = 0
    const poll = setInterval(() => {
      attempts++
      onRefresh()
      if (attempts >= 6) { clearInterval(poll); setLoading(false) }
    }, 500)
  }

  // FIX: use parentPath() helper which handles Windows backslashes correctly
  async function goUp() {
    const parent = parentPath(currentDir || cwd)
    await browse(parent)
  }

  async function downloadFile(path: string) {
    await sendCommand(agent.id, 'file_download', { path })
    let attempts = 0
    const poll = setInterval(async () => {
      attempts++
      const res = await fetch(`/api/rat/agents/${encodeURIComponent(agent.id)}/file?path=${encodeURIComponent(path)}`)
      if (res.ok) {
        clearInterval(poll)
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = path.split(/[/\\]/).pop() || 'file'
        a.click()
        URL.revokeObjectURL(url)
      }
      if (attempts > 20) clearInterval(poll)
    }, 800)
  }

  async function deleteFile(path: string) {
    await sendCommand(agent.id, 'file_delete', { path })
    setConfirmDelete(null)
    setTimeout(onRefresh, 800)
  }

  async function uploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    const reader = new FileReader()
    reader.onload = async () => {
      const b64 = (reader.result as string).split(',')[1]
      await sendCommand(agent.id, 'file_upload', { path: currentDir, name: file.name, data_b64: b64 })
      setTimeout(() => { onRefresh(); setUploading(false) }, 1000)
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  async function readFile(path: string) {
    setFileContent(null)
    await sendCommand(agent.id, 'file_read', { path })
    let attempts = 0
    const poll = setInterval(() => {
      attempts++; onRefresh()
      if (attempts > 15) clearInterval(poll)
    }, 600)
  }

  // Watch detail messages for file_read replies
  const prevMsgCount = useRef(0)
  useEffect(() => {
    const msgs = detail?.messages ?? []
    if (msgs.length > prevMsgCount.current) {
      prevMsgCount.current = msgs.length
      const last = msgs[msgs.length - 1]
      if (last?.sender === 'agent' && last.body.startsWith('[file_read:')) {
        const nl = last.body.indexOf('\n\n')
        const header = nl > -1 ? last.body.slice(0, nl) : last.body
        const content = nl > -1 ? last.body.slice(nl + 2) : ''
        setFileContent({ header, content })
      }
    }
  }, [detail?.messages])

  if (fileContent) {
    return (
      <Card style={{ minHeight: 460 }}>
        <PanelHeader>
          <div className="flex items-center gap-2 min-w-0">
            <button onClick={() => setFileContent(null)}
              className="text-[11px] px-2 py-1 rounded-[5px] shrink-0 transition-colors"
              style={{ background: '#0f0b0c', border: '1px solid #2e292b', color: '#5d585c' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#e5e3e4')}
              onMouseLeave={e => (e.currentTarget.style.color = '#5d585c')}>← Back</button>
            <span className="text-[11px] font-mono truncate" style={{ color: '#5d585c' }}>{fileContent.header}</span>
          </div>
        </PanelHeader>
        <pre className="p-4 text-[11px] overflow-auto font-mono"
          style={{ color: '#c5c0c2', maxHeight: 420, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {fileContent.content}
        </pre>
      </Card>
    )
  }

  return (
    <Card style={{ minHeight: 460 }}>
      <PanelHeader>
        <div className="flex items-center gap-2 min-w-0">
          <button onClick={goUp} className="text-[11px] px-2 py-1 rounded-[5px] shrink-0 transition-colors"
            style={{ background: '#0f0b0c', border: '1px solid #2e292b', color: '#5d585c' }}
            onMouseEnter={e => (e.currentTarget.style.color = '#e5e3e4')}
            onMouseLeave={e => (e.currentTarget.style.color = '#5d585c')}>↑ Up</button>
          <span className="text-[11px] font-mono truncate" style={{ color: '#5d585c' }}>
            {currentDir || 'Click a folder or enter a path'}
          </span>
        </div>
        <div className="flex gap-2">
          <input ref={fileInputRef} type="file" className="hidden" onChange={uploadFile} />
          <Btn small onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? 'Uploading…' : '⬆ Upload'}
          </Btn>
          <Btn small onClick={() => browse(currentDir || cwd || '/')}>
            {loading ? '…' : '↺ Refresh'}
          </Btn>
        </div>
      </PanelHeader>

      <div className="px-4 py-2 border-b flex gap-2" style={{ borderColor: '#2e292b' }}>
        <Input value={cwd} onChange={setCwd} placeholder="Enter path e.g. C:\Users or /home/user"
          onKeyDown={e => { if (e.key === 'Enter') browse(cwd) }} className="flex-1" />
        <Btn small onClick={() => browse(cwd)}>Go</Btn>
      </div>

      <div className="overflow-y-auto" style={{ maxHeight: 380 }}>
        {files.length === 0
          ? (
            <div className="flex items-center justify-center p-8">
              <p className="text-[12px]" style={{ color: '#3a3537' }}>
                {loading ? 'Loading…' : 'Enter a path above to browse files'}
              </p>
            </div>
          )
          : files.map(f => {
            const isText = !f.is_dir && /\.(txt|log|json|js|ts|tsx|jsx|py|md|csv|xml|html|css|ini|cfg|env|sh|bat|ps1|yaml|yml|toml)$/i.test(f.name)
            return (
              <div key={f.path}
                className="flex items-center gap-3 px-4 py-2 border-b transition-colors group"
                style={{ borderColor: '#1a1518' }}
                onMouseEnter={e => (e.currentTarget.style.background = '#1a1416')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                <span className="text-[14px] shrink-0">{f.is_dir ? '📁' : isText ? '📝' : '📄'}</span>
                {/* FIX: clicking a folder calls browse(f.path) which uses the FULL path from the client */}
                <button className="flex-1 text-left min-w-0"
                  onClick={() => {
                    if (f.is_dir) browse(f.path)
                    else if (isText) readFile(f.path)
                  }}>
                  <p className="text-[12px] truncate"
                    style={{ color: f.is_dir ? '#c5c0c2' : isText ? '#a89fa1' : '#868283' }}>
                    {f.name}
                  </p>
                  <p className="text-[10px]" style={{ color: '#3a3537' }}>
                    {f.is_dir ? 'Directory' : fmtBytes(f.size)} · {f.modified}
                  </p>
                </button>
                <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!f.is_dir && (
                    <Btn small onClick={() => downloadFile(f.path)}>⬇</Btn>
                  )}
                  {confirmDelete === f.path
                    ? (
                      <div className="flex gap-1">
                        <Btn small danger onClick={() => deleteFile(f.path)}>Confirm</Btn>
                        <Btn small onClick={() => setConfirmDelete(null)}>Cancel</Btn>
                      </div>
                    )
                    : <Btn small danger onClick={() => setConfirmDelete(f.path)}>🗑</Btn>
                  }
                </div>
              </div>
            )
          })
        }
      </div>
    </Card>
  )
}

// ─── Processes tab ────────────────────────────────────────────────────────────

function ProcessesTab({ agent, detail, onRefresh }: { agent: Agent; detail: AgentDetail | null; onRefresh: () => void }) {
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [confirmKill, setConfirmKill] = useState<number | null>(null)
  const processes = detail?.processes ?? []

  async function refresh() {
    setLoading(true)
    await sendCommand(agent.id, 'process_list')
    setTimeout(() => { onRefresh(); setLoading(false) }, 1500)
  }

  async function killProcess(pid: number) {
    await sendCommand(agent.id, 'process_kill', { pid })
    setConfirmKill(null)
    setTimeout(onRefresh, 1000)
  }

  const filtered = processes.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    String(p.pid).includes(search)
  )

  return (
    <Card style={{ minHeight: 460 }}>
      <PanelHeader>
        <span className="text-[12px]" style={{ color: '#5d585c' }}>
          Processes ({processes.length})
        </span>
        <Btn onClick={refresh} disabled={loading}>{loading ? 'Refreshing…' : '↺ Refresh'}</Btn>
      </PanelHeader>

      <div className="px-4 py-2 border-b" style={{ borderColor: '#2e292b' }}>
        <Input value={search} onChange={setSearch} placeholder="Search by name or PID…" className="w-full" />
      </div>

      <div className="grid px-4 py-1.5 border-b" style={{ gridTemplateColumns: '60px 1fr 70px 70px 80px 60px', borderColor: '#1e191b' }}>
        {['PID', 'Name', 'CPU %', 'Mem MB', 'Status', ''].map(h => (
          <span key={h} className="text-[10px] uppercase tracking-widest" style={{ color: '#3a3537' }}>{h}</span>
        ))}
      </div>

      <div className="overflow-y-auto" style={{ maxHeight: 360 }}>
        {filtered.length === 0
          ? <p className="text-center text-[12px] p-8" style={{ color: '#3a3537' }}>
              {processes.length === 0 ? 'Click Refresh to load processes' : 'No results'}
            </p>
          : filtered.map(p => (
            <div key={p.pid}
              className="grid items-center px-4 py-1.5 border-b group transition-colors"
              style={{ gridTemplateColumns: '60px 1fr 70px 70px 80px 60px', borderColor: '#1a1518' }}
              onMouseEnter={e => (e.currentTarget.style.background = '#1a1416')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
              <span className="text-[11px] font-mono" style={{ color: '#5d585c' }}>{p.pid}</span>
              <span className="text-[12px] truncate pr-2" style={{ color: '#c5c0c2' }}>{p.name}</span>
              <span className="text-[11px] font-mono" style={{ color: p.cpu > 20 ? '#dc2625' : '#868283' }}>{p.cpu.toFixed(1)}</span>
              <span className="text-[11px] font-mono" style={{ color: '#868283' }}>{(p.mem / 1048576).toFixed(0)}</span>
              <span className="text-[11px]" style={{ color: p.status === 'running' ? '#22c55e' : '#5d585c' }}>{p.status}</span>
              <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                {confirmKill === p.pid
                  ? (
                    <div className="flex gap-1">
                      <Btn small danger onClick={() => killProcess(p.pid)}>Kill</Btn>
                      <Btn small onClick={() => setConfirmKill(null)}>✕</Btn>
                    </div>
                  )
                  : <Btn small danger onClick={() => setConfirmKill(p.pid)}>Kill</Btn>
                }
              </div>
            </div>
          ))
        }
      </div>
    </Card>
  )
}

// ─── Site blocker tab ─────────────────────────────────────────────────────────

const PRESETS = [
  { label: 'Social Media', domains: ['facebook.com','instagram.com','twitter.com','x.com','tiktok.com','snapchat.com','reddit.com','pinterest.com','tumblr.com','discord.com','whatsapp.com'] },
  { label: 'Gaming',       domains: ['roblox.com','minecraft.net','steampowered.com','epicgames.com','twitch.tv','fortnite.com','leagueoflegends.com','chess.com','poki.com','y8.com','friv.com','coolmathgames.com','addictinggames.com'] },
  { label: 'Video',        domains: ['youtube.com','netflix.com','disneyplus.com','primevideo.com','hulu.com','hbomax.com','vimeo.com','dailymotion.com','crunchyroll.com'] },
  { label: 'Adult',        domains: ['pornhub.com','xvideos.com','xnxx.com','redtube.com','onlyfans.com'] },
  { label: 'Gambling',     domains: ['bet365.com','draftkings.com','fanduel.com','betway.com','pokerstars.com'] },
]

function SitesTab({ agent, detail, onRefresh }: { agent: Agent; detail: AgentDetail | null; onRefresh: () => void }) {
  const [input, setInput] = useState('')
  const [working, setWorking] = useState(false)
  const [search, setSearch] = useState('')
  const blocked = detail?.blocked_sites ?? []

  // FIX: poll multiple times after sending block command so the list updates
  function pollRefresh(times = 6, ms = 500) {
    let i = 0
    const id = setInterval(() => { i++; onRefresh(); if (i >= times) { clearInterval(id); setWorking(false) } }, ms)
  }

  async function blockDomains(domains: string[]) {
    setWorking(true)
    const clean = domains
      .map(d => d.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0])
      .filter(Boolean)
    await sendCommand(agent.id, 'block_sites', { domains: clean })
    pollRefresh()
  }

  async function unblockDomain(domain: string) {
    setWorking(true)
    await sendCommand(agent.id, 'unblock_sites', { domains: [domain] })
    pollRefresh()
  }

  async function unblockAll() {
    setWorking(true)
    await sendCommand(agent.id, 'unblock_sites', { domains: blocked })
    pollRefresh()
  }

  function handleAdd() {
    if (!input.trim()) return
    const domains = input.split(/[\n,\s]+/).filter(Boolean)
    blockDomains(domains)
    setInput('')
  }

  const filteredBlocked = blocked.filter(d => d.includes(search.toLowerCase()))

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-4">
        <SectionLabel>Quick Block Presets</SectionLabel>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map(p => (
            <Btn key={p.label} onClick={() => blockDomains(p.domains)} disabled={working} small>
              🚫 {p.label}
            </Btn>
          ))}
        </div>
      </Card>

      <Card className="p-4">
        <SectionLabel>Block Custom Sites</SectionLabel>
        <div className="flex gap-2 items-start">
          <textarea value={input} onChange={e => setInput(e.target.value)} rows={3}
            placeholder={"Enter domains, one per line or comma-separated\ne.g. youtube.com, netflix.com"}
            className="flex-1 rounded-[8px] px-3 py-2 text-[12px] resize-none outline-none"
            style={{ background: '#0f0b0c', border: '1px solid #2e292b', color: '#c5c0c2' }}
            onFocus={e => { e.target.style.borderColor = '#4e4447' }}
            onBlur={e => { e.target.style.borderColor = '#2e292b' }} />
          <Btn onClick={handleAdd} disabled={working || !input.trim()}>Block</Btn>
        </div>
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <SectionLabel>Blocked Sites ({blocked.length})</SectionLabel>
          {blocked.length > 0 && <Btn onClick={unblockAll} disabled={working} danger small>Unblock All</Btn>}
        </div>
        {blocked.length > 4 && (
          <div className="mb-3">
            <Input value={search} onChange={setSearch} placeholder="Filter blocked sites…" className="w-full" />
          </div>
        )}
        {blocked.length === 0
          ? <p className="text-[12px]" style={{ color: '#3a3537' }}>No sites blocked yet</p>
          : (
            <div className="flex flex-col gap-1 max-h-[280px] overflow-y-auto">
              {filteredBlocked.map(domain => (
                <div key={domain} className="flex items-center justify-between px-3 py-2 rounded-[7px] group"
                  style={{ background: '#0f0b0c', border: '1px solid #1e191b' }}>
                  <span className="text-[12px] font-mono" style={{ color: '#868283' }}>{domain}</span>
                  <button onClick={() => unblockDomain(domain)}
                    className="text-[11px] opacity-0 group-hover:opacity-100 transition-all"
                    style={{ color: '#3a3537' }}
                    onMouseEnter={e => (e.currentTarget.style.color = '#dc2625')}
                    onMouseLeave={e => (e.currentTarget.style.color = '#3a3537')}>✕</button>
                </div>
              ))}
            </div>
          )}
      </Card>
    </div>
  )
}

// ─── Chat tab ─────────────────────────────────────────────────────────────────

function ChatTab({ agent, detail, onRefresh }: { agent: Agent; detail: AgentDetail | null; onRefresh: () => void }) {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  // Optimistic local messages so sends appear immediately without waiting for DB roundtrip
  const [optimistic, setOptimistic] = useState<Message[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  const serverMessages = detail?.messages ?? []
  // Keep optimistic messages that haven't yet appeared in the server list
  const serverBodies = new Set(serverMessages.map(m => m.body + m.sender))
  const pendingOptimistic = optimistic.filter(m => !serverBodies.has(m.body + m.sender))
  const messages = [
    ...serverMessages,
    ...pendingOptimistic,
  ].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages.length])
  // FIX: poll more frequently so replies show up faster
  useEffect(() => { const id = setInterval(onRefresh, 2500); return () => clearInterval(id) }, [onRefresh])

  async function send() {
    if (!input.trim()) return
    const body = input.trim()
    setSending(true)
    setInput('')

    // Optimistically add the message so it appears immediately
    const tempMsg: Message = {
      id: -Date.now(),
      sender: 'admin',
      body,
      created_at: new Date().toISOString(),
    }
    setOptimistic(prev => [...prev, tempMsg])

    await sendCommand(agent.id, 'message', { body })
    setTimeout(() => { onRefresh(); setSending(false) }, 400)
  }

  return (
    <div className="rounded-[10px] border flex flex-col"
      style={{ borderColor: '#2e292b', background: 'linear-gradient(180deg,#1c1418 0%,#181114 100%)', height: 500 }}>
      <PanelHeader>
        <span className="text-[12px]" style={{ color: '#5d585c' }}>
          Live Message · {agent.alias || agent.hostname}
          <span className="ml-2 text-[11px]" style={{ color: '#3a3537' }}>(popup appears on their screen)</span>
        </span>
      </PanelHeader>
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
        {messages.length === 0 && (
          <p className="text-center text-[12px] mt-8" style={{ color: '#3a3537' }}>No messages yet — send one to start</p>
        )}
        {messages.map(m => (
          <div key={m.id} className={`flex ${m.sender === 'admin' ? 'justify-end' : 'justify-start'}`}>
            <div className="max-w-[75%] px-3 py-2 rounded-[10px] text-[13px]"
              style={{
                background: m.sender === 'admin' ? 'rgba(220,38,37,0.12)' : '#1c1418',
                color: m.sender === 'admin' ? '#e5e3e4' : '#c5c0c2',
                border: `1px solid ${m.sender === 'admin' ? '#dc262533' : '#2e292b'}`,
                borderBottomRightRadius: m.sender === 'admin' ? 2 : 10,
                borderBottomLeftRadius: m.sender === 'agent' ? 2 : 10,
                opacity: m.id < 0 ? 0.6 : 1,  // dim optimistic messages slightly
              }}>
              {m.body}
              <p className="text-[10px] mt-1 opacity-50">
                {m.sender === 'admin' ? 'You' : agent.alias || agent.username} · {ago(m.created_at)}
                {m.id < 0 && ' · sending…'}
              </p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="p-3 border-t flex gap-2 shrink-0" style={{ borderColor: '#2e292b' }}>
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="Type a message… (Enter to send)"
          className="flex-1 h-[38px] rounded-[8px] px-3 text-[13px] outline-none"
          style={{ background: '#0f0b0c', border: '1px solid #2e292b', color: '#c5c0c2' }}
          onFocus={e => { e.target.style.borderColor = '#4e4447' }}
          onBlur={e => { e.target.style.borderColor = '#2e292b' }} />
        <Btn onClick={send} disabled={sending || !input.trim()}>Send</Btn>
      </div>
    </div>
  )
}

// ─── Info tab ─────────────────────────────────────────────────────────────────

function InfoTab({ agent, onAliasChange, onDelete }: { agent: Agent; onAliasChange: () => void; onDelete: () => void }) {
  const [alias, setAlias] = useState(agent.alias ?? '')
  const [saving, setSaving] = useState(false)
  const [startup, setStartup] = useState(false)
  const [confirmDel, setConfirmDel] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function saveAlias() {
    setSaving(true)
    await fetch(`/api/rat/agents/${encodeURIComponent(agent.id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alias: alias.trim() || null }),
    })
    setTimeout(() => { setSaving(false); onAliasChange() }, 300)
  }

  async function toggleStartup() {
    await sendCommand(agent.id, startup ? 'startup_disable' : 'startup_enable')
    setStartup(s => !s)
  }

  async function deleteAgent() {
    setDeleting(true)
    await fetch(`/api/rat/agents/${encodeURIComponent(agent.id)}`, { method: 'DELETE' })
    onDelete()
  }

  const rows: [string, string][] = [
    ['Agent ID',   agent.id],
    ['Hostname',   agent.hostname],
    ['Username',   agent.username],
    ['Platform',   agent.platform],
    ['IP Address', agent.ip],
    ['Last Seen',  new Date(agent.last_seen).toLocaleString()],
    ['Status',     agent.connected ? '🟢 Online' : '🔴 Offline'],
  ]

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-4">
        <SectionLabel>Device Alias</SectionLabel>
        <p className="text-[12px] mb-3" style={{ color: '#5d585c' }}>Give this device a friendly name shown in the sidebar.</p>
        <div className="flex gap-2">
          <Input value={alias} onChange={setAlias} placeholder="e.g. John's PC, Lab Computer 3"
            onKeyDown={e => { if (e.key === 'Enter') saveAlias() }} className="flex-1" />
          <Btn onClick={saveAlias} disabled={saving}>{saving ? 'Saved ✓' : 'Save'}</Btn>
          {alias && <Btn onClick={() => setAlias('')} small danger>Clear</Btn>}
        </div>
      </Card>

      <Card className="p-4">
        <SectionLabel>System Info</SectionLabel>
        <div className="flex flex-col">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-2.5 border-b" style={{ borderColor: '#1e191b' }}>
              <span className="text-[12px]" style={{ color: '#5d585c' }}>{label}</span>
              <span className="text-[12px] font-mono" style={{ color: '#868283' }}>{value}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-4">
        <SectionLabel>Startup</SectionLabel>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[13px]" style={{ color: '#c5c0c2' }}>Run on startup</p>
            <p className="text-[11px] mt-0.5" style={{ color: '#5d585c' }}>
              Adds the client to the system startup (visible in Task Manager startup tab)
            </p>
          </div>
          <Btn onClick={toggleStartup} active={startup}>{startup ? '✓ Enabled' : 'Disabled'}</Btn>
        </div>
      </Card>

      <Card className="p-4" style={{ borderColor: '#3a1a1a' }}>
        <SectionLabel>Danger Zone</SectionLabel>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[13px]" style={{ color: '#c5c0c2' }}>Remove device</p>
            <p className="text-[11px] mt-0.5" style={{ color: '#5d585c' }}>
              Deletes all data for this agent. It will reappear if the client reconnects.
            </p>
          </div>
          {confirmDel
            ? (
              <div className="flex gap-2">
                <Btn danger onClick={deleteAgent} disabled={deleting}>{deleting ? 'Removing…' : 'Confirm'}</Btn>
                <Btn onClick={() => setConfirmDel(false)}>Cancel</Btn>
              </div>
            )
            : <Btn danger onClick={() => setConfirmDel(true)}>Remove Device</Btn>
          }
        </div>
      </Card>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function RATPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<AgentDetail | null>(null)
  const [tab, setTab] = useState<Tab>('screen')
  const [filter, setFilter] = useState<'all' | 'online' | 'offline'>('all')
  const [ipFilter, setIpFilter] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchAgents = useCallback(async () => {
    const res = await fetch('/api/rat/agents')
    if (res.ok) { setAgents(await res.json()); setLoading(false) }
  }, [])

  const fetchDetail = useCallback(async () => {
    if (!selected) return
    const res = await fetch(`/api/rat/agents/${encodeURIComponent(selected)}`)
    if (res.ok) setDetail(await res.json())
  }, [selected])

  useEffect(() => { fetchAgents(); const id = setInterval(fetchAgents, 6000); return () => clearInterval(id) }, [fetchAgents])
  useEffect(() => { setDetail(null); fetchDetail() }, [selected, fetchDetail])

  const uniqueIps = [...new Set(agents.map(a => a.ip))].sort()

  const filtered = agents.filter(a => {
    if (filter === 'online' && !a.connected) return false
    if (filter === 'offline' && a.connected) return false
    if (ipFilter && a.ip !== ipFilter) return false
    return true
  })

  const selectedAgent = agents.find(a => a.id === selected) ?? null
  const onlineCount = agents.filter(a => a.connected).length

  return (
    <div className="p-8 flex flex-col h-full">
      <div className="flex items-center justify-between mb-5 shrink-0">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#e5e3e4' }}>Remote Admin Tool</h1>
          <p className="text-[13px] mt-0.5" style={{ color: '#5d585c' }}>
            {onlineCount} online · {agents.length} total
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <div className="flex gap-1">
            {(['all', 'online', 'offline'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className="text-[12px] px-3 py-1.5 rounded-[7px] capitalize border transition-colors"
                style={{
                  background: filter === f ? 'rgba(220,38,37,0.1)' : '#1c1418',
                  color: filter === f ? '#dc2625' : '#5d585c',
                  borderColor: filter === f ? '#dc262533' : '#2e292b',
                }}>{f}</button>
            ))}
          </div>
          {uniqueIps.length > 1 && (
            <select value={ipFilter} onChange={e => setIpFilter(e.target.value)}
              className="text-[12px] px-3 py-1.5 rounded-[7px] border outline-none"
              style={{ background: ipFilter ? 'rgba(220,38,37,0.1)' : '#1c1418', color: ipFilter ? '#dc2625' : '#5d585c', borderColor: ipFilter ? '#dc262533' : '#2e292b' }}>
              <option value="">All IPs</option>
              {uniqueIps.map(ip => <option key={ip} value={ip}>{ip}</option>)}
            </select>
          )}
        </div>
      </div>

      <div className="flex gap-5 flex-1 min-h-0">
        <div className="w-[220px] shrink-0 flex flex-col gap-2 overflow-y-auto pr-1">
          {loading && <p className="text-[12px] text-center mt-8" style={{ color: '#3a3537' }}>Loading…</p>}
          {!loading && filtered.length === 0 && (
            <div className="mt-8 text-center">
              <p className="text-[13px] mb-1" style={{ color: '#3a3537' }}>No agents</p>
              <p className="text-[11px]" style={{ color: '#2a2527' }}>Run the Python client to connect</p>
            </div>
          )}
          {filtered.map(a => (
            <AgentCard key={a.id} agent={a} selected={selected === a.id}
              onSelect={() => { setSelected(a.id); setTab('screen') }} />
          ))}
        </div>

        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {!selectedAgent
            ? (
              <div className="flex-1 flex items-center justify-center rounded-[12px] border"
                style={{ borderColor: '#2e292b', background: '#0f0b0c', minHeight: 400 }}>
                <div className="text-center">
                  <p className="text-[28px] mb-3">🖥</p>
                  <p className="text-[13px]" style={{ color: '#3a3537' }}>Select an agent from the sidebar</p>
                </div>
              </div>
            )
            : (
              <>
                <TabBar active={tab} onChange={setTab} />
                {tab === 'screen'    && <ScreenshotTab agent={selectedAgent} detail={detail} onRefresh={fetchDetail} />}
                {tab === 'stream'    && <StreamTab     agent={selectedAgent} detail={detail} onRefresh={fetchDetail} />}
                {tab === 'files'     && <FilesTab      agent={selectedAgent} detail={detail} onRefresh={fetchDetail} />}
                {tab === 'processes' && <ProcessesTab  agent={selectedAgent} detail={detail} onRefresh={fetchDetail} />}
                {tab === 'sites'     && <SitesTab      agent={selectedAgent} detail={detail} onRefresh={fetchDetail} />}
                {tab === 'chat'      && <ChatTab       agent={selectedAgent} detail={detail} onRefresh={fetchDetail} />}
                {tab === 'info'      && <InfoTab       agent={selectedAgent} onAliasChange={fetchAgents} onDelete={() => { setSelected(null); fetchAgents() }} />}
              </>
            )
          }
        </div>
      </div>
    </div>
  )
}