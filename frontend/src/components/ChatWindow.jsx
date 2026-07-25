// src/components/ChatWindow.jsx
// Renders the full chat message history.
// Shows user messages, bot responses and loading state.

import { useEffect, useRef } from 'react'
import LegalCard from './LegalCard.jsx'

export default function ChatWindow({ messages, isLoading, onChipClick }) {
  const bottomRef = useRef(null)

  // ── Auto scroll to bottom on new message ───────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // ── Welcome screen ─────────────────────────────────────
  if (messages.length === 0 && !isLoading) {
    return (
      <div style={styles.welcome}>
        <div style={styles.welcomeInner}>

          <div style={styles.welcomeIcon}>⚖️</div>

          <h2 style={styles.welcomeTitle}>
            ಕನ್ನಡದಲ್ಲಿ ಕಾನೂನು ಪ್ರಶ್ನೆ ಕೇಳಿ
          </h2>

          <p style={styles.welcomeSub}>
            Ask your legal question in Kannada
          </p>

          <p style={styles.welcomeHint}>
            ಕೆಳಗೆ ಟೈಪ್ ಮಾಡಿ, ಮೈಕ್ ಬಳಸಿ ಅಥವಾ ಕನ್ನಡ ಕೀಬೋರ್ಡ್ ಬಳಸಿ
          </p>

          {/* Quick start chips */}
          <div style={styles.chips}>
            {QUICK_QUESTIONS.map((q, i) => (
              <QuickChip
                key={i}
                question={q.text}
                icon={q.icon}
                onClick={() => onChipClick(q.text)}
              />
            ))}
          </div>

          {/* Feature badges */}
          <div style={styles.featureBadges}>
            <span style={styles.featureBadge}>⌨️ Kannada Keyboard</span>
            <span style={styles.featureBadge}>🎤 Voice Input</span>
            <span style={styles.featureBadge}>🔍 Smart Search</span>
            <span style={styles.featureBadge}>📚 Legal Citations</span>
          </div>

        </div>
      </div>
    )
  }

  // ── Chat messages ──────────────────────────────────────
  return (
    <div style={styles.container}>

      {messages.map((msg, i) => {
        // User message
        if (msg.role === 'user') {
          return (
            <div key={i} style={styles.userRow}>
              <div style={styles.userBubble}>
                {msg.content}
              </div>
            </div>
          )
        }

        // Error message
        if (msg.role === 'error') {
          return (
            <div key={i} style={styles.botRow}>
              <BotAvatar />
              <div style={styles.errorCard}>
                <span>⚠️</span>
                <span>{msg.content}</span>
              </div>
            </div>
          )
        }

        // Bot response with legal card
        return (
          <div key={i} style={styles.botRow}>
            <BotAvatar />
            <div style={styles.botContent}>
              <LegalCard data={msg.data} />
            </div>
          </div>
        )
      })}

      {/* Loading indicator */}
      {isLoading && (
        <div style={styles.botRow}>
          <BotAvatar pulse />
          <LoadingCard />
        </div>
      )}

      {/* Invisible div to scroll to */}
      <div ref={bottomRef} />

    </div>
  )
}


// ════════════════════════════════════════════
// SUB COMPONENTS
// ════════════════════════════════════════════

function BotAvatar({ pulse }) {
  return (
    <div style={{
      ...styles.avatar,
      animation: pulse ? 'pulse 1.5s infinite' : 'none',
    }}>
      ⚖️
    </div>
  )
}

function LoadingCard() {
  return (
    <div style={styles.loadingCard}>
      <div style={styles.dots}>
        {[0, 1, 2].map(i => (
          <div
            key={i}
            style={{
              ...styles.dot,
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <span style={styles.loadingText}>
        ಕಾನೂನು ಮಾಹಿತಿ ಹುಡುಕುತ್ತಿದ್ದೇನೆ...
      </span>
    </div>
  )
}

function QuickChip({ question, icon, onClick }) {
  return (
    <button
      style={styles.chip}
      onClick={onClick}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = '#C8973A'
        e.currentTarget.style.background  = '#FDF5E6'
        e.currentTarget.style.transform   = 'translateY(-2px)'
        e.currentTarget.style.boxShadow   = '0 4px 12px rgba(200,151,58,0.15)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = '#EFE5CC'
        e.currentTarget.style.background  = '#FFFFFF'
        e.currentTarget.style.transform   = 'none'
        e.currentTarget.style.boxShadow   = 'none'
      }}
    >
      <span>{icon}</span>
      <span>{question}</span>
    </button>
  )
}


// ════════════════════════════════════════════
// STATIC DATA
// ════════════════════════════════════════════

const QUICK_QUESTIONS = [
  { text: 'IPC ಸೆಕ್ಷನ್ 302 ಏನು?',              icon: '📖' },
  { text: 'ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ಹಕ್ಕೇನು?',        icon: '🛡️' },
  { text: 'FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?',             icon: '📋' },
  { text: 'ಕಳ್ಳತನಕ್ಕೆ ಶಿಕ್ಷೆ ಏನು?',             icon: '⚖️' },
  { text: 'ಜಾಮೀನು ಪಡೆಯುವ ಪ್ರಕ್ರಿಯೆ',           icon: '📝' },
  { text: 'ಉಚಿತ ವಕೀಲರ ಸಹಾಯ ಹೇಗೆ ಪಡೆಯಬಹುದು?', icon: '🆓' },
]


// ════════════════════════════════════════════
// STYLES
// ════════════════════════════════════════════

const styles = {

  // ── Container ──
  container: {
    flex:          1,
    overflowY:     'auto',
    padding:       '20px 24px',
    display:       'flex',
    flexDirection: 'column',
    gap:           '20px',
  },

  // ── Welcome ──
  welcome: {
    flex:           1,
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'center',
    padding:        '32px 24px',
    overflowY:      'auto',
  },
  welcomeInner: {
    display:        'flex',
    flexDirection:  'column',
    alignItems:     'center',
    textAlign:      'center',
    gap:            '10px',
    maxWidth:       '640px',
    width:          '100%',
  },
  welcomeIcon: {
    fontSize:     '3.5rem',
    lineHeight:   1,
    marginBottom: '4px',
    filter:       'drop-shadow(0 4px 8px rgba(200,151,58,0.3))',
  },
  welcomeTitle: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '1.6rem',
    fontWeight: 700,
    color:      '#1A1209',
    lineHeight: 1.3,
  },
  welcomeSub: {
    fontFamily: 'sans-serif',
    fontSize:   '0.95rem',
    color:      '#6B7280',
  },
  welcomeHint: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.85rem',
    color:      '#9CA3AF',
    marginTop:  '2px',
  },

  // Quick chips
  chips: {
    display:        'flex',
    flexWrap:       'wrap',
    gap:            '8px',
    justifyContent: 'center',
    marginTop:      '12px',
  },
  chip: {
    display:      'flex',
    alignItems:   'center',
    gap:          '6px',
    background:   '#FFFFFF',
    border:       '1.5px solid #EFE5CC',
    borderRadius: '20px',
    padding:      '8px 16px',
    fontSize:     '0.88rem',
    cursor:       'pointer',
    color:        '#3D2B10',
    transition:   'all 0.18s ease',
    fontFamily:   "'Noto Sans Kannada', serif",
    boxShadow:    '0 1px 4px rgba(0,0,0,0.05)',
  },

  // Feature badges
  featureBadges: {
    display:        'flex',
    flexWrap:       'wrap',
    gap:            '6px',
    justifyContent: 'center',
    marginTop:      '8px',
  },
  featureBadge: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.68rem',
    padding:       '3px 10px',
    background:    '#F3F4F6',
    border:        '1px solid #E5E7EB',
    borderRadius:  '10px',
    color:         '#6B7280',
    letterSpacing: '0.3px',
  },

  // ── User message ──
  userRow: {
    display:        'flex',
    justifyContent: 'flex-end',
    animation:      'fadeIn 0.25s ease forwards',
  },
  userBubble: {
    background:   '#0D2B45',
    color:        '#FAF4E8',
    padding:      '12px 16px',
    borderRadius: '16px 16px 4px 16px',
    maxWidth:     '75%',
    fontSize:     '0.95rem',
    lineHeight:   '1.7',
    boxShadow:    '0 2px 8px rgba(13,43,69,0.25)',
    fontFamily:   "'Noto Sans Kannada', serif",
    wordBreak:    'break-word',
  },

  // ── Bot message ──
  botRow: {
    display:    'flex',
    gap:        '10px',
    alignItems: 'flex-start',
    animation:  'fadeIn 0.25s ease forwards',
  },
  avatar: {
    width:          '36px',
    height:         '36px',
    background:     '#1A1209',
    border:         '2px solid #C8973A',
    borderRadius:   '50%',
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'center',
    fontSize:       '1rem',
    flexShrink:     0,
    marginTop:      '2px',
  },
  botContent: {
    flex:    1,
    minWidth: 0,
  },

  // ── Error card ──
  errorCard: {
    background:   '#FFF5F5',
    border:       '1px solid #FECACA',
    borderRadius: '10px',
    padding:      '12px 16px',
    color:        '#8B1A1A',
    fontSize:     '0.9rem',
    fontFamily:   "'Noto Sans Kannada', serif",
    display:      'flex',
    gap:          '8px',
    alignItems:   'center',
    flex:         1,
  },

  // ── Loading card ──
  loadingCard: {
    background:   '#FFFFFF',
    border:       '1px solid #EFE5CC',
    borderRadius: '12px',
    padding:      '14px 18px',
    display:      'flex',
    alignItems:   'center',
    gap:          '12px',
    flex:         1,
    boxShadow:    '0 2px 8px rgba(0,0,0,0.05)',
  },
  dots: {
    display: 'flex',
    gap:     '5px',
  },
  dot: {
    width:           '8px',
    height:          '8px',
    background:      '#C8973A',
    borderRadius:    '50%',
    animation:       'bounce 1.2s infinite',
    animationFillMode: 'both',
  },
  loadingText: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.88rem',
    color:      '#6B7280',
  },
}