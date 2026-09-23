import {t,useLocale} from '../i18n';
import {useAuth} from "../auth/AuthContext";
import { Link } from "react-router-dom";
import { ArrowUpRight, Database, Layers3, Users } from "lucide-react";

function tone(score) {
  if (score >= 90) return "priority";
  if (score >= 70) return "ready";
  if (score >= 40) return "working";
  return "draft";
}

export default function ChallengeCard({ challenge }) {
  useLocale();

  const {user}=useAuth();
  return (
    <article className="challenge-card">
      <div className="card-topline">
        <span className="industry-tag">
          <Layers3 size={14} /> {t(challenge.industry)}
        </span>
        <span className={`status-pill ${tone(challenge.score)}`}>
          {t(challenge.readiness_level)}
        </span>
      </div>
      <div className="applicant-row">{user.role === 'business' ? <Link className="applicant-count" to={`/business/challenge/${challenge.id}/proposals`} title={t("Количество уникальных претендентов, отправивших отклик")}><Users size={15}/><span>{t("Претендентов")}</span><b>{challenge.applicant_count ?? 0}</b><ArrowUpRight size={14}/></Link> : <span className="applicant-count" title={t("Количество уникальных претендентов, отправивших отклик")}><Users size={15}/><span>{t("Претендентов")}</span><b>{challenge.applicant_count ?? 0}</b></span>}</div>
      <h3>{challenge.title || t("Черновик задачи")}</h3>
      <p>{challenge.need || challenge.raw_description}</p>
      {user.role === "business" && <span className={`publication-state ${challenge.status}`}>{challenge.status === "published"?t("Опубликована"):challenge.status === "confirmed"?t("Готова к публикации"):t("Черновик · виден только вам")}</span>}
      <div className="card-meta">
        <span className="score-badge">{challenge.score}/100</span>
        <span>
          <Database size={14} />{" "}
          {challenge.data_materials ? t("Данные указаны") : t("Данные не указаны")}
        </span>
      </div>
      <Link className="text-link" to={`/challenges/${challenge.id}`}>{t("Подробнее о задаче")}{" "}<ArrowUpRight size={16} />
      </Link>
    </article>
  );
}
