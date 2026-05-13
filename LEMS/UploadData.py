import os
import pickle
import platform
import subprocess

#syncs data from workstation to server. data must then be verified.
#Creates default path, prompts user to enter new path, stores new path in pickle file for later use

def UploadData(directory, testname):
    #check if default pickle file exists
    filename = "uploadpath.pickle"
    if os.path.isfile(filename):
        with open(filename, 'rb') as fi:
            uploadpath = pickle.load(fi)
    else:
        uploadpath = "Z:\Jaden\Test"

    #check with user if path is appropriate destination
    print(uploadpath + ' \n')
    userinput = input('Is this the destination to upload to? y/n: \n')
    if userinput == 'n' or userinput == 'no' or userinput == 'N' or userinput == 'No':
        uploadpath = input('Please enter upload destination path do not add testname to path. \n')

    #save upload path to pickle file for later use - becomes the new default
    with open(filename, 'wb') as fi:
        pickle.dump(uploadpath, fi)

    current_os = platform.system()

    # Use os.path.join for cross-platform compatibility
    full_destination = os.path.join(uploadpath, testname)

    if current_os == "Windows":
        # Windows command
        cmd = ["robocopy", directory, full_destination, "/E", "/XO"]
    else:
        # macOS/Linux command
        # Note: trailing slash on source is important for rsync
        cmd = ["rsync", "-a", f"{directory}/", full_destination]

    try:
        print(f"Running: {' '.join(cmd)}")
        # check=True will raise a CalledProcessError if the command fails
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}")
    except FileNotFoundError:
        print("The requested executable (robocopy/rsync) was not found on this system.")

