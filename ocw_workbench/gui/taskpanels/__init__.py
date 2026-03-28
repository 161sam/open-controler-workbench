"""Focused task-panel adapters for short-lived workflows.

The dock-based Workbench remains the primary UI surface. Task panels are
intended for guided or commit-oriented flows where FreeCAD's task view is a
better fit than a permanent sidebar.
"""

from ocw_workbench.gui.taskpanels.constraints_taskpanel import ConstraintsTaskPanel
from ocw_workbench.gui.taskpanels.layout_taskpanel import LayoutTaskPanel
from ocw_workbench.gui.taskpanels.library_taskpanel import LibraryTaskPanel

__all__ = ["LibraryTaskPanel", "LayoutTaskPanel", "ConstraintsTaskPanel"]
