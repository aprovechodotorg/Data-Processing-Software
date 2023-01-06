import os
#syncs data from workstation to server. data must then be verified.
os.system("rsync -a /home/sam/python_data/ sam@stovesimulator:/home/sam/python_data_new")