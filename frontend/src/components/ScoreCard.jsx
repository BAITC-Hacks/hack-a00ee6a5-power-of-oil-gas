function tone(score) {
  if (score >= 90) return 'priority'
  if (score >= 70) return 'ready'
  if (score >= 40) return 'working'
  return 'draft'
}

export default function ScoreCard({ rating, preview = false }) {
  if (!rating) return null
  const score = rating.score ?? 0
  return (
    <section className={`score-card ${tone(score)}`}>
      <div className="score-main">
        <div>
          <div className="eyebrow">{preview ? 'Предварительная полнота' : 'Официальный рейтинг'}</div>
          <div className="score-number">{score}<span>/100</span></div>
        </div>
        <span className={`status-pill ${tone(score)}`}>{rating.readiness_level}</span>
      </div>
      <div className="score-track"><div className="score-fill" style={{ width: `${score}%` }} /></div>
      {preview && <p className="muted compact">Баллы станут официальными только после ручного подтверждения карточки.</p>}
      {rating.breakdown?.length > 0 && (
        <div className="breakdown-grid">
          {rating.breakdown.map((item) => (
            <div className="breakdown-row" key={item.field}>
              <span>{item.label}</span>
              <b>{item.points}/{item.weight}</b>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
