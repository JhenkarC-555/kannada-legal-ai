// src/components/QueryInput.jsx
// Bottom input bar with:
//   - Text area for typing Kannada queries
//   - Send button
//   - Mic button (speech to text)
//   - Kannada keyboard toggle button
//   - Character counter
//   - Error display

import { useState, useRef, useEffect } from 'react'
import MicInput from './MicInput.jsx'
import KannadaKeyboard from './KannadaKeyboard.jsx'

const MAX_CHARS = 500

export default function QueryInput({ onSend, isLoading }) {
  const [query,        setQuery]        = useState('')
  const [showKeyboard, setShowKeyboard] = useState(false)
  const [micError,     setMicError]     = useState('')
  const [isFocused,    setIsFocused]    = useState(false)
  const textareaRef = useRef(null)

  // ── Auto focus on mount ────────────────────────────────
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  // ── Auto resize textarea height ────────────────────────
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }, [query])

  // ── Clear mic error after 4 seconds ───────────────────
  useEffect(() => {
    if (!micError) return
    const t = setTimeout(() => setMicError(''), 4000)
    return () => clearTimeout(t)
  }, [micError])

  // ── Handle send ────────────────────────────────────────
  function handleSend() {
    const text = query.trim()
    if (!text || isLoading || text.length > MAX_CHARS) return
    onSend(text)
    setQuery('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  // ── Handle keyboard shortcut ───────────────────────────
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ── Handle mic result ──────────────────────────────────
  function handleMicResult(text, isFinal) {
    if (isFinal) {
      // Final — append to existing query
      setQuery(prev => {
        const sep = prev.trim() ? ' ' : ''
        return prev + sep + text
      })
      textareaRef.current?.focus()
    }
    // Interim results are shown in MicInput tooltip
  }

  // ── Handle mic error ───────────────────────────────────
  function handleMicError(msg) {
    setMicError(msg)
  }

  // ── Handle keyboard insert ─────────────────────────────
  function handleKeyboardInsert(text) {
    setQuery(prev => {
      const sep = prev.trim() ? '' : ''
      return prev + sep + text
    })
    textareaRef.current?.focus()
  }

  const charCount    = query.length
  const isOverLimit  = charCount > MAX_CHARS
  const canSend      = query.trim().length > 0
                       && !isLoading
                       && !isOverLimit

  return (
    <>
      {/* ── Kannada Keyboard (rendered as overlay) ── */}
      {showKeyboard && (
        <KannadaKeyboard
          onInsert={handleKeyboardInsert}
          onClose={() => setShowKeyboard(false)}
        />
      )}

      <div style={styles.wrapper}>

        {/* ── Mic error banner ── */}
        {micError && (
          <div style={styles.errorBanner}>
            <span>⚠️</span>
            <span>{micError}</span>
            <button
              style={styles.errorClose}
              onClick={() => setMicError('')}
            >✕</button>
          </div>
        )}

        {/* ── Main input area ── */}
        <div style={{
          ...styles.inputBox,
          ...(isFocused ? styles.inputBoxFocused : {}),
          ...(isOverLimit ? styles.inputBoxError : {}),
        }}>

          {/* ── Textarea ── */}
          <textarea
            ref={textareaRef}
            style={styles.textarea}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="ನಿಮ್ಮ ಕಾನೂನು ಪ್ರಶ್ನೆ ಇಲ್ಲಿ ಬರೆಯಿರಿ..."
            rows={1}
            disabled={isLoading}
            maxLength={MAX_CHARS + 10}
          />

          {/* ── Right side buttons ── */}
          <div style={styles.btnGroup}>

            {/* Kannada keyboard toggle */}
            <KeyboardToggleBtn
              active={showKeyboard}
              onClick={() => setShowKeyboard(prev => !prev)}
              disabled={isLoading}
            />

            {/* Mic button */}
            <MicInput
              onResult={handleMicResult}
              onError={handleMicError}
              disabled={isLoading}
            />

            {/* Send button */}
            <button
              style={{
                ...styles.sendBtn,
                ...(canSend ? styles.sendBtnActive : {}),
              }}
              onClick={handleSend}
              disabled={!canSend}
              title="Send (Enter)"
            >
              {isLoading
                ? <LoadingSpinner />
                : <SendIcon />
              }
            </button>

          </div>
        </div>

        {/* ── Bottom meta row ── */}
        <div style={styles.metaRow}>

          {/* Left — shortcuts hint */}
          <div style={styles.hints}>
            <span style={styles.hint}>Enter → Send</span>
            <span style={styles.hintDot}>·</span>
            <span style={styles.hint}>Shift+Enter → New line</span>
            <span style={styles.hintDot}>·</span>
            <span style={styles.hint}>⌨️ → Kannada keyboard</span>
            <span style={styles.hintDot}>·</span>
            <span style={styles.hint}>🎤 → Voice</span>
          </div>

          {/* Right — char count */}
          <div style={{
            ...styles.charCount,
            ...(isOverLimit ? styles.charCountError : {}),
            ...(charCount > MAX_CHARS * 0.8
              ? styles.charCountWarn
              : {}),
          }}>
            {charCount} / {MAX_CHARS}
          </div>

        </div>
      </div>
    </>
  )
}


// ════════════════════════════════════════════
// SUB COMPONENTS
// ════════════════════════════════════════════

function KeyboardToggleBtn({ active, onClick, disabled }) {
  const [hovered, setHovered] = useState(false)

  return (
    <button
      style={{
        ...styles.iconBtn,
        ...(active
          ? styles.iconBtnActive
          : hovered && !disabled
          ? styles.iconBtnHover
          : {}),
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
      }}
      onClick={onClick}
      disabled={disabled}
      title="ಕನ್ನಡ ಕೀಬೋರ್ಡ್ ತೆರೆಯಿರಿ"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      ⌨️
    </button>
  )
}

function SendIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

function LoadingSpinner() {
  return (
    <div style={styles.spinner} />
  )
}


// ════════════════════════════════════════════
// STYLES
// ════════════════════════════════════════════

const styles = {

  wrapper: {
    borderTop:     '1px solid #EFE5CC',
    padding:       '12px 24px 14px',
    background:    '#FFFFFF',
    flexShrink:    0,
    display:       'flex',
    flexDirection: 'column',
    gap:           '6px',
  },

  // ── Mic error banner ──
  errorBanner: {
    background:   '#FFF5F5',
    border:       '1px solid #FECACA',
    borderRadius: '8px',
    padding:      '8px 12px',
    display:      'flex',
    alignItems:   'center',
    gap:          '8px',
    fontSize:     '0.85rem',
    color:        '#8B1A1A',
    fontFamily:   "'Noto Sans Kannada', serif",
    animation:    'fadeIn 0.2s ease',
  },
  errorClose: {
    marginLeft:   'auto',
    background:   'none',
    border:       'none',
    color:        '#8B1A1A',
    cursor:       'pointer',
    fontSize:     '0.85rem',
    padding:      '0 4px',
    flexShrink:   0,
  },

  // ── Input box ──
  inputBox: {
    display:      'flex',
    alignItems:   'flex-end',
    gap:          '8px',
    background:   '#FAF4E8',
    border:       '1.5px solid #EFE5CC',
    borderRadius: '12px',
    padding:      '8px 8px 8px 14px',
    transition:   'all 0.2s ease',
  },
  inputBoxFocused: {
    borderColor: '#C8973A',
    background:  '#FFFFFF',
    boxShadow:   '0 0 0 3px rgba(200,151,58,0.1)',
  },
  inputBoxError: {
    borderColor: '#EF4444',
    boxShadow:   '0 0 0 3px rgba(239,68,68,0.1)',
  },

  // ── Textarea ──
  textarea: {
    flex:         1,
    border:       'none',
    outline:      'none',
    background:   'transparent',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '1rem',
    color:        '#1A1209',
    lineHeight:   '1.6',
    resize:       'none',
    minHeight:    '40px',
    maxHeight:    '120px',
    padding:      '4px 0',
    overflowY:    'auto',
  },

  // ── Button group ──
  btnGroup: {
    display:    'flex',
    alignItems: 'flex-end',
    gap:        '6px',
    flexShrink: 0,
  },

  // ── Icon buttons ──
  iconBtn: {
    width:          '48px',
    height:         '48px',
    borderRadius:   '10px',
    border:         '1.5px solid #EFE5CC',
    background:     '#FAF4E8',
    fontSize:       '1.1rem',
    cursor:         'pointer',
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'center',
    transition:     'all 0.15s',
    flexShrink:     0,
  },
  iconBtnHover: {
    background:   '#FDF5E6',
    borderColor:  '#C8973A',
  },
  iconBtnActive: {
    background:   '#C8973A',
    borderColor:  '#C8973A',
    boxShadow:    '0 2px 8px rgba(200,151,58,0.3)',
  },

  // ── Send button ──
  sendBtn: {
    width:          '48px',
    height:         '48px',
    borderRadius:   '10px',
    border:         'none',
    background:     '#EFE5CC',
    color:          '#6B7280',
    cursor:         'not-allowed',
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'center',
    transition:     'all 0.15s',
    flexShrink:     0,
  },
  sendBtnActive: {
    background:   '#C8973A',
    color:        '#FFFFFF',
    cursor:       'pointer',
    boxShadow:    '0 2px 8px rgba(200,151,58,0.35)',
  },

  // Loading spinner
  spinner: {
    width:       '18px',
    height:      '18px',
    border:      '2px solid rgba(255,255,255,0.3)',
    borderTop:   '2px solid #FFFFFF',
    borderRadius:'50%',
    animation:   'spin 0.8s linear infinite',
  },

  // ── Meta row ──
  metaRow: {
    display:        'flex',
    justifyContent: 'space-between',
    alignItems:     'center',
    paddingLeft:    '2px',
  },
  hints: {
    display:    'flex',
    alignItems: 'center',
    gap:        '5px',
    flexWrap:   'wrap',
  },
  hint: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.65rem',
    color:         '#9CA3AF',
    letterSpacing: '0.2px',
  },
  hintDot: {
    color:   '#D1D5DB',
    fontSize:'0.65rem',
  },
  charCount: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.7rem',
    color:         '#9CA3AF',
    letterSpacing: '0.3px',
  },
  charCountWarn: {
    color: '#F59E0B',
  },
  charCountError: {
    color:      '#EF4444',
    fontWeight: 600,
  },
}