// src/App.jsx
// Main app shell — ties all components together.
// Manages global state: messages, loading, session.
//
// Layout:
//   Header
//   ├── Sidebar (examples, laws, stats)
//   └── Main area
//       ├── ChatWindow (messages)
//       └── QueryInput (input bar)

import { useState, useRef, useCallback } from 'react'
import Header      from './components/Header.jsx'
import Sidebar     from './components/Sidebar.jsx'
import ChatWindow  from './components/ChatWindow.jsx'
import QueryInput  from './components/QueryInput.jsx'
import { sendQuery } from './api.js'

// ── Generate a session ID once per browser session ─────────
const SESSION_ID = 'session_' + Date.now()

export default function App() {
  const [messages,  setMessages]  = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const messagesEndRef = useRef(null)

  // ── Add a message to the chat ───────────────────────────
  function addMessage(role, content, data = null) {
    setMessages(prev => [...prev, { role, content, data }])
  }

  // ── Handle query submission ─────────────────────────────
  const handleSend = useCallback(async (question) => {
    if (!question.trim() || isLoading) return

    // Add user message immediately
    addMessage('user', question)
    setIsLoading(true)

    try {
      const data = await sendQuery({
        question,
        sessionId: SESSION_ID,
      })

      if (data.success) {
        // Add bot response
        addMessage('bot', '', data)
      } else {
        addMessage(
          'error',
          data.error ||
          'ಸರ್ವರ್ ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
        )
      }
    } catch (err) {
      addMessage(
        'error',
        err.message ||
        'ಸರ್ವರ್‌ಗೆ ಸಂಪರ್ಕಿಸಲಾಗಲಿಲ್ಲ. ' +
        'Backend ಚಾಲನೆಯಲ್ಲಿದೆಯೇ ಎಂದು ಪರೀಕ್ಷಿಸಿ.'
      )
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  // ── Handle example / chip click ─────────────────────────
  const handleChipClick = useCallback((question) => {
    handleSend(question)
  }, [handleSend])

  // ── Clear chat ──────────────────────────────────────────
  function clearChat() {
    setMessages([])
  }

  return (
    <div style={styles.root}>

      {/* ── Header ── */}
      <Header />

      {/* ── Body ── */}
      <div style={styles.body}>

        {/* ── Sidebar — hidden on small screens ── */}
        {sidebarOpen && (
          <Sidebar onExampleClick={handleChipClick} />
        )}

        {/* ── Main chat area ── */}
        <div style={styles.main}>

          {/* ── Toolbar ── */}
          <div style={styles.toolbar}>

            {/* Sidebar toggle */}
            <button
              style={styles.toolbarBtn}
              onClick={() => setSidebarOpen(prev => !prev)}
              title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
            >
              {sidebarOpen ? '◀ Hide' : '▶ Menu'}
            </button>

            {/* Centre — session info */}
            <div style={styles.toolbarCenter}>
              <span style={styles.sessionLabel}>
                Session
              </span>
              <span style={styles.sessionId}>
                {SESSION_ID.slice(-8)}
              </span>
              <span style={styles.msgCount}>
                {messages.filter(m => m.role === 'user').length} queries
              </span>
            </div>

            {/* Clear chat */}
            {messages.length > 0 && (
              <button
                style={styles.clearBtn}
                onClick={clearChat}
                title="Clear conversation"
              >
                🗑 Clear
              </button>
            )}

          </div>

          {/* ── Chat window ── */}
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            onChipClick={handleChipClick}
          />

          {/* ── Query input ── */}
          <QueryInput
            onSend={handleSend}
            isLoading={isLoading}
          />

        </div>
      </div>
    </div>
  )
}


// ════════════════════════════════════════════
// STYLES
// ════════════════════════════════════════════

const styles = {

  // ── Root ──
  root: {
    height:        '100vh',
    display:       'flex',
    flexDirection: 'column',
    overflow:      'hidden',
    background:    '#FAF4E8',
  },

  // ── Body ──
  body: {
    flex:       1,
    display:    'flex',
    overflow:   'hidden',
    minHeight:  0,
  },

  // ── Main area ──
  main: {
    flex:          1,
    display:       'flex',
    flexDirection: 'column',
    overflow:      'hidden',
    minWidth:      0,
  },

  // ── Toolbar ──
  toolbar: {
    display:        'flex',
    alignItems:     'center',
    gap:            '10px',
    padding:        '8px 16px',
    borderBottom:   '1px solid #EFE5CC',
    background:     '#FFFFFF',
    flexShrink:     0,
  },
  toolbarBtn: {
    background:    'none',
    border:        '1px solid #EFE5CC',
    borderRadius:  '6px',
    padding:       '4px 10px',
    fontSize:      '0.75rem',
    color:         '#6B7280',
    cursor:        'pointer',
    fontFamily:    "'DM Mono', monospace",
    transition:    'all 0.15s',
    whiteSpace:    'nowrap',
  },
  toolbarCenter: {
    flex:          1,
    display:       'flex',
    alignItems:    'center',
    justifyContent:'center',
    gap:           '8px',
  },
  sessionLabel: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.65rem',
    color:         '#D1D5DB',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
  sessionId: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.72rem',
    color:         '#C8973A',
    background:    'rgba(200,151,58,0.08)',
    padding:       '2px 8px',
    borderRadius:  '4px',
    border:        '1px solid rgba(200,151,58,0.2)',
  },
  msgCount: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.65rem',
    color:         '#9CA3AF',
  },
  clearBtn: {
    background:    'none',
    border:        '1px solid #FECACA',
    borderRadius:  '6px',
    padding:       '4px 10px',
    fontSize:      '0.75rem',
    color:         '#8B1A1A',
    cursor:        'pointer',
    fontFamily:    "'DM Mono', monospace",
    transition:    'all 0.15s',
    whiteSpace:    'nowrap',
  },
}