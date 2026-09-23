import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import ChallengeCard from '../components/ChallengeCard'
import { Search, SlidersHorizontal } from 'lucide-react'

export default function Catalog() {
  const [items, setItems] = useState([])
  const [query, setQuery] = useState('')
  const [industry, setIndustry] = useState('Все')
  const [level, setLevel] = useState('Все')
  const [error, setError] = useState('')

  useEffect(() => { api.getChallenges().then(data => setItems(data.items)).catch(err => setError(err.message)) }, [])

  const industries = ['Все', ...new Set(items.map(x => x.industry))]
  const filtered = useMemo(() => items.filter(item => {
    const text = `${item.title || ''} ${item.need || ''} ${item.raw_description || ''}`.toLowerCase()
    return text.includes(query.toLowerCase()) && (industry === 'Все' || item.industry === industry) && (level === 'Все' || item.readiness_level === level)
  }), [items, query, industry, level])

  return (
    <div className="container page-wide">
      <div className="catalog-header">
        <div><span className="eyebrow">Открытый каталог</span><h1>Business Challenges</h1><p>Все опубликованные задачи доступны всем командам независимо от рейтинга.</p></div>
        <div className="catalog-stat"><b>{items.length}</b><span>задач в пуле</span></div>
      </div>
      <div className="filters panel">
        <label className="search-box"><Search size={17}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Поиск по задачам…"/></label>
        <label><SlidersHorizontal size={16}/><select value={industry} onChange={e => setIndustry(e.target.value)}>{industries.map(x => <option key={x}>{x}</option>)}</select></label>
        <label><select value={level} onChange={e => setLevel(e.target.value)}><option>Все</option><option>Черновик</option><option>Рабочая</option><option>Готовая</option><option>Приоритетная</option></select></label>
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="challenge-grid">{filtered.map(item => <ChallengeCard challenge={item} key={item.id}/>)}</div>
    </div>
  )
}
