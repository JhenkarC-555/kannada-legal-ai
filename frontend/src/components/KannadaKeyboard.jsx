// src/components/KannadaKeyboard.jsx
// Virtual Kannada keyboard for users who don't have
// Kannada input method installed on their device.
//
// Sections:
//   1. Vowels        (ಸ್ವರಗಳು)
//   2. Consonants    (ವ್ಯಂಜನಗಳು)
//   3. Vowel signs   (ಮಾತ್ರೆಗಳು)
//   4. Numbers       (ಅಂಕಿಗಳು)
//   5. Legal words   (ಕಾನೂನು ಪದಗಳು)

import { useState } from 'react'

// ── Keyboard layout ─────────────────────────────────────────
const KEYBOARD_SECTIONS = [
  {
    id:    'vowels',
    label: 'ಸ್ವರಗಳು',
    hint:  'Vowels',
    keys:  [
      'ಅ', 'ಆ', 'ಇ', 'ಈ', 'ಉ', 'ಊ',
      'ಋ', 'ಎ', 'ಏ', 'ಐ', 'ಒ', 'ಓ', 'ಔ',
      'ಅಂ', 'ಅಃ',
    ],
  },
  {
    id:    'consonants1',
    label: 'ವ್ಯಂಜನಗಳು',
    hint:  'Consonants',
    keys:  [
      'ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ',
      'ಚ', 'ಛ', 'ಜ', 'ಝ', 'ಞ',
      'ಟ', 'ಠ', 'ಡ', 'ಢ', 'ಣ',
    ],
  },
  {
    id:    'consonants2',
    label: '',
    hint:  '',
    keys:  [
      'ತ', 'ಥ', 'ದ', 'ಧ', 'ನ',
      'ಪ', 'ಫ', 'ಬ', 'ಭ', 'ಮ',
      'ಯ', 'ರ', 'ಲ', 'ವ', 'ಶ',
    ],
  },
  {
    id:    'consonants3',
    label: '',
    hint:  '',
    keys:  [
      'ಷ', 'ಸ', 'ಹ', 'ಳ',
      'ಕ್ಷ', 'ಜ್ಞ', 'ತ್ರ', 'ಶ್ರ',
    ],
  },
  {
    id:    'matras',
    label: 'ಮಾತ್ರೆಗಳು',
    hint:  'Vowel Signs',
    keys:  [
      'ಾ', 'ಿ', 'ೀ', 'ು', 'ೂ',
      'ೃ', 'ೆ', 'ೇ', 'ೈ', 'ೊ',
      'ೋ', 'ೌ', 'ಂ', 'ಃ', '್',
    ],
  },
  {
    id:    'numbers',
    label: 'ಅಂಕಿಗಳು',
    hint:  'Kannada Numbers',
    keys:  [
      '೦', '೧', '೨', '೩', '೪',
      '೫', '೬', '೭', '೮', '೯',
    ],
  },
  {
    id:    'legal',
    label: 'ಕಾನೂನು ಪದಗಳು',
    hint:  'Legal Words',
    keys:  [
      'ಸೆಕ್ಷನ್',
      'ವಿಭಾಗ',
      'ಶಿಕ್ಷೆ',
      'ದಂಡ',
      'ಜಾಮೀನು',
      'ನ್ಯಾಯಾಲಯ',
      'ಪೊಲೀಸ್',
      'ಹಕ್ಕು',
      'ಅರ್ಜಿ',
      'ದೂರು',
      'ವಕೀಲ',
      'ಬಂಧನ',
      'ಆರೋಪಿ',
      'ಸಾಕ್ಷಿ',
      'ತೀರ್ಪು',
      'ಮೇಲ್ಮನವಿ',
      'ಜೈಲು',
      'ಆಸ್ತಿ',
      'ಭೂಮಿ',
      'ಮೋಸ',
      'ಹಲ್ಲೆ',
      'ಕಳ್ಳತನ',
      'ದರೋಡೆ',
      'ಹತ್ಯೆ',
    ],
  },
]


// ════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════

export default function KannadaKeyboard({ onInsert, onClose }) {
  const [buffer,          setBuffer]          = useState('')
  const [activeSection,   setActiveSection]   = useState('vowels')
  const [pressedKey,      setPressedKey]      = useState(null)

  // ── Key press ───────────────────────────────────────────
  function pressKey(char) {
    setBuffer(prev => prev + char)
    // Visual feedback
    setPressedKey(char)
    setTimeout(() => setPressedKey(null), 150)
  }

  // ── Backspace (handles multi-byte Kannada chars) ────────
  function backspace() {
    setBuffer(prev => {
      const chars = [...prev]   // spread handles Unicode correctly
      chars.pop()
      return chars.join('')
    })
  }

  // ── Space ───────────────────────────────────────────────
  function addSpace() {
    setBuffer(prev => prev + ' ')
  }

  // ── Clear buffer ────────────────────────────────────────
  function clearBuffer() {
    setBuffer('')
  }

  // ── Insert into query and close ─────────────────────────
  function insertText() {
    if (buffer.trim()) {
      onInsert(buffer)
      setBuffer('')
    }
  }

  // ── Insert and keep keyboard open ───────────────────────
  function insertAndContinue() {
    if (buffer.trim()) {
      onInsert(buffer)
      setBuffer('')
    }
  }

  const currentSection = KEYBOARD_SECTIONS.find(
    s => s.id === activeSection
  )

  return (
    <div style={styles.overlay} onClick={e => {
      if (e.target === e.currentTarget) onClose()
    }}>
      <div style={styles.keyboard}>

        {/* ── Header ── */}
        <div style={styles.header}>
          <div style={styles.headerLeft}>
            <span style={styles.headerIcon}>⌨️</span>
            <div>
              <div style={styles.headerTitle}>ಕನ್ನಡ ಕೀಬೋರ್ಡ್</div>
              <div style={styles.headerSub}>Kannada Virtual Keyboard</div>
            </div>
          </div>

          {/* Preview of typed text */}
          <div style={styles.preview}>
            {buffer
              ? buffer
              : <span style={styles.previewPlaceholder}>
                  ಅಕ್ಷರಗಳನ್ನು ಆಯ್ಕೆ ಮಾಡಿ...
                </span>
            }
          </div>

          <button style={styles.closeBtn} onClick={onClose}>
            ✕
          </button>
        </div>

        {/* ── Section tabs ── */}
        <div style={styles.tabs}>
          {KEYBOARD_SECTIONS.map(section => (
            section.label && (
              <button
                key={section.id}
                style={{
                  ...styles.tab,
                  ...(activeSection === section.id
                    ? styles.tabActive
                    : {}),
                }}
                onClick={() => setActiveSection(section.id)}
              >
                <span style={styles.tabLabel}>{section.label}</span>
                {section.hint && (
                  <span style={styles.tabHint}>{section.hint}</span>
                )}
              </button>
            )
          ))}
        </div>

        {/* ── Keys grid ── */}
        <div style={styles.keysArea}>

          {/* Show current section and continuations */}
          {KEYBOARD_SECTIONS
            .filter(s =>
              s.id === activeSection ||
              (activeSection === 'consonants1' &&
               (s.id === 'consonants2' || s.id === 'consonants3'))
            )
            .map(section => (
              <div key={section.id} style={styles.keySection}>
                <div style={styles.keysGrid}>
                  {section.keys.map((key, i) => (
                    <KeyButton
                      key={i}
                      char={key}
                      isLegal={section.id === 'legal'}
                      isPressed={pressedKey === key}
                      onPress={() => pressKey(key)}
                    />
                  ))}
                </div>
              </div>
            ))
          }

        </div>

        {/* ── Action row ── */}
        <div style={styles.actionRow}>

          {/* Space */}
          <button
            style={styles.actionBtn}
            onClick={addSpace}
          >
            ␣ ಅಂತರ
          </button>

          {/* Backspace */}
          <button
            style={styles.actionBtn}
            onClick={backspace}
          >
            ← ಅಳಿಸು
          </button>

          {/* Clear */}
          <button
            style={{ ...styles.actionBtn, ...styles.actionBtnRed }}
            onClick={clearBuffer}
          >
            ✕ ತೆರವು
          </button>

          {/* Spacer */}
          <div style={{ flex: 1 }} />

          {/* Insert & Continue */}
          <button
            style={{
              ...styles.insertBtn,
              opacity: buffer.trim() ? 1 : 0.4,
            }}
            onClick={insertAndContinue}
            disabled={!buffer.trim()}
          >
            + ಸೇರಿಸಿ
          </button>

          {/* Insert & Close */}
          <button
            style={{
              ...styles.insertCloseBtn,
              opacity: buffer.trim() ? 1 : 0.4,
            }}
            onClick={insertText}
            disabled={!buffer.trim()}
          >
            ✓ ಸೇರಿಸಿ & ಮುಚ್ಚಿ
          </button>

        </div>

        {/* ── Usage hint ── */}
        <div style={styles.usageHint}>
          Click outside keyboard or ✕ to close &nbsp;·&nbsp;
          ✓ ಸೇರಿಸಿ adds text to your query
        </div>

      </div>
    </div>
  )
}


// ── Key button component ─────────────────────────────────────
function KeyButton({ char, isLegal, isPressed, onPress }) {
  const [hovered, setHovered] = useState(false)

  return (
    <button
      style={{
        ...styles.key,
        ...(isLegal ? styles.keyLegal : {}),
        ...(hovered  ? styles.keyHover  : {}),
        ...(isPressed ? styles.keyPressed : {}),
      }}
      onClick={onPress}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {char}
    </button>
  )
}


// ════════════════════════════════════════════
// STYLES
// ════════════════════════════════════════════

const styles = {

  // ── Overlay ──
  overlay: {
    position:       'fixed',
    inset:          0,
    background:     'rgba(26,18,9,0.7)',
    backdropFilter: 'blur(4px)',
    zIndex:         1000,
    display:        'flex',
    alignItems:     'flex-end',
    justifyContent: 'center',
    animation:      'fadeIn 0.2s ease',
  },

  // ── Keyboard panel ──
  keyboard: {
    background:   '#1C1610',
    borderTop:    '2px solid #C8973A',
    borderLeft:   '1px solid rgba(200,151,58,0.2)',
    borderRight:  '1px solid rgba(200,151,58,0.2)',
    width:        '100%',
    maxWidth:     '900px',
    borderRadius: '16px 16px 0 0',
    boxShadow:    '0 -8px 40px rgba(0,0,0,0.5)',
    maxHeight:    '75vh',
    overflowY:    'auto',
    display:      'flex',
    flexDirection:'column',
    gap:          0,
  },

  // ── Header ──
  header: {
    display:        'flex',
    alignItems:     'center',
    gap:            '12px',
    padding:        '14px 16px',
    borderBottom:   '1px solid rgba(200,151,58,0.15)',
    position:       'sticky',
    top:            0,
    background:     '#1C1610',
    zIndex:         2,
  },
  headerLeft: {
    display:    'flex',
    alignItems: 'center',
    gap:        '10px',
    flexShrink: 0,
  },
  headerIcon: {
    fontSize: '1.4rem',
  },
  headerTitle: {
    fontFamily: "'Noto Sans Kannada', serif",
    color:      '#C8973A',
    fontSize:   '0.95rem',
    fontWeight: 600,
  },
  headerSub: {
    fontFamily:    "'DM Mono', monospace",
    color:         'rgba(200,151,58,0.4)',
    fontSize:      '0.65rem',
    letterSpacing: '0.5px',
  },

  // Preview box
  preview: {
    flex:         1,
    background:   'rgba(255,255,255,0.05)',
    border:       '1px solid rgba(200,151,58,0.25)',
    borderRadius: '8px',
    padding:      '8px 12px',
    minHeight:    '40px',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '1rem',
    color:        '#FAF4E8',
    lineHeight:   '1.5',
    wordBreak:    'break-all',
  },
  previewPlaceholder: {
    color:      'rgba(250,244,232,0.2)',
    fontSize:   '0.85rem',
    fontFamily: "'Noto Sans Kannada', serif",
  },

  closeBtn: {
    background:   'rgba(139,26,26,0.25)',
    border:       '1px solid rgba(139,26,26,0.4)',
    color:        '#FCA5A5',
    borderRadius: '6px',
    padding:      '6px 12px',
    cursor:       'pointer',
    fontSize:     '0.85rem',
    fontFamily:   'sans-serif',
    flexShrink:   0,
    transition:   'all 0.15s',
  },

  // ── Section tabs ──
  tabs: {
    display:    'flex',
    gap:        '4px',
    padding:    '10px 16px 0',
    flexWrap:   'wrap',
    borderBottom: '1px solid rgba(200,151,58,0.1)',
  },
  tab: {
    background:   'none',
    border:       '1px solid rgba(200,151,58,0.15)',
    borderBottom: 'none',
    borderRadius: '6px 6px 0 0',
    padding:      '6px 12px',
    cursor:       'pointer',
    display:      'flex',
    flexDirection:'column',
    alignItems:   'center',
    gap:          '1px',
    transition:   'all 0.15s',
  },
  tabActive: {
    background:   'rgba(200,151,58,0.12)',
    borderColor:  'rgba(200,151,58,0.4)',
    borderBottom: '1px solid #1C1610',
    marginBottom: '-1px',
  },
  tabLabel: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.82rem',
    color:      '#C8973A',
    fontWeight: 500,
  },
  tabHint: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.58rem',
    color:         'rgba(200,151,58,0.45)',
    letterSpacing: '0.3px',
  },

  // ── Keys area ──
  keysArea: {
    padding: '14px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    flex: 1,
  },
  keySection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  keysGrid: {
    display:  'flex',
    flexWrap: 'wrap',
    gap:      '5px',
  },

  // ── Individual key ──
  key: {
    background:   '#2A2017',
    border:       '1px solid rgba(200,151,58,0.2)',
    borderBottom: '2px solid rgba(200,151,58,0.35)',
    borderRadius: '6px',
    color:        '#FAF4E8',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '1rem',
    padding:      '9px 12px',
    cursor:       'pointer',
    minWidth:     '44px',
    textAlign:    'center',
    transition:   'all 0.1s',
    userSelect:   'none',
    lineHeight:   1.2,
  },
  keyHover: {
    background:   '#C8973A',
    color:        '#1A1209',
    borderColor:  '#E8B95A',
    transform:    'translateY(-1px)',
    boxShadow:    '0 3px 8px rgba(200,151,58,0.3)',
  },
  keyPressed: {
    background:   '#E8B95A',
    color:        '#1A1209',
    transform:    'translateY(1px)',
    boxShadow:    'none',
  },
  keyLegal: {
    background:   '#1A2A1A',
    borderColor:  'rgba(110,231,183,0.2)',
    color:        '#6EE7B7',
    fontSize:     '0.85rem',
    padding:      '8px 12px',
  },

  // ── Action row ──
  actionRow: {
    display:      'flex',
    gap:          '6px',
    padding:      '10px 16px',
    borderTop:    '1px solid rgba(200,151,58,0.1)',
    flexWrap:     'wrap',
    background:   '#161008',
    position:     'sticky',
    bottom:       0,
  },
  actionBtn: {
    background:   '#2A2017',
    border:       '1px solid rgba(200,151,58,0.25)',
    borderRadius: '6px',
    color:        '#C8973A',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '0.82rem',
    padding:      '8px 14px',
    cursor:       'pointer',
    transition:   'all 0.15s',
    whiteSpace:   'nowrap',
  },
  actionBtnRed: {
    borderColor: 'rgba(139,26,26,0.4)',
    color:       '#FCA5A5',
  },
  insertBtn: {
    background:   'rgba(26,74,46,0.4)',
    border:       '1px solid rgba(110,231,183,0.3)',
    borderRadius: '6px',
    color:        '#6EE7B7',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '0.82rem',
    padding:      '8px 16px',
    cursor:       'pointer',
    transition:   'all 0.15s',
    fontWeight:   500,
  },
  insertCloseBtn: {
    background:   '#C8973A',
    border:       '1px solid #E8B95A',
    borderRadius: '6px',
    color:        '#1A1209',
    fontFamily:   "'Noto Sans Kannada', serif",
    fontSize:     '0.82rem',
    fontWeight:   700,
    padding:      '8px 18px',
    cursor:       'pointer',
    transition:   'all 0.15s',
    whiteSpace:   'nowrap',
  },

  // ── Usage hint ──
  usageHint: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.65rem',
    color:         'rgba(200,151,58,0.3)',
    textAlign:     'center',
    padding:       '6px 16px 10px',
    letterSpacing: '0.3px',
  },
}