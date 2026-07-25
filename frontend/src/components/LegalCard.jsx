// src/components/LegalCard.jsx
// Renders the legal answer with proper Kannada text.
// This is the main fix for the output accuracy issue.
//
// Key fixes:
//   1. Separates Kannada (kn) and English (en) sources
//   2. Shows Kannada text prominently at top
//   3. Proper Noto Sans Kannada font rendering
//   4. Shows section number, law name as citations
//   5. Shows implicature (implied meaning) if detected

import { useState } from 'react'

// ── Intent configuration ────────────────────────────────────
const INTENT_CONFIG = {
  section_lookup:  {
    icon:  '📖',
    label: 'ವಿಭಾಗ ಮಾಹಿತಿ',
    color: '#1E40AF',
    bg:    '#DBEAFE',
  },
  rights_query: {
    icon:  '🛡️',
    label: 'ಹಕ್ಕುಗಳ ಮಾಹಿತಿ',
    color: '#065F46',
    bg:    '#D1FAE5',
  },
  penalty_query: {
    icon:  '⚖️',
    label: 'ಶಿಕ್ಷೆ ಮಾಹಿತಿ',
    color: '#991B1B',
    bg:    '#FEE2E2',
  },
  procedure_query: {
    icon:  '📋',
    label: 'ಪ್ರಕ್ರಿಯೆ ಮಾಹಿತಿ',
    color: '#92400E',
    bg:    '#FEF3C7',
  },
  document_help: {
    icon:  '📝',
    label: 'ದಾಖಲೆ ಸಹಾಯ',
    color: '#5B21B6',
    bg:    '#EDE9FE',
  },
  general: {
    icon:  '💬',
    label: 'ಸಾಮಾನ್ಯ ಸಹಾಯ',
    color: '#374151',
    bg:    '#F3F4F6',
  },
}


// ════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════
export default function LegalCard({ data }) {
  const [showEnglish, setShowEnglish] = useState(false)

  if (!data) return null

  const {
    intent            = 'general',
    sources           = [],
    section_numbers   = [],
    law_names         = [],
    implicature_detected  = false,
    implicature_offense   = null,
    implicature_hint      = null,
    was_transliterated    = false,
    was_normalized        = false,
    disclaimer,
    processed_query,
  } = data

  // ── Separate Kannada and English sources ────────────────
  // This is the core fix — we show Kannada sources first
  const knSources = sources.filter(s => s.language === 'kn')
  const enSources = sources.filter(s => s.language === 'en')

  // Primary answer comes from top Kannada source
  const primaryKn = knSources[0] || null
  const primaryEn = enSources[0] || null

  const cfg = INTENT_CONFIG[intent] || INTENT_CONFIG.general

  return (
    <div style={styles.card}>

      {/* ── 1. Intent badge ── */}
      <div style={{
        ...styles.intentBadge,
        background: cfg.bg,
        color:      cfg.color,
      }}>
        <span>{cfg.icon}</span>
        <span>{cfg.label}</span>
        <span style={styles.intentConfidence}>
          {data.confidence
            ? `${Math.round(data.confidence * 100)}%`
            : ''}
        </span>
      </div>

      {/* ── 2. Implicature alert ── */}
      {implicature_detected && implicature_offense && (
        <div style={styles.implicatureBox}>
          <span style={styles.implicatureIcon}>🔍</span>
          <div>
            <div style={styles.implicatureTitle}>
              ಪ್ರಕರಣ ಪತ್ತೆ: {implicature_offense}
            </div>
            {implicature_hint && (
              <div style={styles.implicatureHint}>
                {implicature_hint}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── 3. Main Kannada answer ── */}
      {primaryKn ? (
        <div style={styles.answerBox}>

          {/* Kannada label */}
          <div style={styles.answerLangLabel}>
            <span style={styles.kannadaFlag}>ಕ</span>
            ಕನ್ನಡ ಉತ್ತರ
          </div>

          {/* Citation header */}
          {primaryKn.section_number &&
           primaryKn.section_number !== 'unknown' && (
            <div style={styles.citation}>
              <span style={styles.citationLaw}>
                {primaryKn.law_name || 'IPC'}
              </span>
              <span style={styles.citationSection}>
                ವಿಭಾಗ {primaryKn.section_number}
              </span>
              {primaryKn.score != null && (
                <span style={styles.citationScore}>
                  ↑ {Math.round(primaryKn.score * 100)}%
                </span>
              )}
            </div>
          )}

          {/* Kannada answer text */}
          <p style={styles.kannadaText}>
            {primaryKn.text}
          </p>

          {/* Second Kannada source if available */}
          {knSources[1] && (
            <>
              <div style={styles.divider} />
              <div style={styles.answerLangLabel}>
                ಸಂಬಂಧಿತ ಮಾಹಿತಿ
              </div>
              {knSources[1].section_number &&
               knSources[1].section_number !== 'unknown' && (
                <div style={styles.citation}>
                  <span style={styles.citationLaw}>
                    {knSources[1].law_name}
                  </span>
                  <span style={styles.citationSection}>
                    ವಿಭಾಗ {knSources[1].section_number}
                  </span>
                </div>
              )}
              <p style={styles.kannadaText}>
                {knSources[1].text}
              </p>
            </>
          )}

        </div>
      ) : (
        // Fallback when no Kannada source available
        <div style={styles.answerBox}>
          <div style={styles.answerLangLabel}>ಉತ್ತರ</div>
          <p style={styles.kannadaText}>
            {data.answer ||
              'ಕ್ಷಮಿಸಿ, ಈ ಪ್ರಶ್ನೆಗೆ ಸಂಬಂಧಿತ ಕನ್ನಡ ಮಾಹಿತಿ ' +
              'ದೊರೆಯಲಿಲ್ಲ. ಹೆಚ್ಚು ದತ್ತಾಂಶ ಸೇರಿಸಿದ ನಂತರ ' +
              'ಉತ್ತಮ ಉತ್ತರ ಸಿಗುತ್ತದೆ.'}
          </p>
        </div>
      )}

      {/* ── 4. English source toggle ── */}
      {primaryEn && (
        <div>
          <button
            style={styles.toggleBtn}
            onClick={() => setShowEnglish(prev => !prev)}
          >
            {showEnglish
              ? '▲ Hide English Source'
              : '▼ Show English Source'}
          </button>

          {showEnglish && (
            <div style={styles.englishBox}>
              <div style={styles.answerLangLabel}>
                🇬🇧 English Source
              </div>
              {primaryEn.section_number &&
               primaryEn.section_number !== 'unknown' && (
                <div style={styles.citation}>
                  <span style={styles.citationLaw}>
                    {primaryEn.law_name}
                  </span>
                  <span style={styles.citationSection}>
                    Section {primaryEn.section_number}
                  </span>
                </div>
              )}
              <p style={styles.englishText}>
                {primaryEn.text}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── 5. All sources list ── */}
      {sources.length > 0 && (
        <SourcesList sources={sources} />
      )}

      {/* ── 6. Metadata chips ── */}
      <MetaChips
        sectionNumbers={section_numbers}
        lawNames={law_names}
        wasTransliterated={was_transliterated}
        wasNormalized={was_normalized}
        implicatureDetected={implicature_detected}
        implicatureOffense={implicature_offense}
      />

      {/* ── 7. Disclaimer ── */}
      <div style={styles.disclaimer}>
        <span style={styles.disclaimerIcon}>⚠️</span>
        <span style={styles.disclaimerText}>
          {disclaimer ||
            'ಇದು ಕಾನೂನು ಸಲಹೆ ಅಲ್ಲ. ' +
            'ನಿಮ್ಮ ನಿರ್ದಿಷ್ಟ ಪ್ರಕರಣಕ್ಕೆ ' +
            'ಅರ್ಹ ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ.'}
        </span>
      </div>

    </div>
  )
}


// ════════════════════════════════════════════
// SUB COMPONENTS
// ════════════════════════════════════════════

// ── Sources list ────────────────────────────
function SourcesList({ sources }) {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? sources : sources.slice(0, 2)

  return (
    <div style={styles.sourcesSection}>
      <div style={styles.sourcesTitle}>
        📚 ಆಧಾರ ಮಾಹಿತಿ
        <span style={styles.sourcesCount}>
          ({sources.length})
        </span>
      </div>

      {visible.map((src, i) => (
        <SourceCard key={i} source={src} />
      ))}

      {sources.length > 2 && (
        <button
          style={styles.showMoreBtn}
          onClick={() => setExpanded(prev => !prev)}
        >
          {expanded
            ? '▲ ಕಡಿಮೆ ತೋರಿಸಿ'
            : `▼ ${sources.length - 2} ಹೆಚ್ಚು ಮೂಲಗಳು`}
        </button>
      )}
    </div>
  )
}

// ── Single source card ──────────────────────
function SourceCard({ source }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      style={{
        ...styles.sourceCard,
        background: hovered ? '#F5F0E8' : '#F9F7F3',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={styles.sourceHeader}>
        {/* Law badge */}
        <span style={styles.sourceLaw}>
          {source.law_name || 'Law'}
        </span>

        {/* Section number */}
        {source.section_number &&
         source.section_number !== 'unknown' && (
          <span style={styles.sourceSection}>
            § {source.section_number}
          </span>
        )}

        {/* Language tag */}
        <span style={{
          ...styles.sourceLang,
          background: source.language === 'kn'
            ? '#D1FAE5' : '#DBEAFE',
          color: source.language === 'kn'
            ? '#065F46' : '#1E40AF',
        }}>
          {source.language === 'kn' ? 'ಕನ್ನಡ' : 'English'}
        </span>

        {/* Score */}
        {source.score != null && (
          <span style={styles.sourceScore}>
            ↑ {Math.round(source.score * 100)}%
          </span>
        )}
      </div>

      {/* Source text preview */}
      <p style={styles.sourceText}>
        {source.text?.slice(0, 150)}
        {source.text?.length > 150 ? '...' : ''}
      </p>
    </div>
  )
}

// ── Metadata chips ──────────────────────────
function MetaChips({
  sectionNumbers,
  lawNames,
  wasTransliterated,
  wasNormalized,
  implicatureDetected,
  implicatureOffense,
}) {
  const hasAny =
    sectionNumbers.length > 0 ||
    lawNames.length > 0 ||
    wasTransliterated ||
    wasNormalized ||
    implicatureDetected

  if (!hasAny) return null

  return (
    <div style={styles.metaRow}>
      {sectionNumbers.map((sec, i) => (
        <span key={i} style={{ ...styles.chip, ...styles.chipGold }}>
          § {sec}
        </span>
      ))}
      {lawNames.map((law, i) => (
        <span key={i} style={{ ...styles.chip, ...styles.chipGold }}>
          {law}
        </span>
      ))}
      {wasTransliterated && (
        <span style={{ ...styles.chip, ...styles.chipGreen }}>
          🔤 ಲಿಪ್ಯಂತರ
        </span>
      )}
      {wasNormalized && (
        <span style={{ ...styles.chip, ...styles.chipGray }}>
          ✏️ ಸಾಮಾನ್ಯೀಕರಣ
        </span>
      )}
      {implicatureDetected && implicatureOffense && (
        <span style={{ ...styles.chip, ...styles.chipYellow }}>
          🔍 {implicatureOffense}
        </span>
      )}
    </div>
  )
}


// ════════════════════════════════════════════
// STYLES
// ════════════════════════════════════════════
const styles = {

  card: {
    background:    '#FFFFFF',
    border:        '1px solid #EFE5CC',
    borderRadius:  '12px',
    padding:       '18px',
    boxShadow:     '0 2px 12px rgba(0,0,0,0.06)',
    display:       'flex',
    flexDirection: 'column',
    gap:           '14px',
    animation:     'fadeIn 0.3s ease forwards',
  },

  // Intent badge
  intentBadge: {
    display:       'inline-flex',
    alignItems:    'center',
    gap:           '6px',
    fontSize:      '0.78rem',
    padding:       '4px 12px',
    borderRadius:  '20px',
    fontWeight:    600,
    width:         'fit-content',
    fontFamily:    "'Noto Sans Kannada', serif",
  },
  intentConfidence: {
    fontFamily: "'DM Mono', monospace",
    fontSize:   '0.68rem',
    opacity:    0.7,
    marginLeft: '2px',
  },

  // Implicature
  implicatureBox: {
    background:   '#FFFBEB',
    border:       '1px solid #FCD34D',
    borderRadius: '8px',
    padding:      '12px 14px',
    display:      'flex',
    gap:          '10px',
    alignItems:   'flex-start',
  },
  implicatureIcon: {
    fontSize:  '1.1rem',
    flexShrink: 0,
  },
  implicatureTitle: {
    fontFamily:  "'Noto Sans Kannada', serif",
    fontWeight:  600,
    fontSize:    '0.88rem',
    color:       '#92400E',
    marginBottom:'3px',
  },
  implicatureHint: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.82rem',
    color:      '#78350F',
    lineHeight: '1.5',
  },

  // Answer box — Kannada
  answerBox: {
    background:   '#FAFAF8',
    border:       '1px solid #EFE5CC',
    borderLeft:   '4px solid #C8973A',
    borderRadius: '0 8px 8px 0',
    padding:      '14px 16px',
    display:      'flex',
    flexDirection:'column',
    gap:          '10px',
  },
  answerLangLabel: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.68rem',
    color:         '#C8973A',
    letterSpacing: '1px',
    textTransform: 'uppercase',
    display:       'flex',
    alignItems:    'center',
    gap:           '6px',
  },
  kannadaFlag: {
    background:   '#C8973A',
    color:        '#1A1209',
    width:        '18px',
    height:       '18px',
    borderRadius: '3px',
    display:      'inline-flex',
    alignItems:   'center',
    justifyContent:'center',
    fontSize:     '0.7rem',
    fontWeight:   700,
    fontFamily:   "'Noto Sans Kannada', serif",
  },

  // Citation header
  citation: {
    display:    'flex',
    alignItems: 'center',
    gap:        '8px',
    flexWrap:   'wrap',
  },
  citationLaw: {
    fontFamily:   "'DM Mono', monospace",
    fontSize:     '0.72rem',
    fontWeight:   700,
    background:   '#1A1209',
    color:        '#C8973A',
    padding:      '2px 8px',
    borderRadius: '4px',
  },
  citationSection: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.82rem',
    fontWeight: 600,
    color:      '#3D2B10',
  },
  citationScore: {
    fontFamily:   "'DM Mono', monospace",
    fontSize:     '0.68rem',
    color:        '#065F46',
    background:   '#D1FAE5',
    padding:      '1px 7px',
    borderRadius: '10px',
    marginLeft:   'auto',
  },

  // Kannada answer text — most important style
  kannadaText: {
    fontFamily:  "'Noto Sans Kannada', serif",
    fontSize:    '1rem',
    lineHeight:  '1.9',
    color:       '#1A1209',
    whiteSpace:  'pre-wrap',
    wordBreak:   'break-word',
  },

  divider: {
    height:     '1px',
    background: '#EFE5CC',
    margin:     '4px 0',
  },

  // English toggle
  toggleBtn: {
    background:   'none',
    border:       '1px dashed #EFE5CC',
    borderRadius: '6px',
    padding:      '6px 12px',
    fontSize:     '0.75rem',
    color:        '#6B7280',
    cursor:       'pointer',
    fontFamily:   "'DM Mono', monospace",
    width:        '100%',
    textAlign:    'left',
    transition:   'all 0.15s',
  },
  englishBox: {
    background:    '#F8FAFF',
    border:        '1px solid #DBEAFE',
    borderLeft:    '4px solid #1E40AF',
    borderRadius:  '0 8px 8px 0',
    padding:       '12px 14px',
    marginTop:     '6px',
    display:       'flex',
    flexDirection: 'column',
    gap:           '8px',
  },
  englishText: {
    fontFamily: 'sans-serif',
    fontSize:   '0.9rem',
    lineHeight: '1.7',
    color:      '#1E3A5F',
    whiteSpace: 'pre-wrap',
    wordBreak:  'break-word',
  },

  // Sources
  sourcesSection: {
    display:       'flex',
    flexDirection: 'column',
    gap:           '6px',
  },
  sourcesTitle: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.72rem',
    fontWeight:    700,
    color:         '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    display:       'flex',
    alignItems:    'center',
    gap:           '4px',
  },
  sourcesCount: {
    fontWeight: 400,
    opacity:    0.6,
  },
  sourceCard: {
    border:       '1px solid #EFE5CC',
    borderLeft:   '3px solid #C8973A',
    borderRadius: '0 6px 6px 0',
    padding:      '10px 12px',
    transition:   'background 0.15s',
    cursor:       'default',
  },
  sourceHeader: {
    display:     'flex',
    alignItems:  'center',
    gap:         '6px',
    marginBottom:'5px',
    flexWrap:    'wrap',
  },
  sourceLaw: {
    fontFamily:   "'DM Mono', monospace",
    fontSize:     '0.7rem',
    fontWeight:   700,
    background:   '#1A1209',
    color:        '#C8973A',
    padding:      '2px 7px',
    borderRadius: '3px',
  },
  sourceSection: {
    fontFamily: "'DM Mono', monospace",
    fontSize:   '0.7rem',
    color:      '#6B7280',
  },
  sourceLang: {
    fontFamily:   "'DM Mono', monospace",
    fontSize:     '0.65rem',
    padding:      '1px 6px',
    borderRadius: '10px',
    fontWeight:   500,
  },
  sourceScore: {
    fontFamily:   "'DM Mono', monospace",
    fontSize:     '0.68rem',
    color:        '#065F46',
    background:   '#D1FAE5',
    padding:      '1px 6px',
    borderRadius: '10px',
    marginLeft:   'auto',
  },
  sourceText: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.83rem',
    color:      '#3D2B10',
    lineHeight: '1.5',
  },
  showMoreBtn: {
    background:   'none',
    border:       '1px dashed #EFE5CC',
    borderRadius: '6px',
    padding:      '5px 10px',
    fontSize:     '0.75rem',
    color:        '#6B7280',
    cursor:       'pointer',
    fontFamily:   "'Noto Sans Kannada', serif",
    width:        '100%',
    textAlign:    'center',
  },

  // Metadata chips
  metaRow: {
    display:  'flex',
    flexWrap: 'wrap',
    gap:      '6px',
  },
  chip: {
    fontSize:     '0.72rem',
    padding:      '3px 9px',
    borderRadius: '10px',
    fontFamily:   "'DM Mono', monospace",
  },
  chipGold: {
    background: '#FDF5E6',
    color:      '#3D2B10',
    border:     '1px solid rgba(200,151,58,0.35)',
  },
  chipGreen: {
    background: '#D1FAE5',
    color:      '#065F46',
    border:     '1px solid #A7F3D0',
  },
  chipGray: {
    background: '#F3F4F6',
    color:      '#6B7280',
    border:     '1px solid #E5E7EB',
  },
  chipYellow: {
    background: '#FEF3C7',
    color:      '#92400E',
    border:     '1px solid #FCD34D',
  },

  // Disclaimer
  disclaimer: {
    background:   '#FFF5F5',
    border:       '1px solid #FECACA',
    borderRadius: '8px',
    padding:      '10px 14px',
    display:      'flex',
    gap:          '8px',
    alignItems:   'flex-start',
  },
  disclaimerIcon: {
    flexShrink: 0,
    fontSize:   '0.95rem',
  },
  disclaimerText: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.82rem',
    color:      '#8B1A1A',
    lineHeight: '1.6',
  },
}