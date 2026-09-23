import {t,useLocale} from '../i18n';
import { useEffect, useMemo, useState } from "react";
import {useAuth} from "../auth/AuthContext";
import {Link} from "react-router-dom";
import { api } from "../api/client";
import ChallengeCard from "../components/ChallengeCard";
import { Search, SlidersHorizontal } from "lucide-react";

export default function Catalog() {
  useLocale();

  const {user}=useAuth();
  const business=user.role === "business";
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [industry, setIndustry] = useState("Все");
  const [level, setLevel] = useState("Все");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active=true;
    const load=()=>api
      .getChallenges()
      .then((data) => {if(active){setItems(data.items);setError("")}})
      .catch((err) => {if(active)setError(err.message)})
      .finally(() => {if(active)setLoading(false)});
    load();
    const refresh=()=>{if(!document.hidden)load()};
    window.addEventListener("focus",refresh);
    document.addEventListener("visibilitychange",refresh);
    return()=>{active=false;window.removeEventListener("focus",refresh);document.removeEventListener("visibilitychange",refresh)};
  }, []);

  const industries = ["Все", ...new Set(items.map((x) => x.industry))];
  const filtered = useMemo(
    () =>
      items.filter((item) => {
        const text =
          `${item.title || ""} ${item.need || ""} ${item.raw_description || ""}`.toLowerCase();
        return (
          text.includes(query.toLowerCase()) &&
          (industry === "Все" || item.industry === industry) &&
          (level === "Все" || item.readiness_level === level)
        );
      }),
    [items, query, industry, level],
  );

  return (
    <div className="container page-wide">
      <div className="catalog-header">
        <div>
          <span className="eyebrow">{business?t("Кабинет бизнеса"):t("Кабинет исполнителя")}</span>
          <h1>{business?t("Мои задачи"):t("Найдите свою задачу")}</h1>
          <p>
            {business?t("Только ваши задачи: от первого черновика до принятого результата. Улучшайте описание с ИИ и выбирайте исполнителей."):t("Выбирайте из опубликованных задач всех компаний. Рейтинг помогает оценить готовность, но не ограничивает отклик.")}
          </p>
        </div>
        <div className="catalog-stat">
          <b>{items.length}</b>
          <span>{business?t("ваших задач"):t("задач в каталоге")}</span>
        </div>
      </div>
      {business && <div className="workspace-banner"><div><b>{t("Понятная задача привлекает сильные решения")}</b><p>{t("ИИ проверяет конкретность, данные и критерии приёмки. Каждый балл можно объяснить.")}</p></div><Link className="button primary" to="/business/new">{t("+ Создать задачу")}</Link></div>}
      <div className="filters panel">
        <label className="search-box">
          <Search size={17} />
          <input
            aria-label={t("Поиск задач")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("Поиск по задачам…")}
          />
        </label>
        <label>
          <SlidersHorizontal size={16} />
          <select
            aria-label={t("Отрасль")}
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          >
            {industries.map((x) => (
              <option key={x} value={x}>
                {x === "Все" ? t("Все отрасли") : t(x)}
              </option>
            ))}
          </select>
        </label>
        <label>
          <select
            aria-label={t("Готовность")}
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          >
            <option value="Все">{t("Любая готовность")}</option>
            <option value="Черновик">{t("Черновик")}</option>
            <option value="Рабочая">{t("Рабочая")}</option>
            <option value="Готовая">{t("Готовая")}</option>
            <option value="Приоритетная">{t("Приоритетная")}</option>
          </select>
        </label>
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="catalog-caption">
        <span>{t("Найдено:")}{" "}{filtered.length}</span>
        <span>{t("Сначала задачи с высоким рейтингом ↓")}</span>
      </div>
      {loading && (
        <div className="panel empty-state" role="status">{t("Загружаем задачи…")}{" "}</div>
      )}
      {!loading && !error && filtered.length === 0 && (
        <div className="panel empty-state">
          <h3>{t("Задачи не найдены")}</h3>
          <p>{business&&!items.length?t("Создайте первую задачу — она будет закреплена за вашим аккаунтом."):t("Попробуйте другой запрос или сбросьте фильтры.")}</p>
          <button
            className="button secondary"
            onClick={() => {
              setQuery("");
              setIndustry("Все");
              setLevel("Все");
            }}
          >{t("Сбросить фильтры")}{" "}</button>
        </div>
      )}
      <div className="challenge-grid">
        {filtered.map((item) => (
          <ChallengeCard challenge={item} key={item.id} />
        ))}
      </div>
    </div>
  );
}
