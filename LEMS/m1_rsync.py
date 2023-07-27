import os
#syncs verified data from server. this will delete work that you have not sent for verification
#uses ysync or xcopy depending on operating system
#currently set for google drive temporarily set for DOE data

def load_trusted (inputpath):
    directory, filename = os.path.split(sheetinputpath)
    datadirectory, testname = os.path.split(directory)
    try:
        os.system("xcopy G:\\Shared drives\\DOE Cordwood Data Aprovecho\\field\\Verified Data ")
    except:
        os.system("rsync -a --delete sam@stovesimulator:/home/sam/python_data/ /home/sam/python_data")