
import win32api

def get_monitor_screen_coords():
  """
  Gets the screen coordinates for each monitor.

  Returns:
    A list of dictionaries, where each dictionary represents a monitor
    and contains its screen coordinates ('left', 'top', 'right', 'bottom').
  """
  monitors = []
  for monitor_handle in win32api.EnumDisplayMonitors():
    monitor_info = win32api.GetMonitorInfo(monitor_handle[0])
    coords = monitor_info['Monitor']
    monitors.append({
        'left': coords[0],
        'top': coords[1],
        'right': coords[2],
        'bottom': coords[3]
    })
  return monitors

if __name__ == '__main__':
  monitor_coords = get_monitor_screen_coords()
  for i, coords in enumerate(monitor_coords):
    print(f"Monitor {i+1}:")
    print(f"  Left: {coords['left']}, Top: {coords['top']}")
    print(f"  Right: {coords['right']}, Bottom: {coords['bottom']}")
    print(f"  Width: {coords['right'] - coords['left']}, Height: {coords['bottom'] - coords['top']}")
