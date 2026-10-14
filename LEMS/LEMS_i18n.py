import os
import sys
import json

LANGUAGE_NAMES = {
    "en": "English",
    "fr": "Français",
    "es": "Español"
}

_current_lang = "en"
_en_strings = {}
_active_strings = {}

def get_base_dir():
    """Return the base directory whether running as script or PyInstaller frozen bundle."""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_lang_dir():
    """Return the absolute path to the lang directory."""
    return os.path.join(get_base_dir(), "lang")

def get_settings_file():
    """Return path to store user settings."""
    # When running frozen, save in executable directory or current working directory
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(os.path.dirname(sys.executable), "lems_settings.json")
    return os.path.join(get_base_dir(), "lems_settings.json")

def load_catalog(lang_code):
    """Load JSON file for a given language code."""
    filepath = os.path.join(get_lang_dir(), f"{lang_code}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading translation file {filepath}: {e}")
    return {}

def init_i18n():
    """Initialize i18n system, loading English base and saved preference."""
    global _current_lang, _en_strings, _active_strings
    _en_strings = load_catalog("en")
    
    saved_lang = "en"
    settings_file = get_settings_file()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                saved_lang = settings.get("language", "en")
        except Exception:
            saved_lang = "en"
            
    set_language(saved_lang, save=False)

def get_available_languages():
    """Find all available languages by looking at lang/*.json files."""
    lang_dir = get_lang_dir()
    available = {}
    if os.path.exists(lang_dir):
        for fname in os.listdir(lang_dir):
            if fname.endswith(".json"):
                code = fname[:-5]
                name = LANGUAGE_NAMES.get(code, code.upper())
                available[code] = name
    if not available:
        available["en"] = "English"
    return available

def set_language(lang_code, save=True):
    """Set current active language and optionally persist to settings file."""
    global _current_lang, _active_strings
    _current_lang = lang_code
    if lang_code == "en":
        _active_strings = _en_strings
    else:
        _active_strings = load_catalog(lang_code)

    if save:
        try:
            settings_file = get_settings_file()
            settings = {}
            if os.path.exists(settings_file):
                try:
                    with open(settings_file, "r", encoding="utf-8") as f:
                        settings = json.load(f)
                except Exception:
                    settings = {}
            settings["language"] = _current_lang
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving language preference: {e}")

def get_language():
    """Get the current language code."""
    return _current_lang

def t(key, **kwargs):
    """
    Translate a key into the active language with English fallback.
    Optional format kwargs can be supplied.
    """
    text = _active_strings.get(key)
    if text is None:
        text = _en_strings.get(key)
    if text is None:
        text = key
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

def t_field(name):
    """
    Translate a field identifier into user-facing display label.
    Falls back gracefully to capitalized spaced string.
    """
    key = f"field.{name}"
    translated = t(key)
    if translated != key:
        return translated
    # Check if ends with _1, _2, _3
    if len(name) > 2 and name[-2] == '_' and name[-1].isdigit():
        base = name[:-2]
        base_key = f"field.{base}"
        base_trans = t(base_key)
        if base_trans != base_key:
            return f"{base_trans} {name[-1]}"
    return name.capitalize().replace('_', ' ')

# Auto-initialize on module load
init_i18n()

