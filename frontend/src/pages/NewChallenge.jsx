import {t,useLocale} from '../i18n';
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { ArrowRight, Bot, LoaderCircle } from "lucide-react";
const examples = [
  [
    "Oil & Gas",
    "Надёжность оборудования",
    "Хотим использовать AI для уменьшения поломок насосного оборудования.",
  ],
  [
    "HR",
    "Адаптация сотрудников",
    "Новым сотрудникам трудно найти инструкции. Хотим помощника для адаптации.",
  ],
  [
    "Energy",
    "Энергопотребление",
    "Есть почасовой CSV по потреблению энергии за 3 месяца. Хотим находить аномалии.",
  ],
  [
    "Smart City",
    "Очереди",
    "Хотим сократить очереди посетителей в сервисном центре.",
  ],
  [
    "Education",
    "Практика студентов",
    "Нужен сервис, который помогает студентам находить практические задачи.",
  ],
];
export default function NewChallenge() {
  useLocale();

  const navigate = useNavigate();
  const [raw, setRaw] = useState("");
  const [industry, setIndustry] = useState("Oil & Gas");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.analyzeChallenge({
        raw_description: raw,
        industry,
      });
      try {
        sessionStorage.setItem(
          `analysis-${data.challenge.id}`,
          JSON.stringify(data),
        );
      } catch {}
      navigate(`/business/challenge/${data.challenge.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="container page-narrow">
      <div className="stepper">
        {[t("Описание"), t("Уточнения"), t("Карточка"), t("Публикация")].map((s, i) => (
          <span key={s} className={i === 0 ? "current" : ""}>
            <b>{i + 1}</b>
            {s}
          </span>
        ))}
      </div>
      <div className="page-heading">
        <span className="eyebrow">{t("Начнём с вашей идеи")}</span>
        <h1>{t("Какую проблему")}{" "}<br />{t("вы хотите решить?")}{" "}</h1>
        <p>{t("Расскажите о задаче своими словами. Помощник найдёт недостающие сведения и поможет подготовить карточку для команды.")}{" "}</p>
      </div>
      <form className="panel form-panel" onSubmit={submit}>
        <label>{t("Отрасль")}{" "}<select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          >
            <option value="Oil & Gas">{t("Oil & Gas")}</option>
            <option value="Energy">{t("Energy")}</option>
            <option value="HR">{t("HR")}</option>
            <option value="Smart City">{t("Smart City")}</option>
            <option value="Education">{t("Education")}</option>
            <option value="Other">{t("Other")}</option>
          </select>
        </label>
        <label>{t("Описание задачи")}{" "}<textarea
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            rows={7}
            minLength={10}
            maxLength={4000}
            placeholder={t("Что происходит сейчас? Что хотелось бы изменить? Напишите всё, что уже известно о проблеме.")}
            required
          />
          <span className="input-counter">{raw.length}/4000</span>
        </label>
        <div>
          <span className="eyebrow">{t("Или начните с учебного примера")}</span>
          <div className="example-buttons" style={{ marginTop: 12 }}>
            {examples.map(([sector, title, text]) => (
              <button
                key={t(title)}
                type="button"
                onClick={() => {
                  setIndustry(sector);
                  setRaw(t(text));
                }}
              >
                {t(title)}
              </button>
            ))}
          </div>
        </div>
        <div className="form-hint">
          <Bot size={18} />{" "}{t("Помощник использует только ваши сведения. Вы сможете проверить и отредактировать карточку перед публикацией.")}{" "}</div>
        {error && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        <button
          className="button primary"
          disabled={loading || raw.trim().length < 10}
        >
          {loading ? (
            <>
              <LoaderCircle className="spin" size={18} />{" "}{t("Анализируем описание…")}{" "}</>
          ) : (
            <>{t("Уточнить задачу с помощником")}{" "}<ArrowRight size={18} />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
