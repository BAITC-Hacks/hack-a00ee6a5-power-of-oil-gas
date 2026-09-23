import {t,useLocale} from '../i18n';
import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../api/client';
const statuses={pending:'На рассмотрении',accepted:'Выбраны',rejected:'Отклонено'};
export default function MyProposals(){
  useLocale();

 const [items,setItems]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 useEffect(()=>{api.myProposals().then(d=>setItems(d.items)).catch(e=>setError(e.message)).finally(()=>setLoading(false))},[]);
 return <div className="container page-wide"><div className="page-heading"><span className="eyebrow">{t("Кабинет исполнителя")}</span><h1>{t("Мои отклики")}</h1><p>{t("Решения бизнеса и подтверждённые результаты вашей работы.")}</p></div>{error&&<div className="alert error">{error}</div>}{loading?<p>{t("Загружаем…")}</p>:!items.length?<div className="panel empty-state"><h3>{t("Первый проект начинается с отклика")}</h3><Link className="button primary" to="/challenges">{t("Найти задачу")}</Link></div>:<div className="proposal-grid">{items.map(item=><article key={item.id} className="panel proposal-card"><div className="proposal-head"><h3>{item.challenge_title}</h3><span className={`proposal-status ${item.status}`}>{t(statuses[item.status])}</span></div><p>{item.solution_idea}</p><div className="proposal-meta"><span>{item.deadline}</span><b>{item.progress_points}{" "}{t("баллов прогресса")}</b></div>{item.milestones?.map(m=><div className="ai-note" key={m.id}>{m.points}/{{discovery:20,prototype:30,validation:50}[m.stage]} · {m.evidence}</div>)}<Link className="text-link" to={`/challenges/${item.challenge_id}`}>{t("Открыть задачу →")}</Link></article>)}</div>}</div>
}
