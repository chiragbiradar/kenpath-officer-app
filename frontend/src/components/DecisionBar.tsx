import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api, AiAnalysisResult } from '../api'

interface Props {
  appId: string
  status: string
  aiDraftRemark?: string
}

export default function DecisionBar({ appId, status, aiDraftRemark }: Props) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [confirm, setConfirm] = useState<'return' | 'reject' | null>(null)
  const [remark, setRemark] = useState(aiDraftRemark || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (status !== 'pending') {
    return (
      <div style={{ padding: '16px 24px', background: 'var(--surface)', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <span className={`chip chip-${status === 'accepted' ? 'pass' : 'fail'}`} style={{ fontSize: 14 }}>
          {t(`status.${status}`)}
        </span>
      </div>
    )
  }

  async function decide(action: 'accept' | 'return' | 'reject') {
    setLoading(true)
    setError('')
    try {
      await api.decide(appId, action, remark || undefined)
      navigate('/')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error')
    } finally {
      setLoading(false)
      setConfirm(null)
    }
  }

  return (
    <>
      <div style={{
        position: 'sticky', bottom: 0, background: 'var(--surface)',
        borderTop: '2px solid var(--border)', padding: '14px 24px',
        display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap',
        boxShadow: '0 -2px 8px rgba(0,0,0,0.06)',
      }}>
        <button className="btn-success" onClick={() => decide('accept')} disabled={loading}>
          {t('decision.accept')}
        </button>
        <button className="btn-warning" onClick={() => setConfirm('return')} disabled={loading}>
          {t('decision.return')}
        </button>
        <button className="btn-danger" onClick={() => setConfirm('reject')} disabled={loading}>
          {t('decision.reject')}
        </button>
        {error && <span className="error-text">{error}</span>}
      </div>

      {confirm && (
        <div className="modal-overlay" onClick={() => setConfirm(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>{t(`decision.confirm_${confirm}`)}</h3>
            <div style={{ marginTop: 12 }}>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 14, fontWeight: 500 }}>
                {t('decision.remark_label')} *
              </label>
              <textarea
                rows={3}
                value={remark}
                onChange={e => setRemark(e.target.value)}
                placeholder={t('decision.remark_placeholder')}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setConfirm(null)}>{t('decision.confirm_cancel')}</button>
              <button
                className={confirm === 'reject' ? 'btn-danger' : 'btn-warning'}
                disabled={!remark.trim() || loading}
                onClick={() => decide(confirm)}
              >
                {loading ? '...' : t('decision.confirm_yes')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
