import { Link } from 'react-router-dom'
import { ArrowRight, Building2, GraduationCap, ShieldCheck, Sparkles } from 'lucide-react'

export default function Home() {
  return (
    <div>
      <section className="hero container">
        <div className="hero-copy">
          <span className="hero-kicker"><Sparkles size={16} /> AI SANA Practical Challenge</span>
          <h1>От сырой бизнес-проблемы<br />до <em>student-ready challenge</em></h1>
          <p className="hero-text">AI помогает бизнесу уточнить задачу, человек подтверждает факты, прозрачный рейтинг показывает готовность, а студенты сами выбирают реальные challenges.</p>
          <div className="hero-actions">
            <Link to="/business/new" className="button primary">Я представитель бизнеса <ArrowRight size={18} /></Link>
            <Link to="/challenges" className="button secondary">Я студенческая команда</Link>
          </div>
          <div className="trust-row">
            <span><ShieldCheck size={16} /> AI не выдумывает факты</span>
            <span><ShieldCheck size={16} /> Человек подтверждает карточку</span>
            <span><ShieldCheck size={16} /> Бизнес выбирает команду вручную</span>
          </div>
        </div>
        <div className="hero-visual">
          <div className="flow-card raw"><small>01 · RAW PROBLEM</small><b>«Хотим AI для снижения поломок насосов»</b><span>Неполное описание</span></div>
          <div className="flow-line" />
          <div className="flow-card ai"><small>02 · AI CLARIFICATION</small><b>3+ уточняющих вопроса</b><span>Только по недостающим данным</span></div>
          <div className="flow-line" />
          <div className="flow-card ready"><small>03 · HUMAN CONFIRM</small><b>92 / 100 · Приоритетная</b><span>Готово к публикации</span></div>
        </div>
      </section>

      <section className="container role-grid">
        <article className="role-card"><Building2 size={28} /><h3>Для бизнеса</h3><p>Формулируйте качественные задачи и получайте открытые предложения от студенческих команд.</p></article>
        <article className="role-card"><GraduationCap size={28} /><h3>Для студентов</h3><p>Выбирайте реальные задачи из общего каталога и предлагайте собственный подход.</p></article>
      </section>
    </div>
  )
}
