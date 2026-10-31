import { useTranslation } from 'react-i18next'
import { RuleCheck } from '../api'

export default function RuleChecks({ checks }: { checks: RuleCheck[] }) {
  const { t, i18n } = useTranslation()
  const isKn = i18n.language === 'kn'

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>{t('detail.rule_checks')}</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {checks.map(c => (
          <div key={c.code} className="card" style={{ padding: '10px 14px', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <span className={`chip chip-${c.status}`} style={{ flexShrink: 0, marginTop: 2 }}>
              {t(`detail.${c.status}`)}
            </span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>
                {isKn ? c.message_kn : c.message_en}
              </div>
              {c.evidence && (
                <div className="muted" style={{ fontSize: 12, marginTop: 2, fontFamily: 'monospace' }}>
                  {c.evidence}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
