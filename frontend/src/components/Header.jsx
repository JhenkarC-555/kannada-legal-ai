// src/components/Header.jsx
// Top navigation bar.
// Shows logo, app name, connection status and language badge.

import { useEffect, useState } from 'react'
import { checkHealth } from '../api.js'

export default function Header() {
  const [status, setStatus]   = useState('connecting')
  const [docCount, setDocCount] = useState(null)

  // ── Check backend health on mount ──────────────────────
  useEffect(() => {
    async function check() {
      const health = await checkHealth()
      if (health.status === 'ok' || health.status === 'degraded') {
        setStatus('connected')
        setDocCount(health.total_documents || 0)
      } else {
        setStatus('offline')
      }
    }
    check()

    // Re-check every 30 seconds
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [])

  // ── Status badge config ────────────────────────────────
  const statusConfig = {
    connecting: {
      color: '#FCD34D',
      bg:    'rgba(252,211,77,0.15)',
      text:  '● Connecting...',
    },
    connected: {
      color: '#6EE7B7',
      bg:    'rgba(26,74,46,0.6)',
      text:  '● Connected',
    },
    offline: {
      color: '#FCA5A5',
      bg:    'rgba(139,26,26,0.6)',
      text:  '● Offline',
    },
  }

  const cfg = statusConfig[status]

  return (
    <header style={styles.header}>
      <div style={styles.inner}>

        {/* ── Logo ── */}
        <div style={styles.logo}>
          <span style={styles.logoIcon}>⚖️</span>
          <div>
            <h1 style={styles.logoTitle}>ಕನ್ನಡ ಕಾನೂನು AI</h1>
            <p style={styles.logoSub}>Kannada Legal AI Assistant</p>
          </div>
        </div>

        {/* ── Right side badges ── */}
        <div style={styles.badges}>

          {/* Connection status */}
          <span style={{
            ...styles.badge,
            color:      cfg.color,
            background: cfg.bg,
            border:     `1px solid ${cfg.color}33`,
          }}>
            {cfg.text}
          </span>

          {/* Document count — shown when connected */}
          {status === 'connected' && docCount !== null && (
            <span style={{
              ...styles.badge,
              color:      '#93C5FD',
              background: 'rgba(13,43,69,0.7)',
              border:     '1px solid rgba(147,197,253,0.2)',
            }}>
              📚 {docCount} docs
            </span>
          )}

          {/* Language badge */}
          <span style={{
            ...styles.badge,
            color:      '#C8973A',
            background: 'rgba(200,151,58,0.12)',
            border:     '1px solid rgba(200,151,58,0.3)',
          }}>
            ಕನ್ನಡ
          </span>

          {/* Domain badge */}
          <span style={{
            ...styles.badge,
            color:      '#D1FAE5',
            background: 'rgba(26,74,46,0.4)',
            border:     '1px solid rgba(209,250,229,0.2)',
          }}>
            Legal Domain
          </span>

        </div>
      </div>
    </header>
  )
}

// ── Styles ─────────────────────────────────────────────────
const styles = {
  header: {
    background:   '#1A1209',
    borderBottom: '3px solid #C8973A',
    padding:      '14px 24px',
    position:     'sticky',
    top:          0,
    zIndex:       100,
    flexShrink:   0,
  },
  inner: {
    maxWidth:       '1200px',
    margin:         '0 auto',
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'space-between',
    flexWrap:       'wrap',
    gap:            '12px',
  },
  logo: {
    display:    'flex',
    alignItems: 'center',
    gap:        '12px',
  },
  logoIcon: {
    fontSize: '2rem',
    filter:   'drop-shadow(0 0 8px rgba(200,151,58,0.5))',
  },
  logoTitle: {
    fontFamily: "'Noto Sans Kannada', serif",
    color:      '#C8973A',
    fontSize:   '1.35rem',
    fontWeight: 700,
    lineHeight: 1.2,
  },
  logoSub: {
    fontFamily:    "'DM Mono', monospace",
    color:         'rgba(255,255,255,0.4)',
    fontSize:      '0.7rem',
    letterSpacing: '1px',
    marginTop:     '2px',
  },
  badges: {
    display:  'flex',
    gap:      '8px',
    flexWrap: 'wrap',
  },
  badge: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.72rem',
    padding:       '4px 10px',
    borderRadius:  '20px',
    fontWeight:    600,
    letterSpacing: '0.3px',
  },
}