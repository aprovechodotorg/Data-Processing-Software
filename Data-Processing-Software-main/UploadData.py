import os
import pickle
from ipywidgets import interact, widgets
from IPython.display import display, clear_output

#syncs data from workstation to server. data must then be verified.
#Creates defualt path, prompts user to enter new path, stores new path in pickle file for later use

def UploadData(directory, testname):
    #check if default pickle file exists
    filename = "uploadpath.pickle"
    if os.path.isfile(filename):
        with open(filename, 'rb') as fi:
            uploadpath = pickle.load(fi)
    else:
        uploadpath = "G:\\Shared drives\\Baseline efficiency data\\uct_lab"

    #check with user if path is appropriate destination
    print(uploadpath + ' \n')
    userinput = input('Is this the destination to upload to? y/n: \n')
    if userinput == 'n' or userinput == 'no' or userinput == 'N' or userinput == 'No':
        uploadpath = input('Please enter upload destination path do not add testname to path. \n')

    #save upload path to pickle file for later use - becomes the new defualt
    with open(filename, 'wb') as fi:
        pickle.dump(uploadpath, fi)

    user = os.getlogin()

    uploadpath = uploadpath + '\\' + testname + '_' + user

    xmsg = 'xcopy ' + '"' + directory + '" ' + '"' + uploadpath + '"' + ' /E /I /Y /D'
    rmsg = 'rsync -a ' + directory + ' ' + uploadpath
    #s copies directories and subdirectories
    #e copies all subdirectories, even empty on es
    #i if source directory and desitination don't exist, assume desitination specifies directory and create new directory then copy files
    #y supress prompting to confirm that you want to overwrite an existing desitination file
    #Copies only new or updated files is source date time is newer than destination time

    try:
        print(xmsg + '\n')
        os.system(xmsg)
    except:
        print(msg + '\n')
        os.system(rmsg)

