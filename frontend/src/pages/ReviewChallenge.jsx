import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import ScoreCard from '../components/ScoreCard'
import { Bot, CheckCircle2, LoaderCircle, PencilLine, Send } from 'lucide-react'

const fields = [
  ['title', 'Название'], ['context', 'Контекст'], ['need', 'Потребность'], ['users', 'Пользователи'],
  ['data_materials', 'Данные и материалы'], ['constraints', 'Ограничения'], ['expected_result', 'Ожидаемый результат'],
  ['success_criteria', 'Критерии успеха'], ['contact', 'Контакт'], ['interaction_format', 'Формат взаимодействия'],
]

export default function ReviewChallenge() {
  const { id } = useParams()
  const navigate = useNavigate()
  const cached = useMemo(() => {
    try { return JSON.parse(sessionStorage.getItem(`analysis-${id}`) || 'null') } catch { return null }
  }, [id])
  const [challenge, setChallenge] = useState(cached?.challenge || null)
  const [questions, setQuestions] = useState(cached?.questions || [])
  const [answers, setAnswers] = useState((cached?.questions || []).map(q => ({ question: q, answer: '' })))
  const [preview, setPreview] = useState(cached?.preview_rating || null)
  const [aiMode, setAiMode] = useState(cached?.ai_mode || '')
  const [stage, setStage] = useState(cached ? 'questions' : 'review')
  const [card, setCard] = useState({})
  const [officialRating, setOfficialRating] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!challenge) {
      api.getChallenge(id).then(({ challenge: item }) => {
        setChallenge(item)
        setQuestions(item.ai_questions || [])
        setAnswers((item.ai_questions || []).map(q => ({ question: q, answer: '' })))
        const next = {}
        fields.forEach(([key]) => { next[key] = item[key] || '' })
        setCard(next)
        setOfficialRating(item.rating)
      }).catch(err => setError(err.message))
    }
  }, [challenge, id])

  async function buildDraft(e) {
    e.preventDefault()
    const completed = answers.filter(item => item.answer.trim())
    if (completed.length < 3) {
      setError('Ответьте минимум на 3 уточняющих вопроса.')
      return
    }
    setError(''); setLoading(true)
    try {
      const data = await api.buildCard(id, completed)
      setChallenge(data.challenge)
      const next = {}
      fields.forEach(([key]) => { next[key] = data.challenge[key] || '' })
      setCard(next)
      setPreview(data.preview_rating)
      setAiMode(data.ai_mode)
      setStage('review')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function confirmCard(e) {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const data = await api.confirmChallenge(id, card)
      setChallenge(data.challenge)
      setOfficialRating(data.rating)
      setStage('confirmed')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function publish() {
    setLoading(true); setError('')
    try {
      await api.publishChallenge(id)
      navigate('/challenges')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  if (!challenge) return <div className="container page-narrow"><div className="panel">Загрузка…</div></div>

  return (
    <div className="container split-layout">
      <div>
        <div className="page-heading">
          <span className="eyebrow">Шаг 2–3 из 4</span>
          <h1>{stage === 'questions' ? 'AI нашёл недостающие сведения' : 'Проверьте карточку задачи'}</h1>
          <p>{stage === 'questions' ? 'Ответьте минимум на три вопроса. AI не должен додумывать ответы вместо вас.' : 'Текст AI — только черновик. Отредактируйте его и подтвердите вручную.'}</p>
        </div>

        {stage === 'questions' && (
          <form className="panel question-list" onSubmit={buildDraft}>
            <div className="ai-note"><Bot size={19}/> Режим AI: <b>{aiMode === 'openai' ? 'OpenAI API' : 'Local fallback'}</b></div>
            {answers.map((item, index) => (
              <label className="question-item" key={index}>
                <span><b>{String(index + 1).padStart(2, '0')}</b>{item.question}</span>
                <textarea rows="3" value={item.answer} onChange={(e) => {
                  const copy = [...answers]; copy[index] = { ...copy[index], answer: e.target.value }; setAnswers(copy)
                }} placeholder="Ответ бизнеса…" />
              </label>
            ))}
            {error && <div className="alert error">{error}</div>}
            <button className="button primary" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={18}/> Формируем…</> : <>Сформировать карточку <Send size={18}/></>}</button>
          </form>
        )}

        {stage !== 'questions' && (
          <form className="panel form-panel" onSubmit={confirmCard}>
            <div className="ai-note"><PencilLine size={19}/> Все поля доступны для ручного редактирования до подтверждения.</div>
            <div className="field-grid">
              {fields.map(([key, label]) => (
                <label key={key}>{label}
                  <textarea rows={key === 'title' || key === 'contact' ? 2 : 4} value={card[key] || ''} onChange={(e) => setCard({ ...card, [key]: e.target.value })} placeholder="Не указано" disabled={stage === 'confirmed'} />
                </label>
              ))}
            </div>
            {error && <div className="alert error">{error}</div>}
            {stage === 'review' && <button className="button primary" disabled={loading}><CheckCircle2 size={18}/> Подтвердить карточку человеком</button>}
            {stage === 'confirmed' && <button type="button" className="button primary" onClick={publish} disabled={loading}>Опубликовать в каталоге <Send size={18}/></button>}
          </form>
        )}
      </div>

      <aside className="sticky-side">
        <ScoreCard rating={stage === 'confirmed' ? officialRating : preview} preview={stage !== 'confirmed'} />
        <div className="panel mini-panel">
          <span className="eyebrow">Исходный текст</span>
          <p>{challenge.raw_description}</p>
        </div>
      </aside>
    </div>
  )
}
