import nclib #for sending commands to listen node
import math

# Constants
X = 0
Y = 1
Z = 2
A = 3
B = 4
C = 5
E = 6
F = 7
Axes = ['X','Y','Z','A','B','C','E','F']

RAPID = 0
FEED = 1
G92 = 2

class Line:
    def __init__(self, LineNum, AcelTime, Blend, InitialF):
        self.LineNum = LineNum
        self.Values = [0.0,0.0,0.0,0.0,0.0,180.0,0.0,InitialF]
        self.ESpeed = 0.0
        self.Moving = False
        self.MoveType = -1
        self.AcelTime = AcelTime
        self.Blend = Blend

    def _SetSpeed(self,LastValues):
        dx2 = (self.Values[X] - LastValues[X])**2
        dy2 = (self.Values[Y] - LastValues[Y])**2
        dz2 = (self.Values[Z] - LastValues[Z])**2
        
        dist = math.sqrt(dx2+dy2+dz2)
        Edist = self.Values[E]-LastValues[E]

        time = (60.0*dist)/self.Values[F]

        if time == 0:
            self.ESpeed = 0.0
        else:
            self.ESpeed = round(Edist/time, 2)

    def SetValues(self, text, CurrentSpeeds):
        LastValues = [0,0,0,0,0,0,0,0]
        for i in range(F):
            LastValues[i] = self.Values[i]
        self.Moving = False
        self.ESpeed = 0.0

        # get rid of comment
        text = text.split(";",maxsplit=1)[0]

        # get move type
        if   "G0" in text:
            self.MoveType = RAPID
        elif "G1" in text:
            self.MoveType = FEED
        elif "G92" in text:
            self.MoveType = G92
        else:
            return # self.Valid will be false

        # Do stuff based on movetype
        if self.MoveType == RAPID or self.MoveType == FEED:
            # set F to be same as prev for this movetype
            self.Values[F] = CurrentSpeeds[self.MoveType]
            EValue = False

            # Go through axes in gcode and set valyes
            for i, a in enumerate(Axes):
                if a in text:
                    self.Values[i] = float(text.split(a,maxsplit=1)[-1].split(maxsplit=1)[0])
                    if i==X or i==Y or i==Z:
                        self.Moving = True
                    elif i==F:
                        CurrentSpeeds[self.MoveType] = self.Values[F]
                    elif i==E:
                        EValue = True
            
            # Set ESpeed if there was an E value
            if self.Moving:
                if EValue:
                    self._SetSpeed(LastValues)
                else:
                    self.ESpeed = 0.0
        
        elif self.MoveType == G92:
            self.Moving = False
            for i, a in enumerate(Axes):
                if a in text:
                    self.Values[i] = float(text.split(a,maxsplit=1)[-1].split(maxsplit=1)[0])
            
    def com_write(self):
        return f'com_writeline("spd_Arduino",{self.ESpeed})'

    def PLine(self):
        # y and z axes are negative because datum from landmark is upside-down. Flip make these positive if datum is the right way up
        return f'PLine("CAP",{self.Values[X]},{-self.Values[Y]},{-self.Values[Z]},{self.Values[A]},{self.Values[B]},{self.Values[C]},{int(self.Values[F]/60.0)},{self.AcelTime},{self.Blend})'
    
    def ExtruderAxis(self): #USER_EDIT
        # function called whenever the speed of the E axis changes. Return a list of commands for the robot. These can be based on the current speed by accessing self.ESpeed
        if self.ESpeed > 0:
            return [f'IO["ControlBox"].DO[0]=0',f'IO["ControlBox"].DO[7]=0']
        else:
            return [f'IO["ControlBox"].DO[7]=1',f'IO["ControlBox"].DO[7]=1']

class GCode2Omron:
    def __init__(self, AcelTime=50, Blend=10, InitialF=600):
        self.IP_address = '192.168.1.3'
        self.GCode_file_path = r'run.gcode'
        self.AcelTime = AcelTime
        self.Blend = Blend
        self.InitialF = InitialF
        self.nc = None
        self.Lines = []

    def Connect(self, IP_address):
        self.IP_address = IP_address

        print("Connecting to robot...")
        self.nc = nclib.Netcat((self.IP_address, 5890),udp=False,verbose=False)
        print("Robot connected")

    def ReadGCode(self, GCode_file_path):
        self.GCode_file_path = GCode_file_path

        print("Reading run.gcode file...")

        # Read File
        with open(self.GCode_file_path) as file:
            gcode = file.readlines()

        print("File read")

        print("Generating commands...")

        # Generate commands from lines
        self.Lines = [Line(0,self.AcelTime,self.Blend,self.InitialF)]
        CurrentSpeed = [self.InitialF,self.InitialF]
        for line_num, line in enumerate(gcode):
            new_l = Line(line_num,self.AcelTime,self.Blend,self.InitialF)
            for i in range(F):
                new_l.Values[i] = self.Lines[-1].Values[i]
            new_l.SetValues(line,CurrentSpeed)
            self.Lines.append(new_l)
            
        LastE = 0.0
        for l in self.Lines:
            if l.Moving:
                if l.ESpeed == 0.0 or abs(l.ESpeed - LastE) > 0.1:
                    LastE = l.ESpeed
                else:
                    l.ESpeed = LastE

        print("Commands generated")

    def GenerateCommand(self, ID, Code):
        command = f'{ID},{Code}'
        command1=f'TMSCT,{len(command)},{command},' #add header and length
        checksum=0
        for n in command1:
            checksum ^=ord(n) #create checksum using bitwise xor of each character in command1
        command2=f'${command1}*{checksum:02x}\r\n'
        return command2.encode() #convert to hex
    
    def SendCommand(self, command, wait_response):
        print(f'send: {command}',end=" | ")
        self.nc.send(command) #send command to robot
        if wait_response:
            getresponse = nc.recv(n=4096,timeout=5) #must include receive otherwise robot doesn't accept command
            print(f'recv: {getresponse}',end=" | ")

    def StreamCommands(self, Wait_for_response, Header, Footer):
        print("Sending commands to robot...")

        for c in Header:
            self.SendCommand(self.GenerateCommand(0,c), Wait_for_response)
            print()
        
        print()

        LastESpeed = 0.0
        for i in range(1,len(self.Lines)):
            if self.Lines[i].Moving:
                if self.Lines[i].ESpeed != LastESpeed:
                    e_coms = self.Lines[i].ExtruderAxis()
                    for c in e_coms:
                        self.SendCommand(self.GenerateCommand(self.Lines[i].LineNum,c), Wait_for_response)
                    LastESpeed = self.Lines[i].ESpeed
                self.SendCommand(self.GenerateCommand(self.Lines[i].LineNum,self.Lines[i].PLine()), Wait_for_response)
                print()
            
        for c in Footer:
            self.SendCommand(self.GenerateCommand(0,c), Wait_for_response)
            print()

        print("Finished streaming commands")


if __name__ == "__main__":
    #TM robot listen node commands are listed in 'expression editor and listen node manual'
    #IP  address must be set on TM robot / system / network / Local Area Conn 2 / Static IP / IP address: 10.18.0.22 / Subnet mask: 255.255.0.0

    IP_address = '192.168.1.3' #USER_EDIT # address of Omron robot
    GCode_file_path = r'run.gcode' #USER_EDIT # file path of gcode file
    Wait_for_response = False #USER_EDIT # wait for response from robot before sending the next command

    AcelTime = 50 #USER_EDIT # Time taken to accelerate to full speed (s)
    Blend = 10 #USER_EDIT # percentage blend for each linear move (%)
    InitialF = 600 #USER_EDIT # default feed rate until a feed rate is specified in GCode (mm/min)

    HeaderCommands = [ #USER_EDIT
        'StopAndClearBuffer()',
        'IO["ControlBox"].DO[0]=1',
        'IO["ControlBox"].DO[7]=1',
        'ChangeBase("vision_Datum")'
    ]

    FooterCommands = [ #USER_EDIT
        'IO["ControlBox"].DO[0]=1',
        'IO["ControlBox"].DO[7]=1'
    ]

    GCodeSender = GCode2Omron(AcelTime, Blend, InitialF)
    GCodeSender.Connect(IP_address)
    GCodeSender.ReadGCode(GCode_file_path)
    GCodeSender.StreamCommands(Wait_for_response, HeaderCommands, FooterCommands)
    