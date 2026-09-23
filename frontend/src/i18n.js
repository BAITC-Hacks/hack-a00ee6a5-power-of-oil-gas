import {useSyncExternalStore} from 'react';
import translations from '../../shared/translations.json';
import questions from '../../shared/questions.json';
const reverse=new Map();for(const [key,entry] of Object.entries(translations)){for(const value of Object.values(entry))reverse.set(value,key)}
const listeners=new Set();
function stored(key,fallback){try{return localStorage.getItem(key)||fallback}catch{return fallback}}
let language=stored('alem-language','ru');if(!['kk','ru','en'].includes(language))language='ru';
let theme=stored('alem-theme',window.matchMedia?.('(prefers-color-scheme: dark)').matches?'dark':'light');if(!['dark','light'].includes(theme))theme='light';
function apply(){document.documentElement.lang=language;document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme;document.title=language==='kk'?'Alem · Тапсырмалар платформасы':language==='en'?'Alem · Challenge Hub':'Alem · Платформа задач'}
apply();
function emit(){apply();listeners.forEach(f=>f())}
export function setLanguage(value){if(!['kk','ru','en'].includes(value))return;language=value;try{localStorage.setItem('alem-language',value)}catch{}emit()}
export function setTheme(value){if(!['dark','light'].includes(value))return;theme=value;try{localStorage.setItem('alem-theme',value)}catch{}emit()}
export const getLanguage=()=>language;
export function useLocale(){useSyncExternalStore(callback=>{listeners.add(callback);return()=>listeners.delete(callback)},()=>language+':'+theme);return {language,theme,setLanguage,setTheme,t}}
window.addEventListener('storage',event=>{if(event.key==='alem-language'&&['kk','ru','en'].includes(event.newValue))language=event.newValue;else if(event.key==='alem-theme'&&['light','dark'].includes(event.newValue))theme=event.newValue;else return;emit()});
export function t(key,values={}){if(typeof key!=='string')return key;key=reverse.get(key)||key;let result=language==='ru'?key:(translations[key]?.[language]||key);return result.replace(/\{(\w+)\}/g,(match,k)=>values[k]??match)}

export function questionText(question){return question.question_translations?.[language] || ((question.language||'ru')===language || translations[question.question] || reverse.has(question.question) ? t(question.question) : t(questions[question.field]?.[0]||question.question))}
export function ratingSummary(rating){return rating.summary_translations?.[language] || ((rating.language||'ru')===language || translations[rating.summary] || reverse.has(rating.summary) ? t(rating.summary) : t('Оценка сохранена. Раскройте разделы, чтобы увидеть критерии и рекомендации.'))}
