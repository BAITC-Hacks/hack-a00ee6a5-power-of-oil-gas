import { Outlet, Link, NavLink } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

export default function Layout() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark"><Sparkles size={18} /></span>
          <span>AI SANA <b>Challenge Hub</b></span>
        </Link>
        <nav className="nav-links">
          <NavLink to="/challenges">Каталог</NavLink>
          <NavLink to="/business/new" className="nav-cta">Создать задачу</NavLink>
        </nav>
      </header>
      <main><Outlet /></main>
      <footer className="footer">HackAlem AI / AI Sana MVP · Human-in-the-loop</footer>
    </div>
  )
}
