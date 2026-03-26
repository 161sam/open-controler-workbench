import os
import sys

repo_root = os.path.dirname(os.path.abspath(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import FreeCADGui
from ocf_freecad.workbench import OpenControllerWorkbench

FreeCADGui.addWorkbench(OpenControllerWorkbench())
