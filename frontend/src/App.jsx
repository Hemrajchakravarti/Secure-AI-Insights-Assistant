import { useState, useRef, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { sendChat, fetchExamples, fetchAnalytics } from './api/client'

const PALETTE = ['#7c3aed','#0d9488','#dc2626','#d97706','#2563eb','#059669','#db2777']

const css = {
  app:       { display:'flex', height:'100vh', overflow:'hidden', background:'#0f1117', color:'#e2e8f0',
               fontFamily:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif', fontSize:14 },
  // Left sidebar
  sidebar:   { width:264, minWidth:264, background:'#131620', borderRight:'1px solid #1e2235',
               display:'flex', flexDirection:'column', overflow:'hidden' },
  sideLogo:  { padding:'18px 16px 12px', borderBottom:'1px solid #1e2235' },
  sideTitle: { fontSize:15, fontWeight:700, color:'#a78bfa', letterSpacing:'-0.01em' },
  sideSub:   { fontSize:11, color:'#4b5563', marginTop:3 },
  sideSection:{ padding:'14px 12px 8px' },
  sideLabel: { fontSize:10, fontWeight:700, color:'#374151', letterSpacing:'0.08em',
               textTransform:'uppercase', marginBottom:8, paddingLeft:4 },
  pill:      { background:'#1a1e30', border:'1px solid #252a40', borderRadius:8,
               padding:'7px 11px', cursor:'pointer', fontSize:12, color:'#a78bfa',
               marginBottom:6, lineHeight:1.4, transition:'background .15s' },
  // Centre chat
  centre:    { flex:1, display:'flex', flexDirection:'column', overflow:'hidden', minWidth:0 },
  topBar:    { padding:'12px 20px', borderBottom:'1px solid #1e2235', display:'flex',
               alignItems:'center', justifyContent:'space-between' },
  topTitle:  { fontSize:13, fontWeight:600, color:'#6b7280' },
  chatScroll:{ flex:1, overflowY:'auto', padding:'20px', display:'flex', flexDirection:'column', gap:14 },
  userBubble:{ alignSelf:'flex-end', background:'#1e1b4b', border:'1px solid #312e81',
               borderRadius:'14px 14px 3px 14px', padding:'10px 14px',
               maxWidth:'68%', lineHeight:1.6 },
  aiBubble:  { alignSelf:'flex-start', background:'#131620', border:'1px solid #1e2235',
               borderRadius:'3px 14px 14px 14px', padding:'13px 16px',
               maxWidth:'84%', lineHeight:1.7, whiteSpace:'pre-wrap' },
  srcRow:    { marginTop:10, paddingTop:8, borderTop:'1px solid #1e2235',
               display:'flex', flexWrap:'wrap', gap:4, alignItems:'center' },
  srcLabel:  { fontSize:11, color:'#4b5563' },
  srcBadge:  { background:'#0d948818', color:'#2dd4bf', border:'1px solid #0d948840',
               borderRadius:4, padding:'1px 7px', fontSize:11, fontWeight:600 },
  thinking:  { alignSelf:'flex-start', color:'#7c3aed', fontSize:12,
               fontStyle:'italic', display:'flex', alignItems:'center', gap:6 },
  inputRow:  { padding:'12px 20px 16px', borderTop:'1px solid #1e2235',
               display:'flex', gap:10 },
  input:     { flex:1, background:'#131620', border:'1px solid #1e2235', borderRadius:10,
               padding:'10px 14px', color:'#e2e8f0', fontSize:14, outline:'none',
               transition:'border-color .15s' },
  sendBtn:   { background:'#7c3aed', color:'#fff', border:'none', borderRadius:10,
               padding:'10px 20px', cursor:'pointer', fontWeight:700, fontSize:13,
               transition:'background .15s' },
  // Tool trace
  traceWrap: { marginTop:10, border:'1px solid #1e2235', borderRadius:8, overflow:'hidden' },
  traceHead: { padding:'7px 12px', background:'#0f1117', fontSize:12, color:'#6b7280',
               display:'flex', justifyContent:'space-between', cursor:'pointer',
               userSelect:'none' },
  traceRow:  { padding:'8px 12px', borderTop:'1px solid #1a1e30', fontSize:12 },
  toolBadge: { display:'inline-block', background:'#7c3aed18', color:'#c4b5fd',
               border:'1px solid #7c3aed30', borderRadius:4, padding:'1px 7px',
               marginRight:6, fontSize:11, fontWeight:700 },
  monoText:  { fontFamily:'monospace', fontSize:11, color:'#374151', marginTop:3 },
  // Right panel
  right:     { width:300, minWidth:300, background:'#131620', borderLeft:'1px solid #1e2235',
               display:'flex', flexDirection:'column', overflow:'hidden' },
  tabBar:    { display:'flex', borderBottom:'1px solid #1e2235' },
  tab:       { flex:1, padding:'11px 0', fontSize:12, fontWeight:700, cursor:'pointer',
               textAlign:'center', border:'none', background:'transparent', transition:'color .15s' },
  panelBody: { flex:1, overflowY:'auto', padding:'12px' },
  chartCard: { background:'#0f1117', border:'1px solid #1e2235', borderRadius:10,
               padding:'12px 14px', marginBottom:12 },
  chartTitle:{ fontSize:10, fontWeight:700, color:'#4b5563', letterSpacing:'0.07em',
               textTransform:'uppercase', marginBottom:10 },
  histRow:   { padding:'9px 10px', borderBottom:'1px solid #1a1e30', cursor:'pointer',
               borderRadius:6, marginBottom:4 },
  histQ:     { fontSize:12, color:'#c9d1d9', marginBottom:4 },
  histMeta:  { display:'flex', justifyContent:'space-between', alignItems:'center' },
  emptyState:{ textAlign:'center', padding:'48px 16px', color:'#374151' },
}

export default function App() {
  const [messages,   setMessages]   = useState([])
  const [input,      setInput]      = useState('')
  const [loading,    setLoading]    = useState(false)
  const [examples,   setExamples]   = useState([])
  const [history,    setHistory]    = useState([])
  const [rightTab,   setRightTab]   = useState('charts')
  const [openTraces, setOpenTraces] = useState({})
  const [chartData,  setChartData]  = useState({})
  const [backendOk,  setBackendOk]  = useState(null)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:'smooth' }) }, [messages])

  useEffect(() => {
    // Check backend health
    fetch('/health').then(r => r.ok ? setBackendOk(true) : setBackendOk(false)).catch(() => setBackendOk(false))

    fetchExamples().then(d => setExamples(d.examples || [])).catch(() => {})

    Promise.all([
      fetchAnalytics('genre-performance'),
      fetchAnalytics('regional-engagement'),
      fetchAnalytics('marketing-channels'),
    ]).then(([genre, regional, marketing]) => {
      setChartData({ genre: genre.result, regional: regional.result, marketing: marketing.result })
    }).catch(() => {})
  }, [])

  const submit = useCallback(async (msg) => {
    const text = (msg || input).trim()
    if (!text || loading) return
    setInput('')
    inputRef.current?.focus()

    const userMsg = { role:'user', content:text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    const apiHistory = messages.slice(-10).map(m => ({ role:m.role, content:m.content }))

    try {
      const res = await sendChat(text, apiHistory)
      const aiMsg = { role:'assistant', content:res.answer, toolTrace:res.tool_trace||[], sources:res.sources||[] }
      setMessages(prev => [...prev, aiMsg])
      setHistory(prev => [
        { query:text, sources:res.sources, ts:new Date().toLocaleTimeString() },
        ...prev.slice(0,49)
      ])
    } catch (err) {
      setMessages(prev => [...prev, {
        role:'assistant', content:`Error: ${err.message}\n\nMake sure the backend is running (./start.sh).`,
        toolTrace:[], sources:[],
      }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, messages])

  const toggleTrace = (idx) => setOpenTraces(p => ({ ...p, [idx]: !p[idx] }))

  return (
    <div style={css.app}>

      {/* ── Left sidebar ── */}
      <div style={css.sidebar}>
        <div style={css.sideLogo}>
          <div style={css.sideTitle}>🎬 AI Insights</div>
          <div style={css.sideSub}>Entertainment Analytics Assistant</div>
        </div>

        {backendOk === false && (
          <div style={{ margin:10, padding:'8px 10px', background:'#450a0a', border:'1px solid #991b1b',
                        borderRadius:8, fontSize:12, color:'#fca5a5' }}>
            Backend offline or API key missing. Run <code style={{background:'#300'}}>./start.sh</code>
          </div>
        )}

        <div style={css.sideSection}>
          <div style={css.sideLabel}>Example queries</div>
          {examples.map((ex,i) => (
            <div key={i} style={css.pill} onClick={() => submit(ex)}
                 onMouseEnter={e => e.currentTarget.style.background='#252a40'}
                 onMouseLeave={e => e.currentTarget.style.background='#1a1e30'}>
              {ex}
            </div>
          ))}
        </div>

        <div style={{ flex:1 }} />
        <div style={{ padding:'10px 14px', fontSize:11, color:'#1f2937', borderTop:'1px solid #131620' }}>
          Read-only · Tool-traced · Secure
        </div>
      </div>

      {/* ── Centre chat ── */}
      <div style={css.centre}>
        <div style={css.topBar}>
          <div style={css.topTitle}>Chat</div>
          {loading && <div style={{ fontSize:12, color:'#7c3aed' }}>Querying data sources…</div>}
        </div>

        <div style={css.chatScroll}>
          {messages.length === 0 && (
            <div style={css.emptyState}>
              <div style={{ fontSize:36, marginBottom:14 }}>🔍</div>
              <div style={{ fontSize:17, fontWeight:700, color:'#7c3aed', marginBottom:6 }}>
                Ask anything about your content
              </div>
              <div style={{ fontSize:13 }}>Click an example query on the left to get started</div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i}>
              {msg.role === 'user'
                ? <div style={css.userBubble}>{msg.content}</div>
                : (
                  <div>
                    <div style={css.aiBubble}>
                      {msg.content}
                      {msg.sources?.length > 0 && (
                        <div style={css.srcRow}>
                          <span style={css.srcLabel}>Sources:</span>
                          {msg.sources.map(s => <span key={s} style={css.srcBadge}>{s}</span>)}
                        </div>
                      )}
                    </div>
                    {msg.toolTrace?.length > 0 && (
                      <ToolTrace trace={msg.toolTrace} open={openTraces[i]} onToggle={() => toggleTrace(i)} />
                    )}
                  </div>
                )
              }
            </div>
          ))}

          {loading && (
            <div style={css.thinking}><Spinner /> Routing to tools…</div>
          )}
          <div ref={bottomRef} />
        </div>

        <div style={css.inputRow}>
          <input
            ref={inputRef}
            style={css.input}
            value={input}
            placeholder="Ask a business question…"
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submit()}
            onFocus={e  => e.target.style.borderColor = '#7c3aed'}
            onBlur={e   => e.target.style.borderColor = '#1e2235'}
          />
          <button
            style={{ ...css.sendBtn, opacity: loading ? 0.6 : 1 }}
            onClick={() => submit()}
            disabled={loading}
            onMouseEnter={e => !loading && (e.target.style.background='#6d28d9')}
            onMouseLeave={e => (e.target.style.background='#7c3aed')}
          >
            {loading ? '…' : 'Send'}
          </button>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div style={css.right}>
        <div style={css.tabBar}>
          {['charts', 'history'].map(t => (
            <button key={t} style={{
              ...css.tab,
              color: rightTab===t ? '#7c3aed' : '#4b5563',
              borderBottom: rightTab===t ? '2px solid #7c3aed' : '2px solid transparent',
            }} onClick={() => setRightTab(t)}>
              {t === 'charts' ? '📊 Charts' : '🕐 History'}
            </button>
          ))}
        </div>
        <div style={css.panelBody}>
          {rightTab === 'charts'  && <ChartsPanel data={chartData} />}
          {rightTab === 'history' && <HistoryPanel items={history} onSelect={submit} />}
        </div>
      </div>
    </div>
  )
}

// ── Tool trace ───────────────────────────────────────────────────────────
function ToolTrace({ trace, open, onToggle }) {
  return (
    <div style={css.traceWrap}>
      <div style={css.traceHead} onClick={onToggle}>
        <span>🔧 {trace.length} tool{trace.length !== 1 ? 's' : ''} invoked</span>
        <span>{open ? '▲ hide' : '▼ show'} trace</span>
      </div>
      {open && trace.map((t, i) => (
        <div key={i} style={css.traceRow}>
          <div>
            <span style={css.toolBadge}>{t.tool}</span>
            <span style={{ color:'#6b7280' }}>{t.result_summary}</span>
          </div>
          {t.input && Object.keys(t.input).length > 0 && (
            <div style={css.monoText}>
              input: {JSON.stringify(t.input).slice(0,150)}{JSON.stringify(t.input).length>150?'…':''}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Charts panel ─────────────────────────────────────────────────────────
function ChartsPanel({ data }) {
  const genre = (data.genre || []).map(r => ({
    name: r.genre, watches: r.total_watches || 0,
  }))
  const regional = (data.regional || []).slice(0,6).map(r => ({
    name: r.city, views: Math.round((r.views||0)/1000),
  }))
  const marketing = (data.marketing || []).map(r => ({
    name: r.channel, spend: Math.round((r.spend_inr||0)/100000),
  }))

  const ttStyle = { background:'#0f1117', border:'1px solid #1e2235', borderRadius:8, fontSize:12, color:'#e2e8f0' }
  const axStyle = { fill:'#374151', fontSize:10 }

  if (!genre.length) return (
    <div style={css.emptyState}>
      <div style={{ fontSize:22 }}>📊</div>
      <div style={{ fontSize:12, marginTop:8 }}>
        Charts load from the backend.<br/>Make sure the server is running.
      </div>
    </div>
  )

  return (
    <div>
      <div style={css.chartCard}>
        <div style={css.chartTitle}>Genre watch volume</div>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={genre} margin={{top:0,right:4,left:-24,bottom:0}}>
            <XAxis dataKey="name" tick={axStyle} />
            <YAxis tick={axStyle} />
            <Tooltip contentStyle={ttStyle} />
            <Bar dataKey="watches" fill="#7c3aed" radius={[3,3,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={css.chartCard}>
        <div style={css.chartTitle}>Top cities  -  views (K)</div>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={regional} margin={{top:0,right:4,left:-24,bottom:0}}>
            <XAxis dataKey="name" tick={axStyle} />
            <YAxis tick={axStyle} />
            <Tooltip contentStyle={ttStyle} />
            <Bar dataKey="views" fill="#0d9488" radius={[3,3,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={css.chartCard}>
        <div style={css.chartTitle}>Marketing spend by channel (Rs.L)</div>
        <ResponsiveContainer width="100%" height={155}>
          <PieChart>
            <Pie data={marketing} dataKey="spend" nameKey="name" cx="50%" cy="50%" outerRadius={58}>
              {marketing.map((_,i) => <Cell key={i} fill={PALETTE[i%PALETTE.length]} />)}
            </Pie>
            <Tooltip contentStyle={ttStyle} />
            <Legend iconSize={9} iconType="circle"
                    wrapperStyle={{fontSize:11,color:'#6b7280'}} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ── History panel ────────────────────────────────────────────────────────
function HistoryPanel({ items, onSelect }) {
  if (!items.length) return (
    <div style={css.emptyState}>
      <div style={{ fontSize:22 }}>🕐</div>
      <div style={{ fontSize:12, marginTop:8 }}>No queries yet.<br/>Ask something to see history here.</div>
    </div>
  )
  return items.map((item, i) => (
    <div key={i} style={css.histRow} onClick={() => onSelect(item.query)}
         onMouseEnter={e => e.currentTarget.style.background='#1a1e30'}
         onMouseLeave={e => e.currentTarget.style.background='transparent'}>
      <div style={css.histQ}>{item.query}</div>
      <div style={css.histMeta}>
        <div style={{ display:'flex', gap:4, flexWrap:'wrap' }}>
          {item.sources.map(s => <span key={s} style={css.srcBadge}>{s}</span>)}
        </div>
        <span style={{ fontSize:10, color:'#374151' }}>{item.ts}</span>
      </div>
    </div>
  ))
}

// ── Spinner ──────────────────────────────────────────────────────────────
function Spinner() {
  return (
    <>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      <span style={{ display:'inline-block', width:11, height:11, borderRadius:'50%',
        border:'2px solid #7c3aed33', borderTopColor:'#7c3aed',
        animation:'spin 0.7s linear infinite' }} />
    </>
  )
}
