// src/api.js
// All backend API calls in one place.
// Uses Vite proxy (/api) so no CORS issues.
// Never call http://localhost:5000 directly from components.

import axios from 'axios'

// ── Axios instance ────────────────────────────────────────
// baseURL '/api' is forwarded to http://localhost:5000/api
// by Vite proxy defined in vite.config.js
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor ───────────────────────────────────
// Logs every request in development mode
api.interceptors.request.use(
  (config) => {
    console.log(`API → ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor ──────────────────────────────────
// Logs every response and catches errors globally
api.interceptors.response.use(
  (response) => {
    console.log(`API ← ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    const status  = error.response?.status
    const message = error.response?.data?.detail?.message
      || error.response?.data?.message
      || error.message
      || 'ಸರ್ವರ್ ದೋಷ ಸಂಭವಿಸಿದೆ'

    console.error(`API Error ${status}: ${message}`)
    return Promise.reject({ status, message })
  }
)


// ═══════════════════════════════════════════════
// API FUNCTIONS
// ═══════════════════════════════════════════════

// ── Health check ──────────────────────────────
// GET /api/health
// Check if backend and all components are running

export async function checkHealth() {
  try {
    const { data } = await api.get('/health')
    return data
  } catch {
    return { status: 'error' }
  }
}

// ── Ping ──────────────────────────────────────
// GET /api/ping
// Quick alive check

export async function ping() {
  try {
    const { data } = await api.get('/ping')
    return data
  } catch {
    return null
  }
}

// ── Get example queries ───────────────────────
// GET /api/query/examples
// Fetch example Kannada legal questions for sidebar

export async function getExamples() {
  try {
    const { data } = await api.get('/query/examples')
    return data.examples || []
  } catch {
    // Return hardcoded fallback if API fails
    return [
      {
        question:    'IPC ಸೆಕ್ಷನ್ 302 ಏನು?',
        description: 'Section 302 IPC information',
        intent:      'section_lookup',
      },
      {
        question:    'ಪೊಲೀಸ್ ಬಂಧಿಸಿದರೆ ನನ್ನ ಹಕ್ಕೇನು?',
        description: 'Rights when arrested',
        intent:      'rights_query',
      },
      {
        question:    'FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?',
        description: 'How to file FIR',
        intent:      'procedure_query',
      },
      {
        question:    'ಕಳ್ಳತನಕ್ಕೆ ಎಷ್ಟು ಜೈಲು ಶಿಕ್ಷೆ?',
        description: 'Punishment for theft',
        intent:      'penalty_query',
      },
      {
        question:    'ಜಾಮೀನು ಪಡೆಯುವ ಪ್ರಕ್ರಿಯೆ',
        description: 'Bail process',
        intent:      'procedure_query',
      },
      {
        question:    'RTI ಅರ್ಜಿ ಹೇಗೆ ಹಾಕಬೇಕು?',
        description: 'How to file RTI',
        intent:      'procedure_query',
      },
      {
        question:    'ಉಚಿತ ವಕೀಲರ ಸಹಾಯ ಹೇಗೆ ಪಡೆಯಬಹುದು?',
        description: 'Free legal aid',
        intent:      'rights_query',
      },
      {
        question:    'ಕೌಟುಂಬಿಕ ಹಿಂಸೆ ಆದರೆ ಎಲ್ಲಿ ದೂರು ನೀಡಬೇಕು?',
        description: 'Domestic violence complaint',
        intent:      'procedure_query',
      },
    ]
  }
}

// ── Get stats ─────────────────────────────────
// GET /api/query/stats
// Fetch knowledge base statistics for sidebar

export async function getStats() {
  try {
    const { data } = await api.get('/query/stats')
    return data
  } catch {
    return {
      knowledge_base: {
        ipc_sections:        28,
        karnataka_laws:      16,
        vikaspedia_articles:  8,
        manual_qa_pairs:     15,
      },
      vector_store: {
        total_documents: 0,
      },
    }
  }
}

// ── Send query ────────────────────────────────
// POST /api/query
// Main function — sends a Kannada legal question
// and returns the full pipeline response

export async function sendQuery({
  question,
  sessionId,
  topK  = 5,
  alpha = 0.6,
}) {
  const { data } = await api.post('/query', {
    question:   question,
    session_id: sessionId,
    language:   'kn',
    top_k:      topK,
    alpha:      alpha,
  })
  return data
}

// ── Submit feedback ───────────────────────────
// POST /api/feedback
// Record user rating for an answer

export async function submitFeedback({
  sessionId,
  question,
  rating,
  wasHelpful,
  comment,
}) {
  try {
    const { data } = await api.post('/feedback', {
      session_id:  sessionId,
      question:    question,
      rating:      rating,
      was_helpful: wasHelpful,
      comment:     comment,
    })
    return data
  } catch {
    return null
  }
}