import {t,useLocale} from './i18n';
import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import {AuthProvider,Protected} from "./auth/AuthContext";
import Login from "./pages/Login";
import MyProposals from "./pages/MyProposals";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import NewChallenge from "./pages/NewChallenge";
import ReviewChallenge from "./pages/ReviewChallenge";
import Catalog from "./pages/Catalog";
import ChallengeDetails from "./pages/ChallengeDetails";
import BusinessProposals from "./pages/BusinessProposals";

export default function App() {
  useLocale();

  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return (
    <AuthProvider><Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/my-proposals" element={<Protected role="performer"><MyProposals/></Protected>} />
        <Route path="/business/new" element={<Protected role="business"><NewChallenge/></Protected>} />
        <Route path="/business/challenge/:id" element={<Protected role="business"><ReviewChallenge/></Protected>} />
        <Route
          path="/business/challenge/:id/proposals"
          element={<Protected role="business"><BusinessProposals/></Protected>}
        />
        <Route path="/challenges" element={<Protected><Catalog/></Protected>} />
        <Route path="/challenges/:id" element={<Protected><ChallengeDetails/></Protected>} />
      </Route>
    </Routes></AuthProvider>
  );
}
