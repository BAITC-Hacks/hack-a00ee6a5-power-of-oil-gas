import {t,useLocale,questionText} from '../i18n';
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import ScoreCard from "../components/ScoreCard";
import {
  ArrowLeft,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  LoaderCircle,
  Send,
} from "lucide-react";

const fields = [
  ["title", "Название"],
  ["context", "Контекст"],
  ["need", "Потребность"],
  ["users", "Пользователи"],
  ["data_materials", "Данные и материалы"],
  ["constraints", "Ограничения"],
  ["expected_result", "Ожидаемый результат"],
  ["success_criteria", "Критерии успеха"],
  ["contact", "Контакт"],
  ["interaction_format", "Формат взаимодействия"],
];
const readDraft = (id) => {
  try {
    return JSON.parse(sessionStorage.getItem(`draft-${id}`) || "null");
  } catch {
    return null;
  }
};

export default function ReviewChallenge() {
  useLocale();

  const { id } = useParams();
  const [challenge, setChallenge] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [card, setCard] = useState({});
  const [stage, setStage] = useState("questions");
  const [index, setIndex] = useState(0);
  const [preview, setPreview] = useState(null);
  const [mode, setMode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [checked, setChecked] = useState(false);
  const [assessment, setAssessment] = useState(null);
  const [assessing,setAssessing]=useState(false);
  const previewSequence = useRef(0);

  useEffect(() => {
    let active = true;
    setLoaded(false);
    api
      .getChallenge(id)
      .then(({ challenge: c }) => {
        if (!active) return;
        const cachedDraft = readDraft(id);
        const saved =
          cachedDraft?.version === c.updated_at ? cachedDraft : null;
        let analysis;
        try {
          analysis = JSON.parse(
            sessionStorage.getItem(`analysis-${id}`) || "null",
          );
        } catch {}
        setChallenge(c);
        setMode(c.ai_mode || analysis?.ai_mode || "fallback");
        const qs = (c.ai_questions || []).filter((q) => typeof q === "object");
        const initial = qs.map((q) => ({
          ...q,
          answer:
            (c.answers || []).find((a) => a.field === q.field)?.answer || "",
        }));
        setAnswers(saved?.answers || initial);
        setCard(
          saved?.card ||
            Object.fromEntries(fields.map(([k]) => [k, c[k] || ""])),
        );
        setStage(
          c.status === "confirmed" && !saved
            ? "confirmed"
            : c.is_confirmed
            ? "review"
            : saved?.stage ||
                (c.answers?.length || !qs.length ? "review" : "questions"),
        );
        setIndex(saved?.index || 0);
        setLoaded(true);
      })
      .catch((err) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, [id]);

  useEffect(() => {
    if (loaded && stage !== "confirmed") {
      try {
        sessionStorage.setItem(
          `draft-${id}`,
          JSON.stringify({
            answers,
            card,
            stage,
            index,
            version: challenge.updated_at,
          }),
        );
      } catch {}
    }
  }, [answers, card, stage, index, id, loaded]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [stage]);

  useEffect(() => {
    if (!loaded || assessment) return;
    const seq = ++previewSequence.current;
    const values =
      stage === "questions"
        ? {
            ...card,
            ...Object.fromEntries(
              answers
                .filter((a) => a.answer.trim())
                .map((a) => [a.field, a.answer]),
            ),
          }
        : card;
    const timer = setTimeout(
      () =>
        api
          .previewCard(values)
          .then((result) => {
            if (seq === previewSequence.current && !assessment) setPreview(result);
          })
          .catch(() => {}),
      250,
    );
    return () => {
      clearTimeout(timer);
      previewSequence.current++;
    };
  }, [card, answers, stage, loaded, assessment]);

  async function build() {
    const completed = answers.filter((a) => a.answer.trim());
    if (completed.length < 3) {
      setError(
        t("Ответьте хотя бы на три вопроса. Если сведений нет, можно указать «Не знаю»."),
      );
      return;
    }
    setBusy(true);
    setError("");
    try {
      const data = await api.buildCard(
        id,
        completed.map(({ field, question, answer }) => ({
          field,
          question,
          answer,
        })),
      );
      setChallenge(data.challenge);
      setCard(
        Object.fromEntries(fields.map(([k]) => [k, data.challenge[k] || ""])),
      );
      setPreview(data.preview_rating);
      setStage("review");
      setAssessment(null);
      setChecked(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function evaluate() {
    setAssessing(true);setError('');setChecked(false);
    try {const data=await api.assessCard(id,card);setAssessment(data);setPreview(data.rating);}
    catch(err){setError(err.message)}finally{setAssessing(false)}
  }
  async function confirm(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api.confirmChallenge(id, card, assessment?.assessment_id);
      setChallenge(data.challenge);
      setStage("confirmed");
      setPreview(data.rating);
      sessionStorage.removeItem(`draft-${id}`);
      sessionStorage.removeItem(`analysis-${id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function publish() {
    setBusy(true);
    setError("");
    try {
      const data = await api.publishChallenge(id);
      setChallenge(data.challenge);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  function answer(value) {
    setAnswers((items) =>
      items.map((a, i) => (i === index ? { ...a, answer: value } : a)),
    );
  }
  if (!loaded)
    return (
      <div className="container page-narrow">
        <div className="panel form-panel" role="status">
          {error || t("Загружаем конструктор…")}
        </div>
      </div>
    );
  const current = answers[Math.min(index, answers.length - 1)];
  const completed = answers.filter((a) => a.answer.trim()).length;
  return (
    <div className="container split-layout">
      <div>
        <Link className="back-link" to="/challenges">
          <ArrowLeft size={16} />{" "}{t("Мои задачи")}{" "}</Link>
        <div className="stepper" aria-label={t("Этапы создания")}>
          {[t("Описание"), t("Уточнения"), t("Карточка"), t("Публикация")].map((s, i) => (
            <span
              key={s}
              className={
                i === (stage === "questions" ? 1 : stage === "review" ? 2 : 3)
                  ? "current"
                  : ""
              }
            >
              <b>{i + 1}</b>
              {s}
            </span>
          ))}
        </div>
        <div className="page-heading">
          <span className="eyebrow">{t("Конструктор задачи")}</span>
          <h1>
            {stage === "questions"
              ? t("Давайте уточним детали")
              : stage === "review"
                ? t("Всё на своих местах?")
                : challenge.status === "published"
                  ? t("Задача в открытом каталоге")
                  : t("Карточка подтверждена")}
          </h1>
          <p>
            {stage === "questions"
              ? t("Один вопрос за раз. Ваши ответы помогут команде оценить задачу и предложить решение.")
              : stage === "review"
                ? t("Проверьте карточку, затем запустите оценку ИИ. Он проверит содержание по критериям и объяснит каждый балл.")
                : t("Вы управляете публикацией и самостоятельно выбираете команды.")}
          </p>
        </div>
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        {stage === "questions" && current && (
          <section className="panel interview">
            <div className="interview-top">
              <span className="assistant-avatar">
                <Bot size={22} />
              </span>
              <div>
                <b>{t("Помощник по задачам")}</b>
                <small>
                  {mode === "openai"
                    ? t("ИИ-анализ описания")
                    : t("Локальный помощник · без внешнего ИИ")}
                </small>
              </div>
              <span className="interview-counter">
                {Math.min(index + 1, answers.length)} / {answers.length}
              </span>
            </div>
            <div className="question-progress">
              {answers.map((a, i) => (
                <button
                  key={a.field}
                  onClick={() => setIndex(i)}
                  className={`${i === index ? "active" : ""} ${a.answer.trim() ? "done" : ""}`}
                  aria-label={t("Вопрос {v0}: {v1}", {v0: (i + 1),v1: t(fields.find(([k]) => k === a.field)?.[1] || a.field)})}
                >
                  {a.answer.trim() ? <Check size={14} /> : i + 1}
                </button>
              ))}
            </div>
            <div className="question-body">
              <div className="question-topic">
                <span className="eyebrow">
                  {t(fields.find(([k]) => k === current.field)?.[1])}
                </span>
                {current.points > 0 && (
                  <span className="points-chip">{t("раздел: до")}{" "}{current.points}{" "}{t("баллов")}{" "}</span>
                )}
              </div>
              <h2>{questionText(current)}</h2>
              <p>{t(current.reason)}</p>
              <label htmlFor="question-answer">{t("Ваш ответ")}{" "}<textarea
                  id="question-answer"
                  rows={5}
                  maxLength={3000}
                  value={current.answer}
                  onChange={(e) => answer(e.target.value)}
                  placeholder={t(current.hint)}
                />
              </label>
              <div className="answer-meta">
                <span>{t("Сохраняется в этой вкладке")}</span>
                <span>{current.answer.length}/3000</span>
              </div>
              <button className="text-button" onClick={() => answer(t("Не знаю"))}>{t("Пока не знаю — уточню позже")}{" "}</button>
            </div>
            <div className="interview-actions">
              <button
                className="button secondary"
                disabled={index === 0}
                onClick={() => setIndex(index - 1)}
              >
                <ArrowLeft size={16} />{" "}{t("Назад")}{" "}</button>
              {index < answers.length - 1 ? (
                <button
                  className="button primary"
                  onClick={() => setIndex(index + 1)}
                >{t("Далее")}{" "}<ArrowRight size={16} />
                </button>
              ) : (
                <button
                  className="button primary"
                  disabled={busy || completed < 3}
                  onClick={build}
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={18} />
                  ) : (
                    <CheckCircle2 size={18} />
                  )}{" "}{t("Собрать карточку")}{" "}</button>
              )}
            </div>
            {completed >= 3 && index < answers.length - 1 && (
              <button
                className="text-button build-early"
                disabled={busy}
                onClick={build}
              >
                {busy
                  ? t("Собираем…")
                  : t("Перейти к карточке · ответов {v0}/{v1}", {v0: (completed),v1: (answers.length)})}
              </button>
            )}
          </section>
        )}
        {stage === "review" && (
          <form className="panel form-panel" onSubmit={confirm}>
            <div className="ai-note">
              <CheckCircle2 size={19} />{" "}{t("Ответы перенесены в соответствующие поля. Неизвестные сведения остаются пустыми.")}{" "}</div>
            <div className="field-grid">
              {fields.map(([key, label]) => (
                <label key={key} htmlFor={`field-${key}`}>
                  {t(label)}
                  {key === "title" ? " *" : ""}
                  <textarea
                    id={`field-${key}`}
                    rows={key === "title" ? 2 : 3}
                    required={key === "title"}
                    minLength={key === "title" ? 3 : undefined}
                    maxLength={key === "title" ? 180 : 4000}
                    value={card[key] || ""}
                    disabled={assessing || busy}
                    onChange={(e) => {
                      setAssessment(null);
                      setCard({ ...card, [key]: e.target.value });
                      setChecked(false);
                    }}
                    placeholder={t("Пока не указано")}
                  />
                </label>
              ))}
            </div>
            <div className="ai-evaluation-box"><div className="ai-evaluation-heading"><Bot size={24}/><div><b>{t("Теперь ИИ проверит качество")}</b><p>{t("Не длину ответа, а конкретность: что есть, чего не хватает и чем это подтверждено.")}</p></div></div><button type="button" className="button ai-button" disabled={assessing || busy} onClick={evaluate}>{assessing?<><LoaderCircle className="spin" size={18}/>{" "}{t("ИИ читает карточку и проверяет критерии…")}</>:<><Bot size={18}/>{assessment?.rating.mode === 'openai'?t("Посмотреть сохранённую оценку ИИ"):assessment?t("Повторить оценку с ИИ"):t("Оценить с ИИ")}</>}</button>{assessment && <p className="assessment-result">{assessment.rating.mode === 'openai'?t("ИИ-оценка готова"):t("Использованы локальные правила")}: <b>{assessment.rating.score}/100</b>{t(". Расчёт и рекомендации — в панели справа.")}</p>}{!assessment&&<p className="muted compact">{t("После правок нужна новая оценка. До неё справа показан предварительный расчёт по локальным правилам.")}</p>}</div>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={checked}
                onChange={(e) => setChecked(e.target.checked)}
                required
              />{" "}{t("Я проверил(а) карточку и подтверждаю указанные сведения.")}{" "}</label>
            <div className="decision-actions">
              {!challenge.is_confirmed && answers.length > 0 && (
                <button
                  type="button"
                  className="button secondary"
                  disabled={assessing || busy}
                  onClick={() => {setAssessment(null);setStage("questions")}}
                >{t("К вопросам")}{" "}</button>
              )}
              <button className="button primary" disabled={busy || assessing || !checked || !assessment}>
                {busy ? (
                  <LoaderCircle className="spin" size={18} />
                ) : (
                  <CheckCircle2 size={18} />
                )}{" "}{t("Подтвердить сведения")}{" "}</button>
            </div>
          </form>
        )}
        {stage === "confirmed" && (
          <div className="panel completion-panel">
            <span className="completion-icon">
              <CheckCircle2 size={38} />
            </span>
            <h2>
              {challenge.status === "published"
                ? t("Теперь команды могут откликаться")
                : t("Остался один шаг")}
            </h2>
            <p>
              {challenge.status === "published"
                ? t("Задача доступна всем командам. Дополняйте описание, сравнивайте предложения и подтверждайте реальные результаты.")
                : t("Опубликуйте задачу. Даже с небольшим рейтингом она будет доступна всем командам.")}
            </p>
            <div className="hero-actions">
              {challenge.status === "published" ? (
                <>
                  <Link className="button primary" to={`/challenges/${id}`}>{t("Открыть задачу")}{" "}<ArrowRight size={18} />
                  </Link>
                  <Link
                    className="button secondary"
                    to={`/business/challenge/${id}/proposals`}
                  >{t("Предложения команд")}{" "}</Link>
                </>
              ) : (
                <button
                  className="button primary"
                  onClick={publish}
                  disabled={busy}
                >
                  <Send size={18} />{" "}{t("Опубликовать задачу")}{" "}</button>
              )}
              <button
                className="button secondary"
                onClick={() => {
                  setStage("review");
                  setAssessment(null);
                  setChecked(false);
                }}
              >{t("Дополнить карточку")}{" "}</button>
            </div>
          </div>
        )}
      </div>
      <aside className="sticky-side">
        <ScoreCard
          rating={stage === "confirmed" ? challenge.rating : preview}
          preview={stage !== "confirmed"}
        />
        <div className="panel mini-panel">
          <span className="eyebrow">{t("Ваша исходная идея")}</span>
          <p>{challenge.raw_description}</p>
        </div>
        <div className="side-note">
          <Bot size={18} />
          <p>{t("Помощник уточняет и структурирует. Факты подтверждаете вы.")}</p>
        </div>
      </aside>
    </div>
  );
}
