// src/components/Sidebar.jsx
// Left panel showing:
//   - Example Kannada legal queries
//   - Supported laws list
//   - Dialect tags
//   - Knowledge base statistics

import { useEffect, useState } from 'react'
import { getExamples, getStats } from '../api.js'

export default function Sidebar({ onExampleClick }) {
  const [examples, setExamples] = useState([])
  const [stats,    setStats]    = useState(null)
  const [loading,  setLoading]  = useState(true)

  // ── Load examples and stats on mount ───────────────────
  useEffect(() => {
    async function loadData() {
      const [exData, stData] = await Promise.all([
        getExamples(),
        getStats(),
      ])
      setExamples(exData)
      setStats(stData)
      setLoading(false)
    }
    loadData()
  }, [])

  return (
    <aside style={styles.sidebar}>

      {/* ── Example queries ── */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>📋</span>
          <div>
            <h3 style={styles.sectionTitle}>ಉದಾಹರಣೆ ಪ್ರಶ್ನೆಗಳು</h3>
            <p style={styles.sectionHint}>Example Questions</p>
          </div>
        </div>

        <div style={styles.exampleList}>
          {loading ? (
            // Skeleton loading
            [1,2,3,4].map(i => (
              <div key={i} style={styles.skeletonBtn} />
            ))
          ) : (
            examples.map((ex, i) => (
              <ExampleButton
                key={i}
                question={ex.question}
                intent={ex.intent}
                onClick={() => onExampleClick(ex.question)}
              />
            ))
          )}
        </div>
      </div>

      {/* ── Supported laws ── */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>🏛️</span>
          <div>
            <h3 style={styles.sectionTitle}>ಕಾನೂನುಗಳು</h3>
            <p style={styles.sectionHint}>Supported Laws</p>
          </div>
        </div>

        <ul style={styles.lawList}>
          {SUPPORTED_LAWS.map((law, i) => (
            <li key={i} style={styles.lawItem}>
              <span style={styles.lawDot} />
              {law}
            </li>
          ))}
        </ul>
      </div>

      {/* ── Dialects ── */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>🗣️</span>
          <div>
            <h3 style={styles.sectionTitle}>ಉಪಭಾಷೆಗಳು</h3>
            <p style={styles.sectionHint}>Dialects Supported</p>
          </div>
        </div>

        <div style={styles.dialectRow}>
          {DIALECTS.map((d, i) => (
            <span key={i} style={styles.dialectTag}>{d}</span>
          ))}
        </div>
      </div>

      {/* ── Knowledge base stats ── */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>📊</span>
          <div>
            <h3 style={styles.sectionTitle}>ಜ್ಞಾನ ಭಂಡಾರ</h3>
            <p style={styles.sectionHint}>Knowledge Base</p>
          </div>
        </div>

        <div style={styles.statsGrid}>
          <StatCard
            num={stats?.vector_store?.total_documents || '--'}
            label="Documents"
          />
          <StatCard
            num={stats?.knowledge_base?.ipc_sections || 28}
            label="IPC Sections"
          />
          <StatCard
            num={stats?.knowledge_base?.karnataka_laws || 16}
            label="State Laws"
          />
          <StatCard
            num={stats?.knowledge_base?.manual_qa_pairs || 15}
            label="QA Pairs"
          />
        </div>
      </div>

      {/* ── Helplines ── */}
      <div style={{ ...styles.section, borderBottom: 'none' }}>
        <div style={styles.sectionHeader}>
          <span style={styles.sectionIcon}>📞</span>
          <div>
            <h3 style={styles.sectionTitle}>ಸಹಾಯ ಸಂಖ್ಯೆಗಳು</h3>
            <p style={styles.sectionHint}>Emergency Helplines</p>
          </div>
        </div>

        <div style={styles.helplineList}>
          {HELPLINES.map((h, i) => (
            <div key={i} style={styles.helplineItem}>
              <span style={styles.helplineName}>{h.name}</span>
              <span style={styles.helplineNum}>{h.number}</span>
            </div>
          ))}
        </div>
      </div>

    </aside>
  )
}

// ── Sub components ──────────────────────────────────────────

function ExampleButton({ question, intent, onClick }) {
  const [hovered, setHovered] = useState(false)
  const color = INTENT_COLORS[intent] || INTENT_COLORS.general

  return (
    <button
      style={{
        ...styles.exampleBtn,
        borderColor: hovered ? color : '#EFE5CC',
        background:  hovered ? '#FDF5E6' : '#FAFAF8',
        transform:   hovered ? 'translateX(3px)' : 'none',
      }}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span style={{
        ...styles.intentDot,
        background: color,
      }} />
      {question}
    </button>
  )
}

function StatCard({ num, label }) {
  return (
    <div style={styles.statCard}>
      <span style={styles.statNum}>{num}</span>
      <span style={styles.statLabel}>{label}</span>
    </div>
  )
}

// ── Static data ─────────────────────────────────────────────

const SUPPORTED_LAWS = [
  'IPC (Indian Penal Code)',
  'CrPC',
  'CPC',
  'Karnataka Land Revenue Act',
  'Karnataka Police Act',
  'RTI Act 2005',
  'Consumer Protection Act',
  'PWDVA 2005',
  'Legal Services Act',
]

const DIALECTS = ['Mysuru', 'Dharwad', 'Mangaluru', 'Bengaluru']

const HELPLINES = [
  { name: 'ಮಹಿಳಾ ಸಹಾಯ',   number: '181'          },
  { name: 'ಪೊಲೀಸ್',        number: '100'          },
  { name: 'ಕಾನೂನು ಸೇವೆ',   number: '15100'        },
  { name: 'ಗ್ರಾಹಕ ಸಹಾಯ',   number: '1800-11-4000' },
  { name: 'ಮಕ್ಕಳ ಸಹಾಯ',    number: '1098'         },
]

const INTENT_COLORS = {
  section_lookup:  '#1E40AF',
  rights_query:    '#065F46',
  penalty_query:   '#991B1B',
  procedure_query: '#92400E',
  document_help:   '#5B21B6',
  general:         '#6B7280',
}

// ── Styles ──────────────────────────────────────────────────

const styles = {
  sidebar: {
    width:          '280px',
    minWidth:       '280px',
    background:     '#FFFFFF',
    borderRight:    '1px solid #EFE5CC',
    overflowY:      'auto',
    display:        'flex',
    flexDirection:  'column',
    flexShrink:     0,
  },
  section: {
    padding:      '16px',
    borderBottom: '1px solid #EFE5CC',
  },
  sectionHeader: {
    display:     'flex',
    alignItems:  'flex-start',
    gap:         '8px',
    marginBottom:'10px',
  },
  sectionIcon: {
    fontSize:   '1rem',
    marginTop:  '2px',
    flexShrink: 0,
  },
  sectionTitle: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.88rem',
    fontWeight: 700,
    color:      '#1A1209',
    lineHeight: 1.3,
  },
  sectionHint: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.65rem',
    color:         '#6B7280',
    letterSpacing: '0.5px',
    marginTop:     '1px',
  },

  // Examples
  exampleList: {
    display:       'flex',
    flexDirection: 'column',
    gap:           '5px',
  },
  exampleBtn: {
    display:        'flex',
    alignItems:     'flex-start',
    gap:            '8px',
    background:     '#FAFAF8',
    border:         '1px solid #EFE5CC',
    borderRadius:   '6px',
    padding:        '8px 10px',
    fontSize:       '0.83rem',
    color:          '#3D2B10',
    cursor:         'pointer',
    textAlign:      'left',
    fontFamily:     "'Noto Sans Kannada', serif",
    transition:     'all 0.15s',
    lineHeight:     '1.4',
    width:          '100%',
  },
  intentDot: {
    width:     '7px',
    height:    '7px',
    borderRadius: '50%',
    flexShrink: 0,
    marginTop:  '5px',
  },

  // Skeleton
  skeletonBtn: {
    height:     '38px',
    borderRadius: '6px',
    background: 'linear-gradient(90deg, #EFE5CC 25%, #FAF4E8 50%, #EFE5CC 75%)',
    backgroundSize: '200% 100%',
    animation:  'shimmer 1.5s infinite',
    marginBottom: '5px',
  },

  // Laws
  lawList: {
    listStyle: 'none',
    display:   'flex',
    flexDirection: 'column',
    gap:       '4px',
  },
  lawItem: {
    display:      'flex',
    alignItems:   'center',
    gap:          '8px',
    fontSize:     '0.8rem',
    color:        '#3D2B10',
    padding:      '4px 8px',
    background:   '#F9F7F3',
    borderRadius: '4px',
    fontFamily:   'sans-serif',
  },
  lawDot: {
    width:        '6px',
    height:       '6px',
    borderRadius: '50%',
    background:   '#C8973A',
    flexShrink:   0,
  },

  // Dialects
  dialectRow: {
    display:  'flex',
    flexWrap: 'wrap',
    gap:      '6px',
  },
  dialectTag: {
    fontFamily:    'sans-serif',
    fontSize:      '0.75rem',
    padding:       '3px 10px',
    background:    '#FDF5E6',
    border:        '1px solid rgba(200,151,58,0.3)',
    borderRadius:  '12px',
    color:         '#3D2B10',
  },

  // Stats grid
  statsGrid: {
    display:             'grid',
    gridTemplateColumns: '1fr 1fr',
    gap:                 '8px',
  },
  statCard: {
    background:    '#F9F7F3',
    border:        '1px solid #EFE5CC',
    borderRadius:  '6px',
    padding:       '10px 8px',
    textAlign:     'center',
    display:       'flex',
    flexDirection: 'column',
    gap:           '3px',
  },
  statNum: {
    fontFamily: "'Playfair Display', serif",
    fontSize:   '1.4rem',
    fontWeight: 700,
    color:      '#C8973A',
    lineHeight: 1,
  },
  statLabel: {
    fontFamily:    "'DM Mono', monospace",
    fontSize:      '0.62rem',
    color:         '#6B7280',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },

  // Helplines
  helplineList: {
    display:       'flex',
    flexDirection: 'column',
    gap:           '5px',
  },
  helplineItem: {
    display:        'flex',
    justifyContent: 'space-between',
    alignItems:     'center',
    padding:        '5px 8px',
    background:     '#F9F7F3',
    borderRadius:   '4px',
  },
  helplineName: {
    fontFamily: "'Noto Sans Kannada', serif",
    fontSize:   '0.78rem',
    color:      '#3D2B10',
  },
  helplineNum: {
    fontFamily: "'DM Mono', monospace",
    fontSize:   '0.78rem',
    fontWeight: 600,
    color:      '#C8973A',
  },
}