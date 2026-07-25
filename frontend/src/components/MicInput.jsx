// src/components/MicInput.jsx
// Speech-to-text input using Web Speech API.
// Language set to kn-IN (Kannada - India).
// Shows live interim results while user is speaking.

import { useState, useRef, useEffect } from 'react'

export default function MicInput({ onResult, onError, disabled }) {
  const [isListening,  setIsListening]  = useState(false)
  const [isSupported,  setIsSupported]  = useState(true)
  const [showTooltip,  setShowTooltip]  = useState(false)
  const [interimText,  setInterimText]  = useState('')
  const recognitionRef = useRef(null)

  // ── Setup speech recognition ────────────────────────────
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setIsSupported(false)
      return
    }

    const recognition          = new SpeechRecognition()
    recognition.lang           = 'kn-IN'   // Kannada India
    recognition.interimResults = true       // Live results
    recognition.maxAlternatives = 3
    recognition.continuous     = false

    // ── On result ─────────────────────────────────────────
    recognition.onresult = (event) => {
      let finalText   = ''
      let interimText = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalText += transcript
        } else {
          interimText += transcript
        }
      }

      // Show live interim text in the button tooltip
      if (interimText) {
        setInterimText(interimText)
        onResult(interimText, false)   // false = not final
      }

      // Send final result to parent
      if (finalText) {
        setInterimText('')
        onResult(finalText, true)      // true = final
        setIsListening(false)
      }
    }

    // ── On error ──────────────────────────────────────────
    recognition.onerror = (event) => {
      setIsListening(false)
      setInterimText('')

      const ERROR_MESSAGES = {
        'no-speech':              'ಮಾತು ಕೇಳಿಸಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
        'audio-capture':          'ಮೈಕ್ ಸಿಗಲಿಲ್ಲ. ಅನುಮತಿ ನೀಡಿ.',
        'not-allowed':            'ಮೈಕ್ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ.',
        'network':                'ನೆಟ್‌ವರ್ಕ್ ದೋಷ ಸಂಭವಿಸಿದೆ.',
        'language-not-supported': 'ಕನ್ನಡ ಭಾಷೆ ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಬೆಂಬಲಿತವಾಗಿಲ್ಲ.',
        'service-not-allowed':    'ಮಾತಿನ ಸೇವೆ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ.',
        'aborted':                '',   // silent — user stopped
      }

      const msg = ERROR_MESSAGES[event.error]
      if (msg && onError) {
        onError(msg)
      }
    }

    // ── On end ────────────────────────────────────────────
    recognition.onend = () => {
      setIsListening(false)
      setInterimText('')
    }

    recognitionRef.current = recognition

    return () => {
      recognitionRef.current?.abort()
    }
  }, [onResult, onError])

  // ── Toggle mic ─────────────────────────────────────────
  function toggleMic() {
    if (!isSupported || disabled) return

    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      setInterimText('')
    } else {
      try {
        recognitionRef.current?.start()
        setIsListening(true)
      } catch (e) {
        // Recognition may already be running
        setIsListening(false)
      }
    }
  }

  // ── Tooltip text ───────────────────────────────────────
  const tooltipText = !isSupported
    ? 'This browser does not support speech recognition. Use Chrome.'
    : isListening
    ? interimText
      ? `"${interimText}"`
      : 'ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ...'
    : 'ಮೈಕ್ — ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ'

  return (
    <div style={styles.wrapper}>

      {/* ── Mic button ── */}
      <button
        style={{
          ...styles.micBtn,
          ...(isListening
            ? styles.micListening
            : isSupported && !disabled
            ? styles.micIdle
            : styles.micDisabled),
          cursor: (!isSupported || disabled) ? 'not-allowed' : 'pointer',
        }}
        onClick={toggleMic}
        disabled={!isSupported || disabled}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        title={tooltipText}
      >
        {/* Ripple effect when listening */}
        {isListening && (
          <>
            <span style={styles.ripple1} />
            <span style={styles.ripple2} />
          </>
        )}

        {/* Icon */}
        <span style={styles.icon}>
          {isListening ? '⏹' : '🎤'}
        </span>
      </button>

      {/* ── Tooltip ── */}
      {showTooltip && tooltipText && (
        <div style={styles.tooltip}>
          {tooltipText}
        </div>
      )}

      {/* ── Live interim text display ── */}
      {isListening && interimText && (
        <div style={styles.interimBox}>
          <span style={styles.interimDot} />
          <span style={styles.interimText}>{interimText}</span>
        </div>
      )}

    </div>
  )
}


// ════════════════════════════════════════════
// STYLES
// ════════════════════════════════════════════

const styles = {
  wrapper: {
    position: 'relative',
    display:  'flex',
    flexShrink: 0,
  },

  // ── Mic button ──
  micBtn: {
    width:          '48px',
    height:         '48px',
    borderRadius:   '50%',
    border:         '2px solid',
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'center',
    fontSize:       '1.1rem',
    transition:     'all 0.2s ease',
    flexShrink:     0,
    position:       'relative',
    overflow:       'hidden',
  },

  micIdle: {
    background:  '#1A4A6E',
    borderColor: 'rgba(200,151,58,0.5)',
    color:       '#93C5FD',
  },

  micListening: {
    background:  '#8B1A1A',
    borderColor: '#FCA5A5',
    color:       '#FCA5A5',
    animation:   'pulse 1.5s ease infinite',
  },

  micDisabled: {
    background:  '#374151',
    borderColor: '#4B5563',
    color:       '#6B7280',
  },

  icon: {
    position: 'relative',
    zIndex:   2,
  },

  // ── Ripple rings ──
  ripple1: {
    position:        'absolute',
    inset:           '-6px',
    borderRadius:    '50%',
    border:          '2px solid #FCA5A5',
    animation:       'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
    animationDelay:  '0s',
    pointerEvents:   'none',
  },
  ripple2: {
    position:        'absolute',
    inset:           '-14px',
    borderRadius:    '50%',
    border:          '1.5px solid rgba(252,165,165,0.4)',
    animation:       'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
    animationDelay:  '0.3s',
    pointerEvents:   'none',
  },

  // ── Tooltip ──
  tooltip: {
    position:      'absolute',
    bottom:        'calc(100% + 8px)',
    left:          '50%',
    transform:     'translateX(-50%)',
    background:    '#1A1209',
    color:         '#FAF4E8',
    fontFamily:    "'Noto Sans Kannada', serif",
    fontSize:      '0.75rem',
    padding:       '5px 12px',
    borderRadius:  '6px',
    whiteSpace:    'nowrap',
    border:        '1px solid rgba(200,151,58,0.3)',
    pointerEvents: 'none',
    zIndex:        20,
    maxWidth:      '220px',
    whiteSpace:    'normal',
    textAlign:     'center',
    boxShadow:     '0 4px 12px rgba(0,0,0,0.2)',
  },

  // ── Live interim text ──
  interimBox: {
    position:     'absolute',
    bottom:       'calc(100% + 8px)',
    right:        0,
    background:   '#8B1A1A',
    color:        '#FEE2E2',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '0.82rem',
    padding:      '6px 12px',
    borderRadius: '8px',
    maxWidth:     '250px',
    display:      'flex',
    alignItems:   'center',
    gap:          '6px',
    whiteSpace:   'pre-wrap',
    wordBreak:    'break-word',
    zIndex:       20,
    boxShadow:    '0 4px 12px rgba(0,0,0,0.2)',
    animation:    'fadeIn 0.2s ease',
  },
  interimDot: {
    width:        '6px',
    height:       '6px',
    background:   '#FCA5A5',
    borderRadius: '50%',
    flexShrink:   0,
    animation:    'pulse 1s infinite',
  },
  interimText: {
    lineHeight: 1.4,
  },
}