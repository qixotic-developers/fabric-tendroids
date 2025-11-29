"""
Reusable slider row components with consistent styling

Dark-themed sliders matching Property panel style.
"""

import omni.ui as ui

# Very dark slider style for controls (darker than container)
SLIDER_STYLE = {
    "draw_mode": ui.SliderDrawMode.HANDLE,
    "background_color": 0xFF0A0A0A,  # Very dark background
    "secondary_color": 0xFF444444,    # Handle track
    "color": 0xFF888888,              # Handle itself
    "border_radius": 3,
}


def create_int_slider_row(
    label: str,
    value: int,
    min_val: int,
    max_val: int,
    tooltip: str,
    on_change: callable,
    label_width: int = 100,
    value_width: int = 35
) -> ui.IntSlider:
    """
    Create a labeled integer slider row with tooltip.
    
    Args:
        label: Label text
        value: Initial value
        min_val: Minimum value
        max_val: Maximum value
        tooltip: Tooltip text
        on_change: Callback(int) when value changes
        label_width: Width of label in pixels
        value_width: Width of value display in pixels
    
    Returns:
        The IntSlider widget
    """
    with ui.HStack(height=22, spacing=4):
        ui.Label(label, width=label_width, tooltip=tooltip)
        
        slider = ui.IntSlider(
            min=min_val,
            max=max_val,
            style=SLIDER_STYLE,
            tooltip=tooltip
        )
        slider.model.set_value(value)
        
        value_label = ui.Label(str(value), width=value_width)
        
        def _on_changed(model):
            v = model.get_value_as_int()
            value_label.text = str(v)
            on_change(v)
        
        slider.model.add_value_changed_fn(_on_changed)
        
    return slider


def create_float_slider_row(
    label: str,
    value: float,
    min_val: float,
    max_val: float,
    tooltip: str,
    on_change: callable,
    precision: int = 2,
    label_width: int = 100,
    value_width: int = 35
) -> ui.FloatSlider:
    """
    Create a labeled float slider row with tooltip.
    
    Args:
        label: Label text
        value: Initial value
        min_val: Minimum value
        max_val: Maximum value
        tooltip: Tooltip text
        on_change: Callback(float) when value changes
        precision: Decimal places to display
        label_width: Width of label in pixels
        value_width: Width of value display in pixels
    
    Returns:
        The FloatSlider widget
    """
    fmt = f"{{:.{precision}f}}"
    
    with ui.HStack(height=22, spacing=4):
        ui.Label(label, width=label_width, tooltip=tooltip)
        
        slider = ui.FloatSlider(
            min=min_val,
            max=max_val,
            style=SLIDER_STYLE,
            tooltip=tooltip
        )
        slider.model.set_value(value)
        
        value_label = ui.Label(fmt.format(value), width=value_width)
        
        def _on_changed(model):
            v = model.get_value_as_float()
            value_label.text = fmt.format(v)
            on_change(v)
        
        slider.model.add_value_changed_fn(_on_changed)
        
    return slider
