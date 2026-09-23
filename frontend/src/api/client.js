const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload.detail || 'Ошибка запроса')
  }
  return payload
}

export const api = {
  analyzeChallenge: (data) => request('/challenges/analyze', { method: 'POST', body: JSON.stringify(data) }),
  buildCard: (id, answers) => request(`/challenges/${id}/build-card`, { method: 'POST', body: JSON.stringify({ answers }) }),
  confirmChallenge: (id, card) => request(`/challenges/${id}/confirm`, { method: 'PUT', body: JSON.stringify({ ...card, confirmed: true }) }),
  publishChallenge: (id) => request(`/challenges/${id}/publish`, { method: 'POST' }),
  getChallenges: () => request('/challenges'),
  getChallenge: (id) => request(`/challenges/${id}`),
  getTeams: () => request('/teams'),
  createProposal: (data) => request('/proposals', { method: 'POST', body: JSON.stringify(data) }),
  getProposals: (challengeId) => request(`/challenges/${challengeId}/proposals`),
  decideProposal: (proposalId, decision) => request(`/proposals/${proposalId}/decision`, { method: 'POST', body: JSON.stringify({ decision }) }),
}
