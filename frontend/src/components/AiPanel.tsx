import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AiAnalysisResponse, api } from '../api'

interface Props {
  appId: string
  analysis: AiAnalysisResponse | null
  onRefresh: (a: AiAnalysisResponse) => void
}

const decisionColor: Record<string, string> = {
  accept: 'var(--success)',
  return: 'var(--warning)',
  reject: 'var(--danger)',
}

export default function AiPanel({ appId, analysis, onRefresh }: Props) {
  const { t, i18n } = useTranslation()
  const isKn = i18n.language === 'kn'
  const [loading, setLoading] = useState(false)

  async function runAnalysis(force = false) {
    setLoading(true)
    try {
      const result = await api.analyse(appId, force)
      onRefresh(result)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (!analysis) {
    return (
      <div style={{ background: 'var(--ai-bg)', border: '1px solid var(--ai-border)', borderRadius: 'var(--radius)', padding: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--primary)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.5px' }}>
          {t('detail.ai_panel')}
        </div>
        <button className="btn-primary" onClick={() => runAnalysis(false)} disabled={loading}>
          {loading ? '...' : t('detail.analyse')}
        </button>
      </div>
    )
  }

  if (!analysis.available) {
    return (
      <div style={{ background: 'var(--ai-bg)', border: '1px solid var(--ai-border)', borderRadius: 'var(--radius)', padding: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--primary)', textTransform: 'uppercase', marginBottom: 12 }}>
          {t('detail.ai_panel')}
        </div>
        <p className="muted">{t('detail.ai_unavailable')}</p>
        <button className="btn-secondary" style={{ marginTop: 12 }} onClick={() => runAnalysis(true)} disabled={loading}>
          {loading ? '...' : t('detail.regenerate')}
        </button>
      </div>
    )
  }

  const r = analysis.result!

  return (
    <div style={{ background: 'var(--ai-bg)', border: '1px solid var(--ai-border)', borderRadius: 'var(--radius)', padding: 20 }}>
      {/* Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.5px', background: '#dbeafe', padding: '3px 8px', borderRadius: 12 }}>
          {t('detail.ai_badge')}
        </span>
        <button className="btn-secondary" style={{ fontSize: 12, padding: '4px 10px' }} onClick={() => runAnalysis(true)} disabled={loading}>
          {loading ? '...' : t('detail.regenerate')}
        </button>
      </div>

      {/* Summary */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>{t('detail.ai_summary')}</div>
        <p style={{ fontSize: 14, lineHeight: 1.7 }}>{isKn ? r.summary_kn : r.summary_en}</p>
      </div>

      {/* Inconsistencies */}
      {r.inconsistencies.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>⚠ Inconsistencies</div>
          {r.inconsistencies.map((inc, i) => (
            <div key={i} style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 6, padding: '8px 12px', marginBottom: 6, fontSize: 13 }}>
              <strong>{inc.field}:</strong> {isKn ? inc.detail_kn : inc.detail_en}
            </div>
          ))}
        </div>
      )}

      {/* Suggested decision */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>{t('detail.ai_suggestion')}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: decisionColor[r.suggested_decision] }}>
            {r.suggested_decision.toUpperCase()}
          </span>
          <span className={`chip chip-${r.confidence === 'high' ? 'pass' : r.confidence === 'medium' ? 'review' : 'fail'}`} style={{ fontSize: 11 }}>
            {r.confidence}
          </span>
        </div>
      </div>

      {/* Reasons */}
      {r.reasons.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>{t('detail.ai_reasons')}</div>
          <ul style={{ paddingLeft: 18, fontSize: 13, lineHeight: 1.7 }}>
            {r.reasons.map((re, i) => (
              <li key={i}>{isKn ? re.text_kn : re.text_en}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Meta */}
      <div className="muted" style={{ fontSize: 11, borderTop: '1px solid var(--ai-border)', paddingTop: 8, marginTop: 8 }}>
        {analysis.cached ? '📦 cached' : `⚡ ${analysis.latency_ms}ms`} · {analysis.model}
      </div>
    </div>
  )
}
