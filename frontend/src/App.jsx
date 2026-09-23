import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import NewChallenge from './pages/NewChallenge'
import ReviewChallenge from './pages/ReviewChallenge'
import Catalog from './pages/Catalog'
import ChallengeDetails from './pages/ChallengeDetails'
import BusinessProposals from './pages/BusinessProposals'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/business/new" element={<NewChallenge />} />
        <Route path="/business/challenge/:id" element={<ReviewChallenge />} />
        <Route path="/business/challenge/:id/proposals" element={<BusinessProposals />} />
        <Route path="/challenges" element={<Catalog />} />
        <Route path="/challenges/:id" element={<ChallengeDetails />} />
      </Route>
    </Routes>
  )
}
