import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { ArrowRight, Bot, LoaderCircle } from 'lucide-react'

export default function NewChallenge() {
  const navigate = useNavigate()
  const [raw, setRaw] = useState('Хотим использовать AI для уменьшения поломок насосного оборудования.')
  const [industry, setIndustry] = useState('Oil & Gas')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await api.analyzeChallenge({ raw_description: raw, industry })
      sessionStorage.setItem(`analysis-${data.challenge.id}`, JSON.stringify(data))
      navigate(`/business/challenge/${data.challenge.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container page-narrow">
      <div className="page-heading">
        <span className="eyebrow">Шаг 1 из 4</span>
        <h1>Опишите бизнес-задачу своими словами</h1>
        <p>Не заполняйте длинную анкету. Напишите то, что уже известно — AI найдёт пробелы и задаст уточняющие вопросы.</p>
      </div>

      <form className="panel form-panel" onSubmit={submit}>
        <label>Отрасль
          <select value={industry} onChange={(e) => setIndustry(e.target.value)}>
            <option>Oil & Gas</option><option>Energy</option><option>HR</option><option>Smart City</option><option>Education</option><option>Other</option>
          </select>
        </label>
        <label>Свободное описание проблемы
          <textarea value={raw} onChange={(e) => setRaw(e.target.value)} rows="8" minLength="10" required />
        </label>
        <div className="form-hint"><Bot size={18} /> AI использует только ваши факты. Неизвестные поля останутся пустыми.</div>
        {error && <div className="alert error">{error}</div>}
        <button className="button primary" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={18}/> Анализируем…</> : <>Анализировать с AI <ArrowRight size={18}/></>}</button>
      </form>
    </div>
  )
}
