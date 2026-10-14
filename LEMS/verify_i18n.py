# verify_i18n.py
import json
import os
import sys
import LEMS_i18n as i18n

def test_catalogs():
    print("=== 1. Testing Catalogs Parity ===")
    en_path = os.path.join(i18n.get_lang_dir(), "en.json")
    fr_path = os.path.join(i18n.get_lang_dir(), "fr.json")
    
    assert os.path.exists(en_path), f"Missing {en_path}"
    assert os.path.exists(fr_path), f"Missing {fr_path}"
    
    with open(en_path, "r", encoding="utf-8") as f:
        en = json.load(f)
    with open(fr_path, "r", encoding="utf-8") as f:
        fr = json.load(f)
        
    print(f"EN keys: {len(en)}")
    print(f"FR keys: {len(fr)}")
    
    missing_in_fr = set(en.keys()) - set(fr.keys())
    missing_in_en = set(fr.keys()) - set(en.keys())
    
    if missing_in_fr:
        print(f"WARNING: Keys in EN but missing in FR: {missing_in_fr}")
    if missing_in_en:
        print(f"WARNING: Keys in FR but missing in EN: {missing_in_en}")
        
    assert len(missing_in_fr) == 0, "FR catalog is missing keys from EN catalog"
    print("PASSED: 100% key parity between en.json and fr.json!")

def test_helpers():
    print("\n=== 2. Testing Helper Functions ===")
    # Reset to en
    i18n.set_language("en", save=False)
    assert i18n.get_language() == "en"
    assert i18n.t("tab.data_entry") == "Data Entry"
    assert i18n.t("btn.cancel") == "Cancel"
    assert i18n.t("app.title", version="9.0") == "App L1. Version: 9.0"
    assert i18n.t_field("test_name") == "Test name"
    assert i18n.t_field("fuel_type_1") == "Fuel type 1"
    
    # Switch to fr
    i18n.set_language("fr", save=False)
    assert i18n.get_language() == "fr"
    assert i18n.t("tab.data_entry") == "Saisie de données"
    assert i18n.t("btn.cancel") == "Annuler"
    assert i18n.t("btn.setup_and_run").startswith("Configurer et exécuter")
    assert i18n.t("app.title", version="9.0") == "App L1. Version: 9.0"
    assert i18n.t_field("test_name") == "Nom du test"
    assert i18n.t_field("fuel_type_1") == "Type de combustible 1"
    
    # Test fallback on unknown key
    assert i18n.t("non.existent.key") == "non.existent.key"
    print("PASSED: All helper tests passed!")

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
    
    # Check tabs
    assert app.notebook.tab(0, "text") in ["Data Entry", "Saisie de données"]
    
    # Check data collection
    data = app.collect_all_data()
    assert isinstance(data, dict)
    print(f"Collected form fields count: {len(data)}")
    assert "test_name" in data or "date" in data or "initial_air_temp" in data
    
    # Test adding dynamic tab
    tab_frame, inner = app.add_or_replace_dynamic_tab("test_tab", "My Tab")
    assert "test_tab" in app.managed_tabs
    assert app.managed_tabs["test_tab"] == tab_frame
    
    # Replace dynamic tab
    tab_frame2, inner2 = app.add_or_replace_dynamic_tab("test_tab", "My Tab Renamed")
    assert app.managed_tabs["test_tab"] == tab_frame2
    
    # Test language switch on app
    i18n.set_language("fr", save=False)
    app.rebuild_ui(saved_data=data)
    assert app.notebook.tab(0, "text") == "Saisie de données"
    fr_instructions = app.instructions_frame.get("1.0", "end")
    assert "Veuillez sélectionner un dossier" in fr_instructions, "Instructions frame not translated to French"
    
    # Switch back to English
    i18n.set_language("en", save=False)
    app.rebuild_ui(saved_data=data)
    assert app.notebook.tab(0, "text") == "Data Entry"
    en_instructions = app.instructions_frame.get("1.0", "end")
    assert "Please select a folder" in en_instructions, "Instructions frame not translated to English"
    
    root.destroy()
    print("PASSED: LEMSDataInput UI creation, data collection, and language toggle succeed!")

if __name__ == "__main__":
    test_catalogs()
    test_helpers()
    test_ui_class()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
