import os
from generate_tables import process_tests

root_dir = r"c:\Users\travi\Desktop\Osprey Report script\small combustion chamber"
selected = [
    r"c:\Users\travi\Desktop\Osprey Report script\small combustion chamber\05.15.26",
    r"c:\Users\travi\Desktop\Osprey Report script\small combustion chamber\05.15.26"
]
process_tests(root_dir, selected)
print("Done!")
