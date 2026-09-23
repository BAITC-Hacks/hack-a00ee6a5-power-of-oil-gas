import {t,useLocale} from '../i18n';
import { createContext, useContext, useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { api } from '../api/client';
const AuthContext=createContext(null);
export function AuthProvider({children}) {
  useLocale();

 const [user,setUser]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{api.me().then(d=>setUser(d.user)).catch(e=>{if(e.status!==401)setError(e.message)}).finally(()=>setLoading(false))},[]);
 useEffect(()=>{const expired=()=>{sessionStorage.clear();setUser(null)};window.addEventListener('alem:session-expired',expired);return ()=>window.removeEventListener('alem:session-expired',expired)},[]);
 async function logout(){await api.logout();sessionStorage.clear();setUser(null)}
 return <AuthContext.Provider value={{user,setUser,loading,error,logout}}>{children}</AuthContext.Provider>
}
export const useAuth=()=>useContext(AuthContext);
export function Protected({role,children}) {
  useLocale();

 const {user,loading,error}=useAuth();const location=useLocation();
 if(loading)return <div className="container page-narrow">{t("Проверяем вход…")}</div>;
 if(error)return <div className="container page-narrow"><div className="alert error">{error}</div><button className="button secondary" onClick={()=>window.location.reload()}>{t("Повторить")}</button></div>;
 if(!user)return <Navigate to="/login" state={{from:location.pathname}} replace/>;
 if(role&&user.role!==role)return <Navigate to="/challenges" replace/>;
 return children;
}
