import {t,useLocale} from '../i18n';
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Sparkles,
  BriefcaseBusiness,
  GraduationCap,
  MoveUpRight,
} from "lucide-react";
export default function Home() {
  useLocale();

  return (
    <div className="home">
      <section className="hero container">
        <div className="hero-copy">
          <span className="hero-kicker">
            <span className="live-dot" />{" "}{t("Площадка реальных возможностей")}{" "}</span>
          <h1>{t("Ваша задача.")}{" "}<br />{t("Их талант.")}{" "}<br />
            <em>{t("Общий результат.")}</em>
          </h1>
          <p className="hero-text">{t("Превратите бизнес-идею в понятную задачу.")}{" "}<br />{t("ИИ поможет с деталями, а студенческие команды предложат решение.")}{" "}</p>
          <div className="hero-actions">
            <Link to="/business/new" className="button primary">{t("Создать задачу")}{" "}<ArrowUpRight size={19} />
            </Link>
            <Link to="/challenges" className="button secondary">{t("Найти задачу")}{" "}<ArrowRight size={18} />
            </Link>
          </div>
          <div className="trust-row">
            <span>
              <Check size={16} />{" "}{t("Открытый выбор команд")}{" "}</span>
            <span>
              <Check size={16} />{" "}{t("Прозрачный рейтинг")}{" "}</span>
          </div>
        </div>
        <div className="hero-visual">
          <div className="visual-grid" />
          <div className="orbit-label">
            <Sparkles size={15} />{" "}{t("Из идеи — в действие")}{" "}</div>
          <div className="sample-card">
            <div className="sample-top">
              <span className="sample-icon">
                <BriefcaseBusiness size={20} />
              </span>
              <span>OIL & GAS</span>
              <span className="sample-id">{t("Пример задачи")}</span>
            </div>
            <h2>{t("Предсказывать поломки.")}{" "}<br />{t("Предотвращать простои.")}{" "}</h2>
            <p>{t("Прототип для анализа состояния насосного оборудования")}</p>
            <div className="sample-tags">
              <span>{t("Аналитика данных")}</span>
              <span>Machine Learning</span>
            </div>
            <div className="sample-rating">
              <div>
                <small>{t("Готовность к работе")}</small>
                <b>
                  90<span>/100</span>
                </b>
              </div>
              <span className="rating-orbit">90%</span>
            </div>
            <div className="sample-checks">
              <span>
                <Check size={15} />{" "}{t("Данные описаны")}{" "}</span>
              <span>
                <Check size={15} />{" "}{t("Результат определён")}{" "}</span>
              <span>
                <Check size={15} />{" "}{t("Критерии согласованы")}{" "}</span>
            </div>
          </div>
          <div className="floating-note">
            <span>
              <Sparkles size={20} />
            </span>
            <div>
              <b>{t("Хорошая задача начинается с вопроса")}</b>
              <small>{t("Помощник подскажет, что стоит уточнить")}</small>
            </div>
          </div>
        </div>
      </section>
      <section className="process-strip container">
        <span className="eyebrow">{t("От идеи до результата")}</span>
        <div>
          {[
            t("Опишите проблему"),
            t("Уточните с ИИ"),
            t("Опубликуйте задачу"),
            t("Выберите команду"),
          ].map((s, i) => (
            <span key={s}>
              <b>0{i + 1}</b>
              {s}
              {i < 3 && <ArrowRight size={17} />}
            </span>
          ))}
        </div>
      </section>
      <section className="container role-section">
        <div className="section-heading">
          <span className="eyebrow">{t("Две стороны. Одна цель.")}</span>
          <h2>{t("Здесь находят друг друга")}</h2>
        </div>
        <div className="role-grid">
          <Link to="/business/new" className="role-card">
            <BriefcaseBusiness size={25} />
            <span className="role-number">{t("01 / БИЗНЕС")}</span>
            <h3>{t("Идея, которой нужна команда")}</h3>
            <p>{t("Опишите задачу, повысьте её готовность и сравните предложения. Решение о сотрудничестве всегда за вами.")}{" "}</p>
            <span className="text-link">{t("Сформулировать задачу")}{" "}<MoveUpRight size={17} />
            </span>
          </Link>
          <Link to="/challenges" className="role-card student">
            <GraduationCap size={27} />
            <span className="role-number">{t("02 / КОМАНДЫ")}</span>
            <h3>{t("Талант, которому нужна практика")}</h3>
            <p>{t("Выбирайте интересные задачи без ограничений, предлагайте подход и получайте баллы за подтверждённые результаты.")}{" "}</p>
            <span className="text-link">{t("Посмотреть возможности")}{" "}<MoveUpRight size={17} />
            </span>
          </Link>
        </div>
      </section>
    </div>
  );
}
