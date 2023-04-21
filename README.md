# OmronTM GCode
Python script to control an OmronTM robot with GCode using the Omron listen node.

# Quick setup and use
1. Set up your OmronTM robot with a static IP address.
2. Make a program on your OmronTM with a listen node.
3. Download the Python script onto your computer.
4. Change parameters as desired. All parameters that are recommended to be edited are marked with `#USER_EDIT` in the script.
5. Connect the computer to the robot with an ethernet connection making sure firewalls etc are not going to interrupt the connection.
6. Generate / make a GCode file, place the file in the same folder as the python script and rename it to "run.gcode". Alternatively, edit the `GCode_file_path` variable in the script to match the location of the file.
7. Run the Python script

# Advanced use
The Python script can be used as a module by other scripts. Copy the format in the `__main__` section at the bottom of the script.

There is a method named `ExtruderAxis()` in the `Line` class. This method controls what happens when the E axis speed changes. You can edit this function to return whatever you like, just make sure it returns a list of strings that are valid TM expression editor commands, such as `['IO["ControlBox"].DO[0]=0','IO["ControlBox"].DO[7]=0']`. You can access the speed of the E extruder with `self.ESpeed` and use this in the commands such as `[f'IO["ControlBox"].AO[0]={self.ESpeed}']`.
