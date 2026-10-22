with open('patch_lems_l2.py', 'r', encoding='utf-8') as f:
    code = f.read()

ns = {}
try:
    exec(code, ns)
    print("SUCCESS! patch_lems_l2.py executed completely!")
except Exception as e:
    import traceback
    traceback.print_exc()
