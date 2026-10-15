import os
import sys
import json

try:
    from LEMS_i18n_data import EMBEDDED_CATALOGS as _EMBEDDED_CATALOGS
except Exception:
    _EMBEDDED_CATALOGS = {}

LANGUAGE_NAMES = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "pt": "Português"
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
    """Return the absolute path to the lang directory checking multiple candidate locations."""
    candidates = []

    # 1. PyInstaller temp extraction dir (_MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, "lang"))
        candidates.append(os.path.join(sys._MEIPASS, "LEMS", "lang"))

    # 2. Frozen executable directory (including macOS .app bundle paths)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "lang"))
        candidates.append(os.path.join(exe_dir, "LEMS", "lang"))
        # macOS app bundle: MyApp.app/Contents/MacOS/ -> MyApp.app/Contents/Resources/lang
        candidates.append(os.path.join(exe_dir, "..", "Resources", "lang"))
        # Next to the .app bundle itself:
        candidates.append(os.path.join(exe_dir, "..", "..", "..", "lang"))
        candidates.append(os.path.join(exe_dir, "..", "..", "..", "LEMS", "lang"))

    # 3. Directory of this Python file
    module_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(module_dir, "lang"))

    # 4. Current working directory
    candidates.append(os.path.join(os.getcwd(), "lang"))
    candidates.append(os.path.join(os.getcwd(), "LEMS", "lang"))

    for path in candidates:
        if os.path.exists(path) and os.path.isdir(path):
            return os.path.abspath(path)

    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "lang")
    return os.path.join(module_dir, "lang")

def get_settings_file():
    """Return path to store user settings."""
    # When running frozen, save in executable directory or current working directory
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(os.path.dirname(sys.executable), "lems_settings.json")
    return os.path.join(get_base_dir(), "lems_settings.json")

def load_catalog(lang_code):
    """Load JSON file for a given language code, with fallback to embedded catalog."""
    filepath = os.path.join(get_lang_dir(), f"{lang_code}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception as e:
            print(f"Error loading translation file {filepath}: {e}")
    # Fallback to embedded catalog compiled into Python bytecode
    if lang_code in _EMBEDDED_CATALOGS:
        return _EMBEDDED_CATALOGS[lang_code].copy()
    return {}

def init_i18n():
    """Initialize i18n system, loading English base and saved preference."""
    global _current_lang, _en_strings, _active_strings
    _en_strings = load_catalog("en")
    if not _en_strings and "en" in _EMBEDDED_CATALOGS:
        _en_strings = _EMBEDDED_CATALOGS["en"].copy()
    
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
    """Find all available languages by looking at lang/*.json files and embedded catalogs."""
    lang_dir = get_lang_dir()
    available = {}
    if os.path.exists(lang_dir):
        for fname in os.listdir(lang_dir):
            if fname.endswith(".json"):
                code = fname[:-5]
                name = LANGUAGE_NAMES.get(code, code.upper())
                available[code] = name
    # Also include any embedded languages
    for code in _EMBEDDED_CATALOGS:
        if code not in available:
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

