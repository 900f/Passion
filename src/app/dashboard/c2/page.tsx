// app/dashboard/c2/page.tsx
'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import CommandInterface from './CommandInterface'
import CommandResults from './CommandResults'

interface Client {
  id: number
  hwid: string
  alias: string | null
  ip_address: string
  country: string
  city: string
  is_admin: boolean
  status: 'active' | 'inactive' | 'offline'
  last_seen: string
  last_seen_ago: string
  created_at: string
  system_info?: any
  tags: string[]
}

export default function C2Dashboard() {
  const [clients, setClients] = useState<Client[]>([])
  const [selectedClient, setSelectedClient] = useState<Client | null>(null)
  const [commands, setCommands] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'offline'>('all')
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0, offline: 0 })
  const [autoRefresh, setAutoRefresh] = useState(true)
  const refreshInterval = useRef<NodeJS.Timeout>()

  const fetchClients = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.set('status', statusFilter)
      if (search) params.set('q', search)
      
      const res = await fetch(`/api/c2/clients?${params}`)
      const data = await res.json()
      setClients(data)
      
      // Calculate stats
      const newStats = data.reduce((acc: any, c: Client) => {
        acc.total++
        acc[c.status]++
        return acc
      }, { total: 0, active: 0, inactive: 0, offline: 0 })
      setStats(newStats)
    } catch (error) {
      console.error('Failed to fetch clients:', error)
    }
    setLoading(false)
  }, [search, statusFilter])

  useEffect(() => {
    fetchClients()
    
    if (autoRefresh) {
      refreshInterval.current = setInterval(fetchClients, 3000)
    }
    
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current)
      }
    }
  }, [fetchClients, autoRefresh])

  // Listen for command results via SSE
  useEffect(() => {
    if (!selectedClient) return
    
    const eventSource = new EventSource(`/api/c2/stream/${selectedClient.id}`)
    
    eventSource.onmessage = (event) => {
      const result = JSON.parse(event.data)
      setCommands(prev => [result, ...prev].slice(0, 50))
    }
    
    return () => eventSource.close()
  }, [selectedClient])

  const filteredClients = clients

  return (
    <div className="flex h-screen" style={{ background: '#0f0b0c' }}>
      {/* Client List Sidebar */}
      <div 
        className="w-96 border-r flex flex-col shrink-0"
        style={{ background: '#0f0b0c', borderColor: '#352f31' }}
      >
        {/* Header with stats */}
        <div className="p-4 border-b" style={{ borderColor: '#352f31' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold" style={{ color: '#e5e3e4' }}>
              C2 Clients
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
                  autoRefresh ? 'text-green-500' : 'text-gray-500'
                }`}
                style={{ background: '#1a1218' }}
                title={autoRefresh ? 'Auto-refresh on' : 'Auto-refresh off'}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                </svg>
              </button>
              <button
                onClick={fetchClients}
                className="w-8 h-8 rounded flex items-center justify-center"
                style={{ background: '#1a1218', color: '#868283' }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 4v6h6M23 20v-6h-6M3.51 15a9 9 0 0 0 14.85 3.36L23 14M1 10l4.64-4.36A9 9 0 0 1 20.49 9"/>
                </svg>
              </button>
            </div>
          </div>
          
          {/* Stats cards */}
          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="p-2 rounded text-center" style={{ background: '#1a1218' }}>
              <div className="text-xs" style={{ color: '#5d585c' }}>Total</div>
              <div className="text-lg font-bold" style={{ color: '#e5e3e4' }}>{stats.total}</div>
            </div>
            <div className="p-2 rounded text-center" style={{ background: '#16a34a18' }}>
              <div className="text-xs" style={{ color: '#5d585c' }}>Active</div>
              <div className="text-lg font-bold text-green-500">{stats.active}</div>
            </div>
            <div className="p-2 rounded text-center" style={{ background: '#eab30818' }}>
              <div className="text-xs" style={{ color: '#5d585c' }}>Inactive</div>
              <div className="text-lg font-bold text-yellow-500">{stats.inactive}</div>
            </div>
            <div className="p-2 rounded text-center" style={{ background: '#dc262518' }}>
              <div className="text-xs" style={{ color: '#5d585c' }}>Offline</div>
              <div className="text-lg font-bold text-red-500">{stats.offline}</div>
            </div>
          </div>

          {/* Search and filters */}
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Search by HWID or IP..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full p-2.5 rounded text-sm outline-none transition-colors"
              style={{ 
                background: '#2a2024', 
                border: '1px solid #352f31', 
                color: '#e5e3e4' 
              }}
              onFocus={(e) => e.target.style.borderColor = '#dc2625'}
              onBlur={(e) => e.target.style.borderColor = '#352f31'}
            />
            
            <div className="flex gap-1">
              {(['all', 'active', 'inactive', 'offline'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setStatusFilter(filter)}
                  className={`flex-1 py-1.5 px-2 rounded text-xs font-medium capitalize transition-colors ${
                    statusFilter === filter 
                      ? filter === 'active' ? 'bg-green-500/20 text-green-500'
                      : filter === 'inactive' ? 'bg-yellow-500/20 text-yellow-500'
                      : filter === 'offline' ? 'bg-red-500/20 text-red-500'
                      : 'bg-white/10 text-white'
                      : 'text-gray-500 hover:bg-white/5'
                  }`}
                  style={{ 
                    background: statusFilter === filter ? undefined : '#1a1218',
                    border: '1px solid #352f31'
                  }}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Client list */}
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {loading ? (
            <div className="text-center py-8" style={{ color: '#5d585c' }}>
              Loading clients...
            </div>
          ) : filteredClients.length === 0 ? (
            <div className="text-center py-8" style={{ color: '#5d585c' }}>
              No clients found
            </div>
          ) : (
            filteredClients.map((client) => (
              <div
                key={client.id}
                onClick={() => setSelectedClient(client)}
                className="p-3 rounded-lg cursor-pointer transition-all hover:scale-[1.02]"
                style={{
                  background: selectedClient?.id === client.id 
                    ? 'linear-gradient(135deg, #dc262520 0%, #1a1218 100%)'
                    : '#1a1218',
                  border: selectedClient?.id === client.id 
                    ? '1px solid #dc2625'
                    : '1px solid #352f31',
                  boxShadow: selectedClient?.id === client.id 
                    ? '0 0 20px rgba(220,38,37,0.2)'
                    : 'none'
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      client.status === 'active' ? 'bg-green-500 animate-pulse' :
                      client.status === 'inactive' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`} />
                    <span className="font-mono text-sm font-bold" style={{ color: '#e5e3e4' }}>
                      {client.hwid.slice(0, 12)}...
                    </span>
                  </div>
                  {client.is_admin && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-500">
                      ADMIN
                    </span>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                  <div style={{ color: '#5d585c' }}>
                    IP: <span style={{ color: '#868283' }}>{client.ip_address || 'Unknown'}</span>
                  </div>
                  <div style={{ color: '#5d585c' }}>
                    Last: <span style={{ color: '#868283' }}>{client.last_seen_ago}</span>
                  </div>
                  {client.country && (
                    <div style={{ color: '#5d585c' }} className="col-span-2">
                      📍 {client.country}{client.city ? `, ${client.city}` : ''}
                    </div>
                  )}
                </div>

                {client.tags && client.tags.length > 0 && (
                  <div className="flex gap-1 mt-1">
                    {client.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-1.5 py-0.5 rounded"
                        style={{ background: '#2a2024', color: '#5d585c' }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="p-3 border-t text-xs text-center" style={{ borderColor: '#352f31', color: '#3a3537' }}>
          {stats.active} active · Polling every 3s
          {autoRefresh ? ' · Live' : ''}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {selectedClient ? (
          <div className="p-6 space-y-6">
            {/* Client Info Header */}
            <div
              className="p-6 rounded-xl"
              style={{ 
                background: 'linear-gradient(135deg, #1a1218 0%, #0f0b0c 100%)',
                border: '1px solid #352f31',
                boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
              }}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-2xl font-bold mb-2" style={{ color: '#e5e3e4' }}>
                    {selectedClient.alias || selectedClient.hwid}
                  </h1>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      selectedClient.status === 'active' ? 'bg-green-500/20 text-green-500' :
                      selectedClient.status === 'inactive' ? 'bg-yellow-500/20 text-yellow-500' :
                      'bg-red-500/20 text-red-500'
                    }`}>
                      {selectedClient.status.toUpperCase()}
                    </span>
                    {selectedClient.is_admin && (
                      <span className="px-2 py-1 rounded text-xs font-bold bg-purple-500/20 text-purple-500">
                        ADMIN
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-4xl mb-1">
                    {selectedClient.country?.slice(0,2).toLowerCase() || '🌐'}
                  </div>
                  <div className="text-xs" style={{ color: '#3a3537' }}>
                    Client ID: {selectedClient.id}
                  </div>
                </div>
              </div>

              {/* System Info Grid */}
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="p-3 rounded" style={{ background: '#1a1218' }}>
                  <div className="text-xs mb-1" style={{ color: '#5d585c' }}>OS</div>
                  <div className="font-medium truncate" title={selectedClient.system_info?.os}>
                    {selectedClient.system_info?.os?.slice(0,30) || 'Unknown'}
                  </div>
                </div>
                <div className="p-3 rounded" style={{ background: '#1a1218' }}>
                  <div className="text-xs mb-1" style={{ color: '#5d585c' }}>CPU</div>
                  <div className="font-medium">{selectedClient.system_info?.cpu_percent || 0}%</div>
                </div>
                <div className="p-3 rounded" style={{ background: '#1a1218' }}>
                  <div className="text-xs mb-1" style={{ color: '#5d585c' }}>RAM</div>
                  <div className="font-medium">{selectedClient.system_info?.ram_percent || 0}%</div>
                </div>
                <div className="p-3 rounded" style={{ background: '#1a1218' }}>
                  <div className="text-xs mb-1" style={{ color: '#5d585c' }}>Uptime</div>
                  <div className="font-medium">{selectedClient.system_info?.uptime_str || 'Unknown'}</div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-5 gap-2 mt-4">
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-500">{selectedClient.system_info?.processes || '?'}</div>
                  <div className="text-[10px]" style={{ color: '#5d585c' }}>Processes</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-500">
                    {Object.keys(selectedClient.system_info?.network_interfaces || {}).length}
                  </div>
                  <div className="text-[10px]" style={{ color: '#5d585c' }}>Interfaces</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-yellow-500">
                    {selectedClient.system_info?.cpu_count || '?'}
                  </div>
                  <div className="text-[10px]" style={{ color: '#5d585c' }}>CPU Cores</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-purple-500">
                    {selectedClient.system_info?.ram_total || '?'}GB
                  </div>
                  <div className="text-[10px]" style={{ color: '#5d585c' }}>RAM Total</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-orange-500">
                    {selectedClient.system_info?.disk_usage ? Object.keys(selectedClient.system_info.disk_usage).length : '?'}
                  </div>
                  <div className="text-[10px]" style={{ color: '#5d585c' }}>Drives</div>
                </div>
              </div>
            </div>

            {/* Command Interface */}
            <CommandInterface
              clientId={selectedClient.id}
              onCommandSent={() => {
                // Refresh commands
              }}
            />

            {/* Command Results */}
            <div className="mt-6">
              <h3 className="text-lg font-bold mb-4" style={{ color: '#e5e3e4' }}>
                Command Results
              </h3>
              <CommandResults 
                results={commands} 
                clientId={selectedClient.id}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-8xl mb-6 opacity-20">🎯</div>
              <h2 className="text-2xl font-bold mb-3" style={{ color: '#e5e3e4' }}>
                Select a Client
              </h2>
              <p className="text-sm" style={{ color: '#5d585c' }}>
                Choose a client from the sidebar to start issuing commands
              </p>
              {stats.total === 0 && (
                <div className="mt-6 p-4 rounded-lg" style={{ background: '#1a1218' }}>
                  <p className="text-sm" style={{ color: '#868283' }}>
                    No clients connected yet. Make sure your C2 client is running.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}