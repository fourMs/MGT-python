import sys
sys.path.append('../..')

import mgmodule
mg = mgmodule.MgObject('dance.avi',filtertype = 'Regular', color = True)
mg.motionvideo()
