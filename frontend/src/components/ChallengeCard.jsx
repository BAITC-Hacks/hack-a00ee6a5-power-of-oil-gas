import { Link } from 'react-router-dom'
import { ArrowUpRight, Database, Layers3 } from 'lucide-react'

function tone(score) {
  if (score >= 90) return 'priority'
  if (score >= 70) return 'ready'
  if (score >= 40) return 'working'
  return 'draft'
}

export default function ChallengeCard({ challenge }) {
  return (
    <article className="challenge-card">
      <div className="card-topline">
        <span className="industry-tag"><Layers3 size={14} /> {challenge.industry}</span>
        <span className={`status-pill ${tone(challenge.score)}`}>{challenge.readiness_level}</span>
      </div>
      <h3>{challenge.title || 'Без названия'}</h3>
      <p>{challenge.need || challenge.raw_description}</p>
      <div className="card-meta">
        <span className="score-badge">{challenge.score}/100</span>
        <span><Database size={14} /> {challenge.data_materials ? 'Данные указаны' : 'Данные не указаны'}</span>
      </div>
      <Link className="text-link" to={`/challenges/${challenge.id}`}>Открыть challenge <ArrowUpRight size={16} /></Link>
    </article>
  )
}
