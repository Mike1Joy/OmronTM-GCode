# OmronTM GCode
Python script to control an OmronTM robot with GCode using the Omron listen node.

## Quick setup and use
1. Set up your OmronTM robot with a static IP address.
2. Make a program on your OmronTM with a listen node.
3. Download the Python script onto your computer.
4. Change parameters as desired. All parameters that are recommended to be edited are marked with `#USER_EDIT` in the script.
5. Connect the computer to the robot with an ethernet connection making sure firewalls etc are not going to interrupt the connection.
6. Generate / make a GCode file, place the file in the same folder as the python script and rename it to "run.gcode". Alternatively, edit the `GCode_file_path` variable in the script to match the location of the file.
7. Run the Python script

## Advanced use
The Python script can be used as a module - use the format in the `__main__` section at the bottom of the script as a guide.

There is a method named `ExtruderAxis()` in the `Line` class. This method controls what happens when the E axis speed changes. You can edit this function to return whatever you like, just make sure it returns a list of strings that are valid TM expression editor commands, such as `['IO["ControlBox"].DO[0]=0','IO["ControlBox"].DO[7]=0']`. You can access the speed of the E extruder with `self.ESpeed` and use this in the commands such as `[f'IO["ControlBox"].AO[0]={self.ESpeed}']`.

## Sequencing issues
According to the TM Expression Editor and Listen Node manual:

> "The command can be divided into two categories. The first category is commands which can be accomplished in instance, like assigning variable value. The second category is commands needs to be executed in sequence, like motion command and IO value assigning. The second category command will be placed in queue and executed in order."

So if you want to send any commands that fall into the first category, you must make sure `Wait_for_response` is set to true. Otherwise the instantanious command will be executed when the robot receives it and not in order of the queue. the `Wait_for_response` variable ensures that the next message is not sent until the previous one has been completed. With this set to false, the entire list of commands will be sent in one go. Note that when the script waits for responses, blending is impossible and there is a slight delay between move commands so the motion will be jerky. So I recommend setting `Wait_for_response` to false and only using commands that are done in order.

At the time of writing (as far as I am aware) there is no way to set a variable in sequence as these commands are actioned immediately. TO get around this issue, you can use the analog out pins to store a float between -10 and 10 by calling `IO["ControlBox"].AO[0]=value`. This value can be accessed in the TM flow program in another thread and used to control an extruder through a serial connection etc.
