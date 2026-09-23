import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { Check, X, Users } from 'lucide-react'

export default function BusinessProposals() {
  const { id } = useParams()
  const [challenge, setChallenge] = useState(null)
  const [items, setItems] = useState([])
  const [error, setError] = useState('')

  async function load() {
    try {
      const [c, p] = await Promise.all([api.getChallenge(id), api.getProposals(id)])
      setChallenge(c.challenge); setItems(p.items)
    } catch (err) { setError(err.message) }
  }
  useEffect(() => { load() }, [id])

  async function decide(proposalId, decision) {
    try { await api.decideProposal(proposalId, decision); await load() } catch (err) { setError(err.message) }
  }

  return (
    <div className="container page-wide">
      <div className="catalog-header"><div><span className="eyebrow">Business dashboard</span><h1>{challenge?.title || 'Предложения команд'}</h1><p>AI не выбирает исполнителя — решение принимает представитель бизнеса.</p></div><div className="catalog-stat"><b>{items.length}</b><span>откликов</span></div></div>
      {error && <div className="alert error">{error}</div>}
      <div className="proposal-grid">
        {items.length === 0 && <div className="panel empty-state"><Users size={30}/><h3>Пока нет откликов</h3><p>Откройте Student view и отправьте тестовое предложение.</p></div>}
        {items.map(item => (
          <article className="panel proposal-card" key={item.id}>
            <div className="proposal-head"><div><span className="eyebrow">Команда</span><h3>{item.team_name}</h3></div><span className={`proposal-status ${item.status}`}>{item.status}</span></div>
            <div><b>Идея решения</b><p>{item.solution_idea}</p></div>
            <div><b>План</b><p>{item.plan}</p></div>
            <div className="proposal-meta"><span>Срок: {item.deadline}</span><a href={item.prototype_url} target="_blank" rel="noreferrer">Прототип ↗</a></div>
            <div className="decision-actions"><button className="button success-button" onClick={() => decide(item.id,'accepted')}><Check size={17}/> Accept</button><button className="button danger-button" onClick={() => decide(item.id,'rejected')}><X size={17}/> Reject</button></div>
          </article>
        ))}
      </div>
    </div>
  )
}
