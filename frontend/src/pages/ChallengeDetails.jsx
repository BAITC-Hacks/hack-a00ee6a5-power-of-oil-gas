import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import ScoreCard from '../components/ScoreCard'
import { Send, ExternalLink } from 'lucide-react'

const labels = [
  ['context','Контекст'],['need','Потребность'],['users','Пользователи'],['data_materials','Данные и материалы'],
  ['constraints','Ограничения'],['expected_result','Ожидаемый результат'],['success_criteria','Критерии успеха'],
  ['contact','Контакт'],['interaction_format','Формат взаимодействия'],
]

export default function ChallengeDetails() {
  const { id } = useParams()
  const [challenge, setChallenge] = useState(null)
  const [teams, setTeams] = useState([])
  const [form, setForm] = useState({ team_id: '', team_name: '', solution_idea: '', plan: '', deadline: '', prototype_url: 'https://github.com/example/prototype' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api.getChallenge(id).then(data => setChallenge(data.challenge)).catch(err => setError(err.message))
    api.getTeams().then(data => setTeams(data.items)).catch(() => {})
  }, [id])

  function chooseTeam(teamId) {
    const team = teams.find(x => String(x.id) === String(teamId))
    setForm({ ...form, team_id: teamId, team_name: team?.name || '' })
  }

  async function submit(e) {
    e.preventDefault(); setError(''); setMessage('')
    try {
      await api.createProposal({ ...form, challenge_id: Number(id), team_id: form.team_id ? Number(form.team_id) : null })
      setMessage('Предложение отправлено. Решение принимает бизнес вручную.')
      setForm({ ...form, solution_idea: '', plan: '', deadline: '' })
    } catch (err) { setError(err.message) }
  }

  if (!challenge) return <div className="container page-narrow"><div className="panel">Загрузка…</div></div>

  return (
    <div className="container split-layout">
      <div>
        <div className="page-heading"><span className="eyebrow">{challenge.industry}</span><h1>{challenge.title}</h1><p>{challenge.raw_description}</p></div>
        <section className="panel detail-list">
          {labels.map(([key,label]) => <div className="detail-row" key={key}><span>{label}</span><p>{challenge[key] || 'Не указано'}</p></div>)}
        </section>

        <form className="panel form-panel proposal-form" onSubmit={submit}>
          <div><span className="eyebrow">Отклик команды</span><h2>Предложить решение</h2><p className="muted">AI не назначает исполнителей. Любая команда может подать отклик.</p></div>
          <label>Команда<select value={form.team_id} onChange={e => chooseTeam(e.target.value)} required><option value="">Выберите команду</option>{teams.map(t => <option value={t.id} key={t.id}>{t.name}</option>)}</select></label>
          <label>Идея решения<textarea rows="4" value={form.solution_idea} onChange={e => setForm({...form, solution_idea:e.target.value})} required/></label>
          <label>План<textarea rows="4" value={form.plan} onChange={e => setForm({...form, plan:e.target.value})} required/></label>
          <label>Срок<input value={form.deadline} onChange={e => setForm({...form, deadline:e.target.value})} placeholder="Например: 3 недели" required/></label>
          <label>Ссылка на прототип / репозиторий<input value={form.prototype_url} onChange={e => setForm({...form, prototype_url:e.target.value})} required/></label>
          {message && <div className="alert success">{message}</div>}{error && <div className="alert error">{error}</div>}
          <button className="button primary"><Send size={18}/> Отправить предложение</button>
        </form>
      </div>
      <aside className="sticky-side">
        <ScoreCard rating={challenge.rating} />
        <Link className="button secondary full" to={`/business/challenge/${id}/proposals`}>Business view <ExternalLink size={17}/></Link>
      </aside>
    </div>
  )
}
