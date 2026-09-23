import {t,useLocale} from '../i18n';
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { Check, X, Users, ArrowLeft, Award, Star } from "lucide-react";
const stages = {
  discovery: ["Исследование", 20],
  prototype: ["Прототип", 30],
  validation: ["Проверка результата", 50],
};
const statuses = {
  pending: "На рассмотрении",
  accepted: "Выбрана",
  rejected: "Отклонена",
};
function Progress({ item, onUpdate }) {
  useLocale();

  const remaining = Object.keys(stages).filter(
    (s) => !item.milestones?.some((m) => m.stage === s),
  );
  const [stage, setStage] = useState(remaining[0] || "");
  const [points, setPoints] = useState("");
  const [evidence, setEvidence] = useState("");
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const selected = remaining.includes(stage) ? stage : remaining[0];
  const maximum = stages[selected]?.[1] || 0;
  const validPoints = points !== "" && Number.isInteger(Number(points)) && Number(points) >= 0 && Number(points) <= maximum;
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.confirmMilestone(item.id, { stage: selected, evidence, points: Number(points) });
      setEvidence("");
      setPoints("");
      setChecked(false);
      await onUpdate();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="milestone-box">
      <b>
        <Award size={16} />{" "}{t("Подтверждённый прогресс ·")}{" "}
        {item.progress_points || 0}{" "}{t("баллов")}{" "}</b>
      {item.milestones?.length > 0 && (
        <ul className="milestone-list">
          {item.milestones.map((m) => (
            <li key={m.id}>
              <b>
                {t(stages[m.stage][0])} · {m.points}/{stages[m.stage][1]}
              </b>
              <div>{m.evidence}</div>
              <small>{t("Подтверждено бизнесом:")}{" "}{m.confirmed_at}</small>
            </li>
          ))}
        </ul>
      )}
      {item.status === "accepted" && remaining.length > 0 && (
        <form className="milestone-box" onSubmit={submit}>
          <label>{t("Завершённый этап")}{" "}<select value={selected} onChange={(e) => {setStage(e.target.value);setPoints("");setChecked(false)}}>
              {remaining.map((s) => (
                <option key={s} value={s}>
                  {t(stages[s][0])} · 0–{stages[s][1]}{" "}{t("баллов")}{" "}</option>
              ))}
            </select>
          </label>
          <label>{t("Оценка этапа (0–{max})",{max:maximum})}
            <input type="number" required min="0" max={maximum} step="1" value={points} onChange={e=>{setPoints(e.target.value);setChecked(false)}} placeholder={`0–${maximum}`} />
          </label>
          <label>{t("Что проверено и принято")}{" "}<textarea
              rows={3}
              minLength={10}
              maxLength={2000}
              required
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
              placeholder={t("Опишите фактический результат и способ проверки. Можно добавить ссылку на материалы.")}
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              required
            />{" "}{t("Я проверил(а) результат и принимаю этот этап.")}{" "}</label>
          {error && (
            <div className="alert error" role="alert">
              {error}
            </div>
          )}
          <button className="button secondary" disabled={busy || !checked || !validPoints}>
            {busy ? t("Сохраняем…") : t("Подтвердить этап и начислить баллы")}
          </button>
        </form>
      )}
    </div>
  );
}
export default function BusinessProposals() {
  useLocale();

  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(null);
  const [loading, setLoading] = useState(true);
  async function load() {
    try {
      const [c, p] = await Promise.all([
        api.getChallenge(id),
        api.getProposals(id),
      ]);
      setChallenge(c.challenge);
      setItems(p.items);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
    const refresh=()=>{if(!document.hidden)load()};
    window.addEventListener("focus",refresh);
    document.addEventListener("visibilitychange",refresh);
    return ()=>{window.removeEventListener("focus",refresh);document.removeEventListener("visibilitychange",refresh)};
  }, [id]);
  async function decide(proposalId, decision) {
    setBusy(proposalId);
    setError("");
    try {
      await api.decideProposal(proposalId, decision);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }
  return (
    <div className="container page-wide">
      <Link className="back-link" to={`/challenges/${id}`}>
        <ArrowLeft size={16} />{" "}{t("К задаче")}{" "}</Link>
      <div className="catalog-header">
        <div>
          <span className="eyebrow">{t("Кабинет бизнеса")}</span>
          <h1>{challenge?.title || t("Предложения команд")}</h1>
          <p>{t("Сравните подход, план и сроки. Можно выбрать несколько команд или отклонить все предложения.")}{" "}</p>
        </div>
        <div className="catalog-stat">
          <b>
            {items.filter((i) => i.status === "accepted").length}/{items.length}
          </b>
          <span>{t("выбрано / откликов")}</span>
        </div>
      </div>
      {error && (
        <div className="alert error" role="alert">
          {error}
        </div>
      )}
      <div className="proposal-grid">
        {loading ? (
          <div className="panel empty-state">{t("Загружаем предложения…")}</div>
        ) : (
          items.length === 0 && (
            <div className="panel empty-state">
              <Users size={30} />
              <h3>{t("Здесь появятся предложения")}</h3>
              <p>{t("Команды могут отправить идею и план на странице задачи.")}</p>
              <Link className="button secondary" to={`/challenges/${id}`}>{t("Открыть задачу")}{" "}</Link>
            </div>
          )
        )}
        {items.map((item) => (
          <article className="panel proposal-card" key={item.id}>
            <div className="proposal-head">
              <div>
                <span className="eyebrow">{t("Команда")}</span>
                <h3>{item.team_name}</h3>
              </div>
              <span className={`proposal-status ${item.status}`}>
                {t(statuses[item.status])}
              </span>
            </div>
            <div className="performer-reputation" title={t("Среднее за другие задания с оценками всех трёх этапов. Незавершённые задания не учитываются.")}>
              <Star size={19}/><div><span>{t("Средний рейтинг исполнителя")}</span><strong>{item.performer_rating?.completed_count ? `${item.performer_rating.average_score}/100` : t("Пока нет оценок")}</strong><small>{item.performer_rating?.completed_count ? t("Завершённых заданий: {count}",{count:item.performer_rating.completed_count}) : t("У претендента ещё нет завершённых оценённых заданий")}</small></div>
            </div>
            <div>
              <b>{t("Идея решения")}</b>
              <p>{item.solution_idea}</p>
            </div>
            <div>
              <b>{t("План работы")}</b>
              <p>{item.plan}</p>
            </div>
            <div className="proposal-meta">
              <span>{t("Срок:")}{" "}{item.deadline}</span>
              {/^https?:\/\//i.test(item.prototype_url) && (
                <a href={item.prototype_url} target="_blank" rel="noreferrer">{t("Открыть прототип ↗")}{" "}</a>
              )}
            </div>
            <div className="decision-actions">
              <button
                className="button success-button"
                disabled={busy === item.id || item.status === "accepted"}
                onClick={() => decide(item.id, "accepted")}
              >
                <Check size={17} />{" "}{t("Выбрать команду")}{" "}</button>
              <button
                className="button danger-button"
                disabled={busy === item.id || item.status === "rejected"}
                onClick={() => decide(item.id, "rejected")}
              >
                <X size={17} />{" "}{t("Отклонить")}{" "}</button>
            </div>
            {(item.status === "accepted" || item.milestones?.length > 0) && (
              <Progress item={item} onUpdate={load} />
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
