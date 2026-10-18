# library/api/web/template_globals.py

from fastapi.templating import Jinja2Templates
from library.constant_health_pacs import ALL_ENUMS_CLASS, ALL_ENUMS_DICT
from library.languages.i18n import _, TRANSLATIONS, DEFAULT_LANG

def setup_template_globals(templates: Jinja2Templates) -> None:
    """Registra Enum, dizionari e il sistema i18n nei globali Jinja2."""
    
    # 1. Registrazione Enum
    for enum_cls in ALL_ENUMS_CLASS:
        templates.env.globals[enum_cls.__name__] = {
            item.name: item.value for item in enum_cls
        }

    # 2. Registrazione dizionari
    for name, dict_obj in ALL_ENUMS_DICT.items():
        templates.env.globals[name] = dict_obj

        

    # 3. Registrazione UNICA del multilingua (i18n)
    current_translations = TRANSLATIONS.get(DEFAULT_LANG, {})
    templates.env.globals["_"] = _
    templates.env.globals["TRANSLATIONS"] = current_translations