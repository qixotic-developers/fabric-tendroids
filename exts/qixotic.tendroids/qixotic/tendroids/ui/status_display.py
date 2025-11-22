"""
Status display management for Tendroid UI

Centralized status label updates and formatting.
"""

import omni.ui as ui


class StatusDisplay:
  """
  Manages status labels and updates for the control panel.
  
  Provides centralized status message handling with consistent formatting.
  """
  
  def __init__(self):
    """Initialize status display."""
    self.status_label = None
    self.count_label = None
    self.animation_label = None
  
  def create_ui(self, parent_stack: ui.VStack):
    """
    Create status display UI elements.
    
    Args:
        parent_stack: Parent VStack to add labels to
    """
    with ui.CollapsableFrame("Status", height=0, collapsed=False):
      with ui.VStack(spacing=5):
        self.status_label = ui.Label(
          "Ready",
          word_wrap=True
        )
        
        self.count_label = ui.Label(
          "Tendroids: 0",
          word_wrap=True
        )
        
        self.animation_label = ui.Label(
          "Animation: Stopped",
          word_wrap=True
        )
  
  def update_status(self, message: str):
    """Update main status message."""
    if self.status_label:
      self.status_label.text = message
  
  def update_count(self, count: int):
    """Update tendroid count display."""
    if self.count_label:
      self.count_label.text = f"Tendroids: {count}"
  
  def update_animation_status(self, status: str):
    """Update animation status display."""
    if self.animation_label:
      self.animation_label.text = f"Animation: {status}"
