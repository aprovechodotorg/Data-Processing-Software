# verify_i18n.py
import json
import os
import sys
import LEMS_i18n as i18n

def test_catalogs():
    print("=== 1. Testing Catalogs Parity ===")
    en_path = os.path.join(i18n.get_lang_dir(), "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en = json.load(f)
    print(f"EN keys: {len(en)}")

    for lang in ["fr", "es", "pt"]:
        lang_path = os.path.join(i18n.get_lang_dir(), f"{lang}.json")
        assert os.path.exists(lang_path), f"Missing {lang_path}"
        with open(lang_path, "r", encoding="utf-8") as f:
            cat = json.load(f)
        print(f"{lang.upper()} keys: {len(cat)}")
        missing = set(en.keys()) - set(cat.keys())
        extra = set(cat.keys()) - set(en.keys())
        if missing:
            print(f"WARNING: Keys in EN but missing in {lang.upper()}: {missing}")
        if extra:
            print(f"WARNING: Keys in {lang.upper()} but missing in EN: {extra}")
        assert len(missing) == 0, f"{lang.upper()} catalog is missing keys from EN catalog"
        assert len(extra) == 0, f"{lang.upper()} catalog has unexpected extra keys"
    print("PASSED: 100% key parity across EN, FR, ES, and PT catalogs!")

def test_helpers():
    print("\n=== 2. Testing Helper Functions ===")
    # Reset to en
    i18n.set_language("en", save=False)
    assert i18n.get_language() == "en"
    assert i18n.t("tab.data_entry") == "Data Entry"
    assert i18n.t("btn.cancel") == "Cancel"
    assert i18n.t_field("test_name") == "Test name"
    
    # Switch to fr
    i18n.set_language("fr", save=False)
    assert i18n.get_language() == "fr"
    assert i18n.t("tab.data_entry") == "Saisie de données"
    assert i18n.t("btn.cancel") == "Annuler"
    assert i18n.t_field("test_name") == "Nom du test"
    
    # Switch to es
    i18n.set_language("es", save=False)
    assert i18n.get_language() == "es"
    assert i18n.t("tab.data_entry") == "Entrada de Datos"
    assert i18n.t("btn.cancel") == "Cancelar"
    assert i18n.t_field("test_name") == "Nombre de la prueba"

    # Switch to pt
    i18n.set_language("pt", save=False)
    assert i18n.get_language() == "pt"
    assert i18n.t("tab.data_entry") == "Entrada de Dados"
    assert i18n.t("btn.cancel") == "Cancelar"
    assert i18n.t_field("test_name") == "Nome do teste"

    # Test error popup messages across languages
    i18n.set_language("en", save=False)
    assert i18n.t("msg.error") == "Error"
    assert "require a numerical input" in i18n.t("err.validation.float")
    assert "open in another program" in i18n.t("err.file.open_permission", path="test.csv")

    i18n.set_language("fr", save=False)
    assert i18n.t("msg.error") == "Erreur"
    assert "nécessitent une valeur numérique" in i18n.t("err.validation.float")
    assert "ouvert dans un autre programme" in i18n.t("err.file.open_permission", path="test.csv")

    i18n.set_language("es", save=False)
    assert i18n.t("msg.error") == "Error"
    assert "requieren una entrada numérica" in i18n.t("err.validation.float")
    assert "está abierto en otro programa" in i18n.t("err.file.open_permission", path="test.csv")

    i18n.set_language("pt", save=False)
    assert i18n.t("msg.error") == "Erro"
    assert "requerem uma entrada numérica" in i18n.t("err.validation.float")
    assert "está aberto em outro programa" in i18n.t("err.file.open_permission", path="test.csv")

    # Test fallback on unknown key
    assert i18n.t("non.existent.key") == "non.existent.key"
    print("PASSED: All helper and error popup translation tests passed across all 4 languages!")

def test_ui_class():
    print("\n=== 3. Testing LEMSDataInput Structure & Tab Methods ===")
    import tkinter as tk
    try:
        root = tk.Tk()
        root.withdraw() # hide window
    except Exception as e:
        print(f"Tkinter display not available in environment: {e}. Skipping GUI instantiations.")
        return

    import LEMS_DataEntry_L1_ML as lems_app
    app = lems_app.LEMSDataInput(root)
    
    # Check data collection
    data = app.collect_all_data()
    assert isinstance(data, dict)
    print(f"Collected form fields count: {len(data)}")
    
    # Test adding dynamic tab
    tab_frame, inner = app.add_or_replace_dynamic_tab("test_tab", "My Tab")
    assert "test_tab" in app.managed_tabs
    assert app.managed_tabs["test_tab"] == tab_frame
    
    # Test French switch on app
    i18n.set_language("fr", save=False)
    app.rebuild_ui(saved_data=data)
    assert app.notebook.tab(0, "text") == "Saisie de données"
    assert "Veuillez sélectionner un dossier" in app.instructions_frame.get("1.0", "end")
    
    # Test Spanish switch on app
    i18n.set_language("es", save=False)
    app.rebuild_ui(saved_data=data)
    assert app.notebook.tab(0, "text") == "Entrada de Datos"
    assert "Por favor seleccione una carpeta" in app.instructions_frame.get("1.0", "end")

    # Test Portuguese switch on app
    i18n.set_language("pt", save=False)
    app.rebuild_ui(saved_data=data)
    assert app.notebook.tab(0, "text") == "Entrada de Dados"
    assert "Por favor, selecione uma pasta" in app.instructions_frame.get("1.0", "end")

    # Switch back to English
    i18n.set_language("en", save=False)
    app.rebuild_ui(saved_data=data)
    assert app.notebook.tab(0, "text") == "Data Entry"
    assert "Please select a folder" in app.instructions_frame.get("1.0", "end")
    
    root.destroy()
    print("PASSED: LEMSDataInput UI creation, data collection, and language toggle succeed!")

if __name__ == "__main__":
    test_catalogs()
    test_helpers()
    test_ui_class()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
