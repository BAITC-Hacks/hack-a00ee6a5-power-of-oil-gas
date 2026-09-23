import json
from pathlib import Path
from contextvars import ContextVar
language = ContextVar('language', default='ru')
LANGUAGES = {'ru':'Russian', 'kk':'Kazakh', 'en':'English'}
TRANSLATIONS = json.loads((Path(__file__).resolve().parents[2] / 'shared' / 'translations.json').read_text(encoding='utf-8'))
def translate(text, **values):
    result = TRANSLATIONS.get(text, {}).get(language.get(), text) if language.get() != 'ru' else text
    for key, value in values.items():
        result = result.replace('{'+key+'}', str(value))
    return result
