import { useTranslation } from 'react-i18next'
import { AuditEvent } from '../api'

const eventIcon: Record<string, string> = {
  received: '📥',
  ai_analysed: '🤖',
  decided: '✅',
}

export default function AuditTrail({ events }: { events: AuditEvent[] }) {
  const { t } = useTranslation()

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>{t('detail.audit')}</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {events.map((e, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, fontSize: 13 }}>
            <span>{eventIcon[e.event] || '•'}</span>
            <div>
              <span style={{ fontWeight: 500 }}>{e.event}</span>
              {e.detail.action != null && <span style={{ marginLeft: 6, fontWeight: 600 }}>→ {e.detail.action as string}</span>}
              {e.detail.remark != null && <div className="muted" style={{ marginTop: 2 }}>{e.detail.remark as string}</div>}
              <div className="muted">{new Date(e.created_at).toLocaleString()}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
