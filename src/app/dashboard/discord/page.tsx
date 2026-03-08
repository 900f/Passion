'use client'
// app/dashboard/discord/page.tsx

import { useState, useEffect, useRef, useCallback } from 'react'

/* ─── Types ─────────────────────────────────────────────── */
interface Token  { id: number; alias: string; created_at: string; last_used: string | null }
interface Guild  { id: string; name: string; icon: string | null }
interface Channel{ id: string; name: string; type: number; parent_id: string | null; position: number }
interface BotInfo { id: string; username: string; discriminator: string; avatar: string | null }

type Tab = 'message' | 'embed'

/* ─── Helpers ────────────────────────────────────────────── */
function guildIcon(g: Guild) {
  if (!g.icon) return null
  return `https://cdn.discordapp.com/icons/${g.id}/${g.icon}.webp?size=64`
}

function botAvatar(b: BotInfo) {
  if (!b.avatar) return `https://cdn.discordapp.com/embed/avatars/${Number(b.discriminator) % 5}.png`
  return `https://cdn.discordapp.com/avatars/${b.id}/${b.avatar}.webp?size=64`
}

/* ─── Sub-components ──────────────────────────────────────── */
function Pill({ children, color = '#dc2625' }: { children: React.ReactNode; color?: string }) {
  return (
    <span className="inline-block text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider"
          style={{ background: `${color}22`, color }}>
      {children}
    </span>
  )
}

function Input({
  label, value, onChange, placeholder, type = 'text', mono = false, multiline = false, rows = 3
}: {
  label?: string; value: string; onChange: (v: string) => void
  placeholder?: string; type?: string; mono?: boolean; multiline?: boolean; rows?: number
}) {
  const base = {
    background: '#1e1518', border: '1px solid #352c2f', color: '#c5c0c2',
    fontFamily: mono ? 'monospace' : undefined,
    resize: 'vertical' as const,
  }
  const focusStyle = { borderColor: '#5a4f52', background: '#231a1e' }
  const blurStyle  = { borderColor: '#352c2f', background: '#1e1518' }

  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-[12px] font-medium" style={{ color: '#888485' }}>{label}</label>}
      {multiline ? (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          rows={rows}
          className="rounded-[8px] px-3 py-2.5 text-[13px] outline-none transition-colors w-full"
          style={base}
          onFocus={e => Object.assign(e.target.style, focusStyle)}
          onBlur={e  => Object.assign(e.target.style, blurStyle)}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="h-[40px] rounded-[8px] px-3 text-[13px] outline-none transition-colors w-full"
          style={base}
          onFocus={e => Object.assign(e.target.style, focusStyle)}
          onBlur={e  => Object.assign(e.target.style, blurStyle)}
        />
      )}
    </div>
  )
}

function ColorSwatch({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const presets = ['#dc2625','#5865F2','#57F287','#FEE75C','#EB459E','#ED4245','#ffffff','#2b2d31']
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[12px] font-medium" style={{ color: '#888485' }}>Embed Color</label>
      <div className="flex items-center gap-2 flex-wrap">
        {presets.map(c => (
          <button key={c} onClick={() => onChange(c)}
                  className="w-6 h-6 rounded-full transition-transform hover:scale-110"
                  style={{
                    background: c,
                    border: value === c ? '2px solid #e5e3e4' : '2px solid transparent',
                    boxShadow: value === c ? '0 0 0 1px #e5e3e4' : 'none',
                  }} />
        ))}
        <input type="color" value={value} onChange={e => onChange(e.target.value)}
               className="w-6 h-6 rounded cursor-pointer"
               style={{ border: '1px solid #352c2f', background: 'transparent', padding: 0 }} />
      </div>
    </div>
  )
}

/* ─── Discord Markdown → HTML ────────────────────────────────── */
function renderMd(text: string): string {
  return text
    // escape HTML first to prevent XSS
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // bold+italic ***
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    // bold **
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // italic * or _
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(?!_)(.+?)_(?!_)/g, '<em>$1</em>')
    // underline __
    .replace(/__(.+?)__/g, '<u>$1</u>')
    // strikethrough ~~
    .replace(/~~(.+?)~~/g, '<s>$1</s>')
    // spoiler ||
    .replace(/\|\|(.+?)\|\|/g, '<span style="background:#202225;color:#202225;border-radius:3px;padding:0 2px" title="Spoiler">$1</span>')
    // inline code `
    .replace(/`([^`]+)`/g, '<code style="background:#202225;padding:1px 5px;border-radius:3px;font-size:0.9em;font-family:monospace">$1</code>')
    // code block ```
    .replace(/```[\w]*\n?([\s\S]+?)```/g, '<pre style="background:#202225;padding:8px;border-radius:4px;font-size:0.85em;overflow-x:auto;margin:4px 0"><code style="font-family:monospace">$1</code></pre>')
    // blockquote >
    .replace(/^&gt; (.+)$/gm, '<div style="border-left:3px solid #4e5058;padding-left:8px;margin:2px 0;color:#b5bac1">$1</div>')
    // newlines
    .replace(/\n/g, '<br/>')
}

function MD({ text, className, style }: { text: string; className?: string; style?: React.CSSProperties }) {
  return (
    <span
      className={className}
      style={style}
      dangerouslySetInnerHTML={{ __html: renderMd(text) }}
    />
  )
}

/* ─── Embed Preview ───────────────────────────────────────── */
function EmbedPreview({
  color, title, description, fields, footer, thumbnailUrl, imageUrl, author
}: {
  color: string; title: string; description: string
  fields: { name: string; value: string; inline: boolean }[]
  footer: string; thumbnailUrl: string; imageUrl: string; author: string
}) {
  if (!title && !description && fields.every(f => !f.name && !f.value) && !footer)
    return (
      <div className="rounded-[8px] p-4 text-[12px] text-center" style={{ background: '#1e1518', color: '#4a4448' }}>
        Embed preview will appear here
      </div>
    )
  return (
    <div className="rounded-[6px] overflow-hidden max-w-[460px]"
         style={{ background: '#2b2d31', borderLeft: `4px solid ${color}` }}>
      <div className="p-4">
        {author && <p className="text-[12px] font-semibold mb-1" style={{ color: '#b5bac1' }}>{author}</p>}
        <div className="flex gap-3">
          <div className="flex-1 min-w-0">
            {title && <p className="text-[15px] font-bold mb-1" style={{ color: '#e5e3e4' }}>{title}</p>}
            {description && (
              <MD text={description} className="text-[13px] block" style={{ color: '#b5bac1', whiteSpace: 'pre-wrap' }} />
            )}
            {fields.filter(f => f.name || f.value).length > 0 && (
              <div className="mt-3 grid grid-cols-2 gap-2">
                {fields.filter(f => f.name || f.value).map((f, i) => (
                  <div key={i} className={f.inline ? '' : 'col-span-2'}>
                    <p className="text-[12px] font-bold" style={{ color: '#e5e3e4' }}>{f.name}</p>
                    <MD text={f.value} className="text-[12px]" style={{ color: '#b5bac1' }} />
                  </div>
                ))}
              </div>
            )}
          </div>
          {thumbnailUrl && (
            <img src={thumbnailUrl} alt="" className="w-16 h-16 rounded object-cover flex-shrink-0"
                 onError={e => (e.currentTarget.style.display = 'none')} />
          )}
        </div>
        {imageUrl && (
          <img src={imageUrl} alt="" className="mt-3 w-full rounded object-cover max-h-48"
               onError={e => (e.currentTarget.style.display = 'none')} />
        )}
        {footer && (
          <p className="text-[11px] mt-3 pt-2" style={{ color: '#87898c', borderTop: '1px solid #3f4248' }}>
            {footer}
          </p>
        )}
      </div>
    </div>
  )
}

/* ─── Main Page ───────────────────────────────────────────── */
export default function DiscordPage() {
  /* tokens */
  const [tokens, setTokens]       = useState<Token[]>([])
  const [newAlias, setNewAlias]   = useState('')
  const [newToken, setNewToken]   = useState('')
  const [addOpen, setAddOpen]     = useState(false)
  const [addErr, setAddErr]       = useState('')
  const [addLoading, setAddLoad]  = useState(false)

  /* selected token */
  const [selToken, setSelToken]   = useState<Token | null>(null)
  const [botInfo, setBotInfo]     = useState<BotInfo | null>(null)
  const [guilds, setGuilds]       = useState<Guild[]>([])
  const [guildsLoading, setGL]    = useState(false)

  /* selected guild */
  const [selGuild, setSelGuild]   = useState<Guild | null>(null)
  const [channels, setChannels]   = useState<Channel[]>([])
  const [chanLoading, setChanLoad]= useState(false)

  /* selected channel */
  const [selChan, setSelChan]     = useState<Channel | null>(null)

  /* message composer */
  const [tab, setTab]             = useState<Tab>('message')
  const [msgContent, setMsgContent] = useState('')
  const [sending, setSending]     = useState(false)
  const [sendResult, setSendResult] = useState<{ ok: boolean; text: string } | null>(null)

  /* embed fields */
  const [eColor, setEColor]       = useState('#5865F2')
  const [eTitle, setETitle]       = useState('')
  const [eDesc, setEDesc]         = useState('')
  const [eFooter, setEFooter]     = useState('')
  const [eThumb, setEThumb]       = useState('')
  const [eImage, setEImage]       = useState('')
  const [eAuthor, setEAuthor]     = useState('')
  const [eFields, setEFields]     = useState([{ name: '', value: '', inline: false }])

  const resultTimer = useRef<ReturnType<typeof setTimeout>>()

  /* ── fetch tokens on mount ── */
  useEffect(() => {
    fetch('/api/discord/tokens').then(r => r.json()).then(setTokens).catch(() => {})
  }, [])

  /* ── select token → load guilds ── */
  async function selectToken(t: Token) {
    setSelToken(t); setSelGuild(null); setChannels([]); setSelChan(null)
    setBotInfo(null); setGuilds([])
    setGL(true)

    const [infoRes, guildsRes] = await Promise.all([
      proxy(t.id, 'botInfo'),
      proxy(t.id, 'guilds'),
    ])
    setBotInfo(infoRes as BotInfo)
    setGuilds(Array.isArray(guildsRes) ? guildsRes as Guild[] : [])
    setGL(false)
  }

  /* ── select guild → load channels ── */
  async function selectGuild(g: Guild) {
    setSelGuild(g); setChannels([]); setSelChan(null)
    setChanLoad(true)
    const res = await proxy(selToken!.id, 'channels', { guildId: g.id })
    setChannels(Array.isArray(res) ? res as Channel[] : [])
    setChanLoad(false)
  }

  async function proxy(tokenId: number, action: string, payload?: Record<string, unknown>) {
    const r = await fetch('/api/discord/proxy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tokenId, action, payload }),
    })
    return r.json()
  }

  /* ── add token ── */
  async function addToken() {
    if (!newAlias.trim() || !newToken.trim()) { setAddErr('Both fields required'); return }
    setAddLoad(true); setAddErr('')
    const res = await fetch('/api/discord/tokens', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alias: newAlias, token: newToken }),
    })
    const data = await res.json()
    if (!res.ok) { setAddErr(data.error || 'Failed'); setAddLoad(false); return }
    setTokens(prev => [data, ...prev])
    setNewAlias(''); setNewToken(''); setAddOpen(false)
    setAddLoad(false)
  }

  async function deleteToken(id: number, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm('Delete this token?')) return
    await fetch(`/api/discord/tokens/${id}`, { method: 'DELETE' })
    setTokens(prev => prev.filter(t => t.id !== id))
    if (selToken?.id === id) { setSelToken(null); setGuilds([]); setSelGuild(null) }
  }

  /* ── send message ── */
  async function send() {
    if (!selChan || !selToken) return
    setSending(true); setSendResult(null)

    let body: Record<string, unknown> = { channelId: selChan.id }

    if (tab === 'message') {
      if (!msgContent.trim()) { setSending(false); return }
      body.content = msgContent
    } else {
      const embed: Record<string, unknown> = { color: parseInt(eColor.replace('#',''), 16) }
      if (eAuthor) embed.author = { name: eAuthor }
      if (eTitle)  embed.title = eTitle
      if (eDesc)   embed.description = eDesc
      if (eThumb)  embed.thumbnail = { url: eThumb }
      if (eImage)  embed.image = { url: eImage }
      if (eFooter) embed.footer = { text: eFooter }
      const validFields = eFields.filter(f => f.name || f.value)
      if (validFields.length) embed.fields = validFields
      body.embeds = [embed]
      if (msgContent.trim()) body.content = msgContent
    }

    const res = await fetch('/api/discord/proxy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tokenId: selToken.id, action: 'send', payload: body }),
    })
    const data = await res.json()

    if (res.ok) {
      setSendResult({ ok: true, text: 'Message sent successfully!' })
      if (tab === 'message') setMsgContent('')
    } else {
      setSendResult({ ok: false, text: data.error || JSON.stringify(data.detail) || 'Failed to send' })
    }
    setSending(false)

    clearTimeout(resultTimer.current)
    resultTimer.current = setTimeout(() => setSendResult(null), 4000)
  }

  /* ── channel grouping ── */
  const categories = channels.filter(c => c.type === 4)
  const textChannels = channels.filter(c => c.type === 0)
  const voiceChannels = channels.filter(c => c.type === 2)

  function channelsInCategory(catId: string | null) {
    return channels.filter(c => c.type === 0 && c.parent_id === catId)
  }

  /* ── formatting helpers ── */
  function insertFmt(tag: string) {
    const wrapped = `${tag}text${tag}`
    setMsgContent(prev => prev + wrapped)
  }

  /* ─────────────────────────── RENDER ─────────────────────── */
  return (
    <div className="flex h-full" style={{ minHeight: '100vh' }}>

      {/* ── Left: Token list ── */}
      <div className="w-[220px] flex flex-col border-r shrink-0"
           style={{ background: '#0f0b0c', borderColor: '#252025' }}>

        <div className="flex items-center justify-between px-4 py-4 border-b" style={{ borderColor: '#252025' }}>
          <span className="text-[12px] font-bold uppercase tracking-widest" style={{ color: '#5d585c' }}>
            Tokens
          </span>
          <button onClick={() => setAddOpen(o => !o)}
                  className="w-6 h-6 rounded-[5px] flex items-center justify-center text-[16px] transition-colors"
                  style={{ background: addOpen ? 'rgba(220,38,37,0.15)' : '#1e1518', color: addOpen ? '#dc2625' : '#5d585c' }}
                  title="Add token">
            {addOpen ? '×' : '+'}
          </button>
        </div>

        {/* Add token form */}
        {addOpen && (
          <div className="p-3 border-b flex flex-col gap-2" style={{ borderColor: '#252025', background: '#120d10' }}>
            <input value={newAlias} onChange={e => setNewAlias(e.target.value)}
                   placeholder="Alias (e.g. MyBot)"
                   className="h-[34px] rounded-[6px] px-2.5 text-[12px] outline-none w-full"
                   style={{ background: '#1e1518', border: '1px solid #352c2f', color: '#c5c0c2' }}
                   onFocus={e => (e.target.style.borderColor = '#5a4f52')}
                   onBlur={e  => (e.target.style.borderColor = '#352c2f')} />
            <input value={newToken} onChange={e => setNewToken(e.target.value)}
                   placeholder="Bot token"
                   type="password"
                   className="h-[34px] rounded-[6px] px-2.5 text-[12px] font-mono outline-none w-full"
                   style={{ background: '#1e1518', border: '1px solid #352c2f', color: '#c5c0c2' }}
                   onFocus={e => (e.target.style.borderColor = '#5a4f52')}
                   onBlur={e  => (e.target.style.borderColor = '#352c2f')} />
            {addErr && <p className="text-[11px]" style={{ color: '#dc2625' }}>{addErr}</p>}
            <button onClick={addToken} disabled={addLoading}
                    className="h-[30px] rounded-[6px] text-[12px] font-bold text-white transition-all disabled:opacity-50"
                    style={{ background: '#dc2625' }}>
              {addLoading ? 'Saving…' : 'Save Token'}
            </button>
          </div>
        )}

        {/* Token entries */}
        <div className="flex-1 overflow-y-auto py-2">
          {tokens.length === 0 && (
            <p className="text-[12px] text-center py-6" style={{ color: '#3a3537' }}>No tokens yet</p>
          )}
          {tokens.map(t => (
            <div key={t.id}
                 onClick={() => selectToken(t)}
                 className="group flex items-center justify-between px-3 py-2.5 mx-2 rounded-[7px] cursor-pointer transition-colors"
                 style={{
                   background: selToken?.id === t.id ? 'rgba(220,38,37,0.08)' : 'transparent',
                   borderLeft: selToken?.id === t.id ? '2px solid #dc2625' : '2px solid transparent',
                 }}>
              <div className="min-w-0">
                <p className="text-[13px] font-medium truncate"
                   style={{ color: selToken?.id === t.id ? '#e5e3e4' : '#868283' }}>
                  {t.alias}
                </p>
                {t.last_used && (
                  <p className="text-[10px]" style={{ color: '#3a3537' }}>
                    {new Date(t.last_used).toLocaleDateString()}
                  </p>
                )}
              </div>
              <button onClick={e => deleteToken(t.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-[16px] transition-opacity px-1"
                      style={{ color: '#5d585c' }}
                      onMouseEnter={e => (e.currentTarget.style.color = '#dc2625')}
                      onMouseLeave={e => (e.currentTarget.style.color = '#5d585c')}>
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Middle: Servers & Channels ── */}
      <div className="w-[200px] flex flex-col border-r shrink-0"
           style={{ background: '#0d0a0e', borderColor: '#252025' }}>

        {/* Bot info */}
        {selToken && (
          <div className="p-3 border-b flex items-center gap-2" style={{ borderColor: '#252025' }}>
            {botInfo ? (
              <>
                <img src={botAvatar(botInfo)} alt="" className="w-7 h-7 rounded-full" />
                <div className="min-w-0">
                  <p className="text-[12px] font-semibold truncate" style={{ color: '#e5e3e4' }}>
                    {botInfo.username}
                  </p>
                  <Pill>BOT</Pill>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full animate-pulse" style={{ background: '#252025' }} />
                <div className="h-3 w-20 rounded animate-pulse" style={{ background: '#252025' }} />
              </div>
            )}
          </div>
        )}

        {/* Servers */}
        {selToken && (
          <>
            <div className="px-3 py-2 border-b" style={{ borderColor: '#252025' }}>
              <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#3a3537' }}>
                Servers
              </span>
            </div>
            <div className="flex-1 overflow-y-auto py-1" style={{ maxHeight: selGuild ? '180px' : undefined }}>
              {guildsLoading ? (
                <div className="flex flex-col gap-1 p-2">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-8 rounded-[6px] animate-pulse" style={{ background: '#1a1518' }} />
                  ))}
                </div>
              ) : guilds.map(g => (
                <div key={g.id} onClick={() => selectGuild(g)}
                     className="flex items-center gap-2 px-2 py-1.5 mx-1 rounded-[6px] cursor-pointer transition-colors"
                     style={{
                       background: selGuild?.id === g.id ? 'rgba(220,38,37,0.08)' : 'transparent',
                     }}>
                  {guildIcon(g) ? (
                    <img src={guildIcon(g)!} alt="" className="w-6 h-6 rounded-full flex-shrink-0" />
                  ) : (
                    <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-[9px] font-bold"
                         style={{ background: '#252025', color: '#868283' }}>
                      {g.name.slice(0,2).toUpperCase()}
                    </div>
                  )}
                  <span className="text-[12px] truncate"
                        style={{ color: selGuild?.id === g.id ? '#e5e3e4' : '#5d585c' }}>
                    {g.name}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Channels */}
        {selGuild && (
          <>
            <div className="px-3 py-2 border-t border-b" style={{ borderColor: '#252025' }}>
              <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#3a3537' }}>
                Channels
              </span>
            </div>
            <div className="flex-1 overflow-y-auto py-1">
              {chanLoading ? (
                <div className="flex flex-col gap-1 p-2">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-7 rounded animate-pulse" style={{ background: '#1a1518' }} />
                  ))}
                </div>
              ) : (
                <>
                  {/* Uncategorized text channels */}
                  {channelsInCategory(null).map(c => (
                    <ChannelRow key={c.id} c={c} selected={selChan?.id === c.id} onSelect={setSelChan} />
                  ))}
                  {/* Categories */}
                  {categories.map(cat => (
                    <div key={cat.id}>
                      <p className="text-[10px] font-bold uppercase tracking-widest px-3 pt-3 pb-1"
                         style={{ color: '#3a3537' }}>
                        {cat.name}
                      </p>
                      {channelsInCategory(cat.id).map(c => (
                        <ChannelRow key={c.id} c={c} selected={selChan?.id === c.id} onSelect={setSelChan} />
                      ))}
                    </div>
                  ))}
                  {/* Voice channels */}
                  {voiceChannels.length > 0 && (
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest px-3 pt-3 pb-1"
                         style={{ color: '#3a3537' }}>
                        Voice
                      </p>
                      {voiceChannels.map(c => (
                        <ChannelRow key={c.id} c={c} selected={false} onSelect={() => {}} voice />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        )}

        {!selToken && (
          <div className="flex-1 flex items-center justify-center p-4">
            <p className="text-[12px] text-center" style={{ color: '#3a3537' }}>
              Select a token to get started
            </p>
          </div>
        )}
      </div>

      {/* ── Right: Composer ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!selChan ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <div className="text-[40px] opacity-20">
              <DiscordIcon />
            </div>
            <p className="text-[14px]" style={{ color: '#3a3537' }}>
              {!selToken ? 'Select a token from the left panel'
               : !selGuild ? 'Choose a server'
               : 'Select a channel to start messaging'}
            </p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center gap-3 px-6 py-4 border-b shrink-0"
                 style={{ borderColor: '#252025', background: '#0f0b0c' }}>
              <span style={{ color: '#5d585c' }}>#</span>
              <div>
                <p className="text-[14px] font-semibold" style={{ color: '#e5e3e4' }}>{selChan.name}</p>
                <p className="text-[11px]" style={{ color: '#3a3537' }}>
                  {selGuild?.name} · {selToken?.alias}
                </p>
              </div>
              <div className="ml-auto">
                <Pill color="#5865F2">Discord</Pill>
              </div>
            </div>

            {/* Composer area */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5">

              {/* Tab bar */}
              <div className="flex gap-0 rounded-[9px] p-0.5 self-start"
                   style={{ background: '#161014', border: '1px solid #252025' }}>
                {(['message', 'embed'] as Tab[]).map(t => (
                  <button key={t} onClick={() => setTab(t)}
                          className="px-5 py-1.5 rounded-[7px] text-[12px] font-medium capitalize transition-all"
                          style={{
                            background: tab === t ? '#dc2625' : 'transparent',
                            color: tab === t ? '#fff' : '#5d585c',
                            boxShadow: tab === t ? '0 0 12px rgba(220,38,37,0.3)' : 'none',
                          }}>
                    {t === 'message' ? 'Message' : 'Embed'}
                  </button>
                ))}
              </div>

              {/* Formatting toolbar */}
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[11px] mr-1" style={{ color: '#3a3537' }}>Format:</span>
                {[
                  { label: 'B',     tag: '**',  title: 'Bold' },
                  { label: 'I',     tag: '*',   title: 'Italic' },
                  { label: 'U',     tag: '__',  title: 'Underline' },
                  { label: 'S',     tag: '~~',  title: 'Strikethrough' },
                  { label: '`',     tag: '`',   title: 'Inline code' },
                  { label: '```',   tag: '```', title: 'Code block' },
                  { label: '>',     tag: '> ',  title: 'Blockquote (prefix)' },
                  { label: '||',    tag: '||',  title: 'Spoiler' },
                ].map(({ label, tag, title }) => (
                  <button key={tag}
                          onClick={() => {
                            if (tag === '> ') setMsgContent(p => `> ${p}`)
                            else insertFmt(tag)
                          }}
                          title={title}
                          className="px-2 py-1 rounded-[5px] text-[11px] font-bold transition-colors"
                          style={{ background: '#1e1518', color: '#868283', border: '1px solid #252025' }}
                          onMouseEnter={e => { e.currentTarget.style.background = '#2a2024'; e.currentTarget.style.color = '#e5e3e4' }}
                          onMouseLeave={e => { e.currentTarget.style.background = '#1e1518'; e.currentTarget.style.color = '#868283' }}>
                    {label}
                  </button>
                ))}
              </div>

              {/* Message content (always shown) */}
              <Input
                label={tab === 'embed' ? 'Message Content (optional)' : 'Message Content'}
                value={msgContent}
                onChange={setMsgContent}
                placeholder={tab === 'message' ? 'Type your message… (supports **bold**, *italic*, etc.)' : 'Optional message above the embed'}
                multiline
                rows={tab === 'message' ? 5 : 2}
              />

              {/* Embed fields */}
              {tab === 'embed' && (
                <div className="flex flex-col gap-4 rounded-[12px] p-5"
                     style={{ background: '#120d10', border: '1px solid #252025' }}>
                  <p className="text-[12px] font-bold uppercase tracking-widest" style={{ color: '#5d585c' }}>
                    Embed Builder
                  </p>

                  <ColorSwatch value={eColor} onChange={setEColor} />

                  <div className="grid grid-cols-2 gap-3">
                    <Input label="Author" value={eAuthor} onChange={setEAuthor} placeholder="Author name" />
                    <Input label="Title"  value={eTitle}  onChange={setETitle}  placeholder="Embed title" />
                  </div>

                  <Input label="Description" value={eDesc} onChange={setEDesc}
                         placeholder="Embed body text (supports markdown)" multiline rows={3} />

                  <div className="grid grid-cols-2 gap-3">
                    <Input label="Thumbnail URL" value={eThumb} onChange={setEThumb} placeholder="https://…" />
                    <Input label="Image URL"      value={eImage} onChange={setEImage} placeholder="https://…" />
                  </div>

                  <Input label="Footer" value={eFooter} onChange={setEFooter} placeholder="Footer text" />

                  {/* Fields */}
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <label className="text-[12px] font-medium" style={{ color: '#888485' }}>Fields</label>
                      <button onClick={() => setEFields(f => [...f, { name: '', value: '', inline: false }])}
                              className="text-[11px] px-2 py-0.5 rounded transition-colors"
                              style={{ background: '#1e1518', color: '#5d585c', border: '1px solid #252025' }}
                              onMouseEnter={e => (e.currentTarget.style.color = '#dc2625')}
                              onMouseLeave={e => (e.currentTarget.style.color = '#5d585c')}>
                        + Add Field
                      </button>
                    </div>
                    {eFields.map((f, i) => (
                      <div key={i} className="flex gap-2 items-start rounded-[8px] p-3"
                           style={{ background: '#0f0b0c', border: '1px solid #1e1518' }}>
                        <div className="flex-1 grid grid-cols-2 gap-2">
                          <input value={f.name} onChange={e => setEFields(fs => fs.map((x,j) => j===i ? {...x,name:e.target.value} : x))}
                                 placeholder="Name"
                                 className="h-[34px] rounded-[6px] px-2.5 text-[12px] outline-none"
                                 style={{ background: '#1e1518', border: '1px solid #252025', color: '#c5c0c2' }} />
                          <input value={f.value} onChange={e => setEFields(fs => fs.map((x,j) => j===i ? {...x,value:e.target.value} : x))}
                                 placeholder="Value"
                                 className="h-[34px] rounded-[6px] px-2.5 text-[12px] outline-none"
                                 style={{ background: '#1e1518', border: '1px solid #252025', color: '#c5c0c2' }} />
                        </div>
                        <label className="flex items-center gap-1 text-[11px] pt-2 cursor-pointer"
                               style={{ color: '#5d585c' }}>
                          <input type="checkbox" checked={f.inline}
                                 onChange={e => setEFields(fs => fs.map((x,j) => j===i ? {...x,inline:e.target.checked} : x))}
                                 className="w-3 h-3" />
                          Inline
                        </label>
                        {eFields.length > 1 && (
                          <button onClick={() => setEFields(fs => fs.filter((_,j) => j !== i))}
                                  className="text-[14px] pt-1" style={{ color: '#3a3537' }}
                                  onMouseEnter={e => (e.currentTarget.style.color = '#dc2625')}
                                  onMouseLeave={e => (e.currentTarget.style.color = '#3a3537')}>×</button>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Embed preview */}
                  <div>
                    <p className="text-[11px] uppercase tracking-widest mb-2" style={{ color: '#3a3537' }}>Preview</p>
                    <EmbedPreview
                      color={eColor} title={eTitle} description={eDesc}
                      fields={eFields} footer={eFooter} thumbnailUrl={eThumb}
                      imageUrl={eImage} author={eAuthor}
                    />
                  </div>
                </div>
              )}

              {/* Send */}
              <div className="flex items-center gap-3 mt-auto">
                <button onClick={send} disabled={sending || (!msgContent.trim() && tab === 'message')}
                        className="h-[42px] px-8 rounded-[9px] font-bold text-[14px] text-white transition-all disabled:opacity-40"
                        style={{
                          background: '#dc2625',
                          boxShadow: '0 0 20px rgba(220,38,37,0.35)',
                        }}
                        onMouseEnter={e => { if (!sending) e.currentTarget.style.background = '#e83433' }}
                        onMouseLeave={e => { e.currentTarget.style.background = '#dc2625' }}>
                  {sending ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      Sending…
                    </span>
                  ) : 'Send Message'}
                </button>

                {sendResult && (
                  <p className="text-[13px] font-medium transition-opacity"
                     style={{ color: sendResult.ok ? '#4ade80' : '#dc2625' }}>
                    {sendResult.ok ? '✓ ' : '✗ '}{sendResult.text}
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function ChannelRow({ c, selected, onSelect, voice = false }: {
  c: Channel; selected: boolean; onSelect: (c: Channel) => void; voice?: boolean
}) {
  return (
    <div onClick={() => !voice && onSelect(c)}
         className="flex items-center gap-1.5 px-3 py-1.5 mx-1 rounded-[5px] transition-colors"
         style={{
           cursor: voice ? 'default' : 'pointer',
           background: selected ? 'rgba(220,38,37,0.08)' : 'transparent',
           color: selected ? '#e5e3e4' : voice ? '#3a3537' : '#5d585c',
         }}
         onMouseEnter={e => { if (!voice && !selected) e.currentTarget.style.color = '#868283' }}
         onMouseLeave={e => { if (!voice && !selected) e.currentTarget.style.color = '#5d585c' }}>
      <span className="text-[13px]">{voice ? '🔊' : '#'}</span>
      <span className="text-[12px] truncate">{c.name}</span>
    </div>
  )
}

function DiscordIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 71 55" fill="currentColor">
      <path d="M60.1 4.9A58.5 58.5 0 0 0 45.7.4a.2.2 0 0 0-.2.1 40.8 40.8 0 0 0-1.8 3.7 54 54 0 0 0-16.2 0A37.5 37.5 0 0 0 25.6.5a.2.2 0 0 0-.2-.1A58.4 58.4 0 0 0 11 4.9a.2.2 0 0 0-.1.1C1.6 18.9-1 32.5.3 46a.2.2 0 0 0 .1.1 58.8 58.8 0 0 0 17.7 9 .2.2 0 0 0 .2-.1 42 42 0 0 0 3.6-5.9.2.2 0 0 0-.1-.3 38.7 38.7 0 0 1-5.5-2.6.2.2 0 0 1 0-.4 27.9 27.9 0 0 0 1.1-.9.2.2 0 0 1 .2 0c11.5 5.3 24 5.3 35.4 0a.2.2 0 0 1 .2 0l1.1.9a.2.2 0 0 1 0 .4 36.3 36.3 0 0 1-5.6 2.6.2.2 0 0 0-.1.3 47.2 47.2 0 0 0 3.6 5.9.2.2 0 0 0 .2.1 58.6 58.6 0 0 0 17.8-9 .2.2 0 0 0 .1-.1C72.9 30.4 69.4 17 60.2 5a.2.2 0 0 0-.1-.1zM23.7 37.8c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2c3.6 0 6.5 3.3 6.4 7.2 0 4-2.8 7.2-6.4 7.2zm23.6 0c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2c3.6 0 6.5 3.3 6.4 7.2 0 4-2.8 7.2-6.4 7.2z"/>
    </svg>
  )
}