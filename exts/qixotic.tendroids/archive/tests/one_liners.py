"""
Quick control scripts - One-liners for common operations
Copy and paste these into Script Editor as needed
"""

# === STOP ANIMATION ===
from qixotic.tendroids.scene.manager import TendroidSceneManager; TendroidSceneManager().stop_animation()

# === CLEAR EVERYTHING ===
from qixotic.tendroids.scene.manager import TendroidSceneManager; TendroidSceneManager().clear_tendroids()

# === CREATE 3 TENDROIDS AND START ===
from qixotic.tendroids.scene.manager import TendroidSceneManager; s = TendroidSceneManager(); s.clear_tendroids(); s.create_tendroids(3); s.start_animation()

# === JUST CREATE 5 TENDROIDS (NO ANIMATION) ===
from qixotic.tendroids.scene.manager import TendroidSceneManager; s = TendroidSceneManager(); s.clear_tendroids(); s.create_tendroids(5)

# === GET COUNTS ===
from qixotic.tendroids.scene.manager import TendroidSceneManager; s = TendroidSceneManager(); print(f"Tendroids: {s.get_tendroid_count()}, Bubbles: {s.get_bubble_count()}")
