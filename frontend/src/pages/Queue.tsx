import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { api, ApplicationRow, Stats, Officer } from '../api'
import i18n from '../i18n'

function StatCard({ label, value, variant }: { label: string; value: number; variant?: string }) {
  const color = variant === 'danger' ? 'var(--danger)' : variant === 'warning' ? 'var(--warning)' : 'var(--primary)'
  return (
    <div className="card" style={{ textAlign: 'center', minWidth: 140 }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div className="muted" style={{ marginTop: 2 }}>{label}</div>
    </div>
  )
}

function DeadlineChip({ status }: { status: string }) {
  const { t } = useTranslation()
  return <span className={`chip chip-${status}`}>{t(`deadline.${status}`)}</span>
}

function FlagSummary({ flags }: { flags: ApplicationRow['flags'] }) {
  const { t } = useTranslation()
  const parts: string[] = []
  if (flags.fails > 0) parts.push(`${flags.fails} ${t('flags.fails')}`)
  if (flags.missing_docs > 0) parts.push(`${flags.missing_docs} ${t('flags.missing_docs')}`)
  if (flags.reviews > 0) parts.push(`${flags.reviews} ${t('flags.reviews')}`)
  if (parts.length === 0) return <span className="muted">—</span>
  return <span style={{ fontSize: 13, color: flags.fails > 0 ? 'var(--danger)' : 'var(--warning)' }}>{parts.join(', ')}</span>
}

export default function Queue() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const officer: Officer = JSON.parse(localStorage.getItem('officer') || '{}')

  const [stats, setStats] = useState<Stats | null>(null)
  const [apps, setApps] = useState<ApplicationRow[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('pending')
  const [lang, setLang] = useState(i18n.language)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [s, list] = await Promise.all([
        api.stats(),
        api.applications({ status, q: search, page: '1', limit: '50' }),
      ])
      setStats(s)
      setApps(list.data)
      setTotal(list.pagination.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [status, search])

  useEffect(() => { load() }, [load])

  function toggleLang() {
    const next = lang === 'kn' ? 'en' : 'kn'
    i18n.changeLanguage(next)
    localStorage.setItem('lang', next)
    setLang(next)
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('officer')
    navigate('/login')
  }

  const displayName = lang === 'kn' ? officer.name_kn : officer.name

  return (
    <div>
      <header className="page-header">
        <h1>🪪 {t('app_title')}</h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span className="muted" style={{ fontSize: 14 }}>{displayName}</span>
          <button className="lang-toggle" onClick={toggleLang}>
            {lang === 'kn' ? 'EN' : 'ಕನ್ನಡ'}
          </button>
          <button className="btn-secondary" style={{ fontSize: 13 }} onClick={logout}>
            {t('nav.logout')}
          </button>
        </div>
      </header>

      <div className="container">
        {/* Stats */}
        {stats && (
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
            <StatCard label={t('stats.pending')} value={stats.pending} />
            <StatCard label={t('stats.due_soon')} value={stats.due_soon} variant="warning" />
            <StatCard label={t('stats.overdue')} value={stats.overdue} variant="danger" />
            <StatCard label={t('stats.decided_today')} value={stats.decided_today} variant="primary" />
          </div>
        )}

        {/* Filters */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <input
            style={{ maxWidth: 320 }}
            placeholder={t('queue.search_placeholder')}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <select
            value={status}
            onChange={e => setStatus(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 'var(--radius)', border: '1px solid var(--border)', fontSize: 14, background: 'var(--surface)' }}
          >
            <option value="pending">{t('status.pending')}</option>
            <option value="accepted">{t('status.accepted')}</option>
            <option value="returned">{t('status.returned')}</option>
            <option value="rejected">{t('status.rejected')}</option>
          </select>
        </div>

        {/* Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>...</div>
          ) : apps.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>{t('queue.empty')}</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--surface-alt)', fontSize: 13, color: 'var(--text-muted)' }}>
                  <th style={th}>{t('queue.col_app_no')}</th>
                  <th style={th}>{t('queue.col_name')}</th>
                  <th style={th}>{t('queue.col_type')}</th>
                  <th style={th}>{t('queue.col_days')}</th>
                  <th style={th}>{t('queue.col_deadline')}</th>
                  <th style={th}>{t('queue.col_flags')}</th>
                  <th style={th}>{t('queue.col_action')}</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((app, i) => (
                  <tr key={app.id} style={{ borderTop: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--surface)' : 'var(--surface-alt)' }}>
                    <td style={td}><code style={{ fontSize: 13 }}>{app.app_no}</code></td>
                    <td style={td}>
                      <div>{lang === 'kn' ? app.applicant_name_kn : app.applicant_name}</div>
                    </td>
                    <td style={td}>
                      <span className="chip chip-on_track" style={{ fontSize: 11 }}>
                        {t(`queue.${app.application_type}`)}
                      </span>
                    </td>
                    <td style={{ ...td, textAlign: 'center' }}>{app.days_pending}d</td>
                    <td style={td}><DeadlineChip status={app.deadline_status} /></td>
                    <td style={td}><FlagSummary flags={app.flags} /></td>
                    <td style={td}>
                      <button className="btn-primary" style={{ fontSize: 13, padding: '5px 12px' }}
                        onClick={() => navigate(`/applications/${app.id}`)}>
                        {t('queue.view')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <p className="muted" style={{ marginTop: 8 }}>{total} {t('stats.pending').toLowerCase()}</p>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '10px 16px', textAlign: 'left', fontWeight: 600 }
const td: React.CSSProperties = { padding: '12px 16px' }
