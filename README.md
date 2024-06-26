# miniDOT Multi-Salinity Dissolved Oxygen Data Processor v1.0

![Alt text](multi-salinity-DO/logo.png)
----------------------------------------------------------------------------------------------------------------------------------------------------
Developed by the Institute of the Marine Sciences of Andalusia (ICMAN) - CSIC and The Mediterranean Institute for Advanced Studies (IMEDEA) - CSIC.
----------------------------------------------------------------------------------------------------------------------------------------------------

An extension to the original miniDOT Concatenate by PME that allows to provide an aditional salinity file to process 
each measurement individually, according to the registered salinity at each specific moment, obtained form another instrument.

This is the first version of the program, that must be run from a cmd. (Future updates will include an exe file and maybe migration to java).

Instructions to run the program:

1. Open the cmd corresponding to a python environment (for example from within Anaconda), then find the path to the files of the miniDOT Multi-Salinity Dissolved Oxygen Data Processor. To do so, type in the cmd:

`cd path-to-files\multi-salinity-DO`

for example: `cd C:\Users\Documents\ICMAN\minidot_concatenate\multi-salinity-DO`

2. Install the requirements.txt file, to do so type in the cmd:

`pip install -r requirements.txt`

3. After installation, type:

`python run.py`

4. An interface will open:

- First choose whether you want to use pressure (mbar) or altitude (m) to calculate oxygen saturation.
- Input the pressure/elevation value in the corresponding space, leaving the other as it is.
- Browse for the folder that contains the .txt raw files as obtained form the miniDOT sensor.
	- Make sure they are in .txt format.
- Browse for the file that contains the salinities measured at the time of the miniDOT raw measures. Your salinity file should meet the following 
requirements to be correctly processed: 
	- It must be a .csv file. 
	- It must contain a column named "Salinity" IN THE FIRST ROW OF THE CSV! (this is important, otherwise the program won't find the salinity data), containing the salinities of the site of measurement.
	- Salinities timestamp must be in the format d/m/Y H:M:S for example 21/02/2024 20:00:00
- Click Process Data button, a file named "DO_processed_output.csv" is then generated and saved in the folder named "outputs".


5. EXE generation
pyinstaller -F --add-data='.\logo.png:.' -n 'Multi salinity DO' .\run.py