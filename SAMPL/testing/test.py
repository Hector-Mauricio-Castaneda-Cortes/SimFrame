
import os
import sys
sys.path.append(str(os.path.dirname(os.path.abspath(__file__)))+'\\..\\')
import sampl_v1
sys.path.append('\\\\fed.cclrc.ac.uk\\Org\\NLab\\ASTeC\\Projects\\VELA\\Software\\VELA_CLARA_PYDs\\bin\\stagetim')
import VELA_CLARA_Magnet_Control as mag
import VELA_CLARA_BPM_Control as bpm
import VELA_CLARA_LLRF_Control as llrf
import VELA_CLARA_PILaser_Control as pil
import time
os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
os.environ["EPICS_CA_ADDR_LIST"] = "10.10.0.12"
os.environ["EPICS_CA_MAX_ARRAY_BYTES"] = "10000000"
os.environ["EPICS_CA_SERVER_PORT"] = "6000"
magInit = mag.init()
llrfInit = llrf.init()
pilInit = pil.init()
Vmagnets = magInit.virtual_VELA_INJ_Magnet_Controller()
Cmagnets = magInit.virtual_CLARA_PH1_Magnet_Controller()
laser = pilInit.virtual_PILaser_Controller()
gun = llrfInit.virtual_CLARA_LRRG_LLRF_Controller()
LINAC01 = llrfInit.virtual_L01_LLRF_Controller()


SAMPL = sampl_v1.Setup(V_MAG_Ctrl=Vmagnets,
                       C_S01_MAG_Ctrl=Cmagnets,
                       C_S02_MAG_Ctrl=Cmagnets,
                       C2V_MAG_Ctrl=Cmagnets,
                       V_RF_Ctrl=gun,
                       C_RF_Ctrl=gun,
                       L01_RF_Ctrl=LINAC01,
                       messages=False)

Cmagnets.switchONpsu('DIP02')
Cmagnets.setSI('DIP02', -1.474)
SAMPL.startElement = 'EBT-INJ-MAG-HVCOR-01'
SAMPL.stopElement = 'EBT-INJ-DIA-SCR-04'
while True:
    I = raw_input("Re-enter a current: ")
    print float(I)
    Cmagnets.setSI('DIP02',float(I))
    V = raw_input("Vertical offset (m): ")
    laser.setVpos(float(V))
    H = raw_input("Horizontal offset (m): ")
    laser.setHpos(float(H))
    SAMPL.run()