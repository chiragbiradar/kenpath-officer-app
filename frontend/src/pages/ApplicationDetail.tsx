import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api, ApplicationDetail as AppDetail, AiAnalysisResponse } from '../api'
import RuleChecks from '../components/RuleChecks'
import AiPanel from '../components/AiPanel'
import DecisionBar from '../components/DecisionBar'
import AuditTrail from '../components/AuditTrail'

function DocRow({ doc }: { doc: AppDetail['documents'][0] }) {
  const { t, i18n } = useTranslation()
  const isKn = i18n.language === 'kn'
  const label: Record<string, string> = {
    aadhaar: isKn ? 'ಆಧಾರ್ ಕಾರ್ಡ್' : 'Aadhaar Card',
    dob_proof: isKn ? 'DOB ಪ್ರಮಾಣ (10ನೇ ಅಂಕಪಟ್ಟಿ)' : 'DOB Proof (10th Marksheet)',
    appointment_letter: isKn ? 'ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಪತ್ರ' : 'Appointment Letter',
    old_passport: isKn ? 'ಹಳೆ ಪಾಸ್‌ಪೋರ್ಟ್' : 'Old Passport',
    address_proof: isKn ? 'ವಿಳಾಸ ಪ್ರಮಾಣ' : 'Address Proof',
  }
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
      <span>{label[doc.type] || doc.type}</span>
      <span className={`chip ${doc.present ? 'chip-pass' : 'chip-fail'}`}>
        {doc.present ? t('detail.present') : t('detail.missing')}
      </span>
    </div>
  )
}

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const isKn = i18n.language === 'kn'

  const [app, setApp] = useState<AppDetail | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState<AiAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    api.application(id).then(data => {
      setApp(data)
      setAiAnalysis(data.ai_analysis)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>...</div>
  if (!app) return <div style={{ padding: 40, textAlign: 'center' }}>Not found</div>

  const aiDraftRemark = aiAnalysis?.result?.draft_remark_kn

  return (
    <div>
      {/* Header */}
      <header className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn-secondary" style={{ fontSize: 13 }} onClick={() => navigate('/')}>
            ← {t('detail.back')}
          </button>
          <h1 style={{ fontSize: 16 }}>{app.app_no}</h1>
          <span className={`chip chip-${app.status === 'pending' ? 'review' : app.status === 'accepted' ? 'pass' : 'fail'}`}>
            {t(`status.${app.status}`)}
          </span>
        </div>
        <span className={`chip chip-${app.deadline_status}`}>{t(`deadline.${app.deadline_status}`)}</span>
      </header>

      <div className="container" style={{ paddingBottom: 100 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>

          {/* Column 1: Applicant + Documents */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>{t('detail.applicant_info')}</h3>
              <table style={{ fontSize: 14, width: '100%' }}>
                <tbody>
                  {[
                    [isKn ? 'ಹೆಸರು' : 'Name', isKn ? app.applicant_name_kn : app.applicant_name],
                    [isKn ? 'ಲಿಂಗ' : 'Gender', app.gender],
                    [isKn ? 'ಜನ್ಮ ದಿನಾಂಕ' : 'Date of Birth', app.dob],
                    [isKn ? 'ಆಧಾರ್' : 'Aadhaar', app.aadhaar_masked],
                    [isKn ? 'ಫೋನ್' : 'Phone', app.phone_masked],
                    [isKn ? 'ಅರ್ಜಿ ವಿಧ' : 'Type', t(`queue.${app.application_type}`)],
                    [isKn ? 'ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್' : 'Appointment', app.appointment_date],
                  ].map(([k, v]) => (
                    <tr key={String(k)}>
                      <td style={{ color: 'var(--text-muted)', paddingRight: 12, paddingBottom: 6, verticalAlign: 'top', fontSize: 13 }}>{k}</td>
                      <td style={{ fontWeight: 500, paddingBottom: 6 }}>{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>{t('detail.documents')}</h3>
              {app.documents.map(doc => <DocRow key={doc.type} doc={doc} />)}
            </div>

            <div className="card">
              <AuditTrail events={app.audit} />
            </div>
          </div>

          {/* Column 2: Rule checks */}
          <div>
            <div className="card">
              <RuleChecks checks={app.rule_checks} />
            </div>
          </div>

          {/* Column 3: AI panel */}
          <div>
            <AiPanel
              appId={app.id}
              analysis={aiAnalysis}
              onRefresh={setAiAnalysis}
            />
          </div>
        </div>
      </div>

      <DecisionBar appId={app.id} status={app.status} aiDraftRemark={aiDraftRemark} />
    </div>
  )
}
