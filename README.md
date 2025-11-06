# Data-Processing-Software Database
The following database contains code for processing cooking and heating stove data. 
These instructions will detail the file system, how to view the code, how to view branches, how to request a feature, how to download code, and how to use the code for different tests.
For a specific test protocol or emission testing system, find the appropriate header and follow the instructions.
**Data processing apps are not in this code database.** However, how to access the apps is included in the instructions below.
## Navigating GitHub
### File System
This database contains folders with test data and folders with code scripts. 
Any folder with *Data* in the name contains example data and data outputs that may be run by the code to test it out.
Any folder beginning with a . may be ignored. These folders are for GitHub setup.
The *LEMS* folder contains all code scripts for the LEMS, ISO, WBT, and IDC tests.
The *PEMS* folder contains all code scripts for the PEMS and Possum testing equipment.
The *MusaPlotter_2.0* contains all code scripts for the real-time plotting software used by the LEMS. This software only works on Linux computers. Please go to the software section of aprovecho.org for more information
The *UCET* folder contains all code scripts for processing UCETs.
The *Unit Tests* Folder is used for rapid testing of software to ensure new changes do not interfere with previous work. This is a developer tool.
### How to View the Code
All code may be viewed online through GitHub. Click on the folder containing code scripts and click on any file ending in .py. 
Code may also be viewed through a code editor like PyCharm or VisualStudio. Follow software installation instructions and then follow instructions for *How to Download Code*.
### How to View Branches
GitHub directs all users to the main branch when first opened. The main branch contains finalized code. Other branches contain code that is still in development. 
To view code in different branches, select the dropdown menu in the left corner of the Code page labeled main. Select the branch you wish to view. Now all code viewed will be code from the selected branch.
If GitHub desktop is installed, you may also switch branches through that.
### How to Request a Feature or Report an Issue
This code is still in development. To request an additional feature or report an issue with the code, select the Issues tab in the top toolbar.
Select *New Issue* in the right corner and write a detailed description of the feature request or issue. Add pictures or a screenshot for more detail if needed.
### How to Download Code for Single Use Evaluation
All code may be downloaded using the *<> Code* dropdown menu in the right corner of the Code tab. 
Select *Download ZIP* to download all code to your computer.
To download a single script. Open the script using the instruction in *How to View the Code* then select the download button in the right corner.
### How to Download and Update Code for Production Use
We use GitHub Desktop to maintain an updated copy of the code for daily use. Select Clone Repository by URL - https://github.com/aprovechodotorg/Data-Processing-Software
## Data Processing
### LEMS
The LEMS software (found in the *LEMS* folder), is used for processing energy and emissions metrics. **Energy metrics do not require LEMS outputs**.
The software is split into 3 levels:
- Level 1: Process a single test
- Level 2: Process/reprocess multiple tests and compare all tests
- Level 3: Compare Level 2 outputs across different stoves or design iterations
The LEMS software may be used for cooking and heating stove tests.
#### ISO, WBT, and Cookstove Tests
LEMS data processing may be done through an application that can be downloaded to your computer. To find the download and instructions please go to: [Aprovecho Software Drive](https://drive.google.com/drive/folders/12hJTKqCsw6icbZ02twks7oiitPQT_r0s?usp=sharing) or go to the software section on aprovecho.org
Follow the instructions labeled *Installing Data Processing Apps* for detailed installation instructions.
The apps will include instructions on how to use them. For video instructions, please watch the L1 and L2 walkthroughs on Google Drive or watch them on the Aprovecho YouTube channel.
#### IDC and Heating Stove Tests
Heating stove tests may be through a separate set of applications. The functionality of these applications is the same as the cookstove applications but with specific phase and calculation changes to accommodate heating stove testing. 
To find the download and instructions please go to: [Aprovecho Heating Stove Software Drive](https://drive.google.com/drive/folders/17vJj51NH_q3Xmx9cTbS4UZK-35kOTr_9?usp=sharing) or go to the software section on aprovecho.org
Follow the instructions labeled *Installing Data Processing Apps* for detailed installation instructions.
The apps will include instructions on how to use them. For video instructions, please watch the L1 and L2 walkthroughs on Google Drive or watch them on the Aprovecho YouTube channel.
### PEMS
The PEMS software is still in development and does not have an app yet. 
To use the software, copy the file named *PEMS_EnergyInputs* from the *DataEntrySheets* folder. 
Fill out all requested information.
The PEMS script must be run on a computer with a Python editor/launcher installed. Follow instructions on how to install PyCharm or a similar package and how to connect it to GitHub.
Run *PEMSDataCruncher.py* for level 1 and follow the instructions.
Run *PEMSDataCruncher_L2.py* for level 2 and follow the instructions.
Run *PEMSDataCruncher_L3.py* for level 3 and follow the instructions.
### UCET
The UCET software is run in Jupyter Notebook, a system that allows for easy code installation and visualization.
Follow the instructions at [Installing and Running Jupyter](https://docs.google.com/presentation/d/1gQ6MGKSAx5jQBP9Gohz5Fdsf6tHgLNHSLS427BYSPsY/edit?usp=sharing)
Then follow the instructions for [Using Jupyter](https://docs.google.com/presentation/d/1RdBy40eWOjFHmWkBhXwkdNuUNEEz39ZBEcjw1SLt-yQ/edit?usp=sharing)
The data entry sheet may be found within the UCET protocol at aprovecho.org
