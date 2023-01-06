import os
#syncs verified data from server. this will delete work that you have not sent for verification
os.system("rsync -a --delete sam@stovesimulator:/home/sam/python_data/ /home/sam/python_data")