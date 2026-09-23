import {t,getLanguage} from '../i18n';
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "Alem",
      "Accept-Language": getLanguage(),
        ...(options.headers || {}),
      },
      signal: AbortSignal.timeout(75000),
    });
  } catch (error) {
    throw new Error(t(
      error.name === "TimeoutError"
        ? "Сервер отвечает слишком долго. Повторите запрос."
        : "Не удалось связаться с сервером. Проверьте, запущен ли backend."),
    );
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    const error = new Error(t(
      Array.isArray(detail)
        ? t("Проверьте заполнение полей") + ": " + detail.map(x=>t({points:"Баллы этапа",evidence:"Что проверено и принято",email:"Email",password:"Пароль",display_name:"Имя или название компании"}[x.loc?.at(-1)] || x.loc?.at(-1) || "")).join(", ")
        : detail || "Ошибка запроса"),
    );
    error.status=response.status;
    if(response.status===401 && !path.startsWith("/auth/")) window.dispatchEvent(new Event("alem:session-expired"));
    throw error;
  }
  return payload;
}
export const api = {
  me:()=>request('/auth/me'),
  login:data=>request('/auth/login',{method:'POST',body:JSON.stringify(data)}),
  register:data=>request('/auth/register',{method:'POST',body:JSON.stringify(data)}),
  logout:()=>request('/auth/logout',{method:'POST'}),
  myProposals:()=>request('/my-proposals'),
  assessCard:(id,card)=>request(`/challenges/${id}/assess`,{method:'POST',body:JSON.stringify(card)}),
  analyzeChallenge: (data) =>
    request("/challenges/analyze", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  previewCard: (card) =>
    request("/challenges/preview", {
      method: "POST",
      body: JSON.stringify(card),
    }),
  buildCard: (id, answers) =>
    request(`/challenges/${id}/build-card`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
  confirmChallenge: (id, card, assessmentId) =>
    request(`/challenges/${id}/confirm`, {
      method: "PUT",
      body: JSON.stringify({ ...card, confirmed: true, assessment_id:assessmentId }),
    }),
  publishChallenge: (id) =>
    request(`/challenges/${id}/publish`, { method: "POST" }),
  getChallenges: () => request("/challenges"),
  getChallenge: (id) => request(`/challenges/${id}`),
  getTeams: () => request("/teams"),
  createProposal: (data) =>
    request("/proposals", { method: "POST", body: JSON.stringify(data) }),
  getProposals: (id) => request(`/challenges/${id}/proposals`),
  decideProposal: (id, decision) =>
    request(`/proposals/${id}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }),
  confirmMilestone: (id, data) =>
    request(`/proposals/${id}/milestones`, {
      method: "POST",
      body: JSON.stringify({ ...data, confirmed: true }),
    }),
};
