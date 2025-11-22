"""
Multi-Tendroid Stress Test - PASTE THIS ENTIRE SCRIPT INTO SCRIPT EDITOR
"""

import random
import carb
import omni.usd
import omni.kit.app
from pxr import Gf, UsdGeom

stress = None
SCRIPT_VERSION = "v2.2-official"
print(f"\n{'='*60}")
print(f"LOADING STRESS TEST {SCRIPT_VERSION}")
print(f"{'='*60}\n")


class StressBubbleVisual:
    def __init__(self, stage, path: str, base_x: float, base_z: float):
        self._stage = stage
        self._path = path
        self._base_x = base_x
        self._base_z = base_z
        self._sphere = None
        self._translate_op = None
    
    def create(self, initial_radius: float, start_y: float):
        existing = self._stage.GetPrimAtPath(self._path)
        if existing.IsValid():
            self._stage.RemovePrim(self._path)
        
        self._sphere = UsdGeom.Sphere.Define(self._stage, self._path)
        self._sphere.CreateRadiusAttr(initial_radius * 0.95)
        self._sphere.CreateDisplayColorAttr([(0.3, 0.6, 0.9)])
        self._sphere.CreateDisplayOpacityAttr([0.5])
        
        xform = UsdGeom.Xformable(self._sphere.GetPrim())
        xform.ClearXformOpOrder()
        self._translate_op = xform.AddTranslateOp()
        self._translate_op.Set(Gf.Vec3d(self._base_x, start_y, self._base_z))
    
    def update(self, y_pos: float, radius: float):
        if self._translate_op:
            self._translate_op.Set(Gf.Vec3d(self._base_x, y_pos, self._base_z))
        if self._sphere:
            self._sphere.GetRadiusAttr().Set(radius * 0.95)
    
    def destroy(self):
        if self._stage:
            prim = self._stage.GetPrimAtPath(self._path)
            if prim.IsValid():
                self._stage.RemovePrim(self._path)


class WarpStressTest:
    def __init__(self):
        self.tendroids = []
        self.bubbles = []
        self.visuals = []
        self._update_sub = None
        self._running = False
        self._stage = None
        self.spacing = 50.0
    
    def start(self, count: int = 15):
        ctx = omni.usd.get_context()
        self._stage = ctx.get_stage()
        
        for path in ["/World/Tendroids", "/World/Bubbles"]:
            if not self._stage.GetPrimAtPath(path).IsValid():
                UsdGeom.Xform.Define(self._stage, path)
        
        self._create_tendroids(count)
        
        self._running = True
        app = omni.kit.app.get_app()
        self._update_sub = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="StressTest"
        )
        carb.log_warn(f"[StressTest] Started {count} tendroids")
    
    def _create_tendroids(self, count: int):
        from qixotic.tendroids.v2 import V2WarpTendroid, V2Bubble
        
        cols = int(count ** 0.5) + 1
        
        for i in range(count):
            col = i % cols
            row = i // cols
            x = (col - cols/2) * self.spacing
            z = (row - cols/2) * self.spacing
            
            t_path = f"/World/Tendroids/T_{i:02d}"
            tendroid = V2WarpTendroid(
                stage=self._stage, path=t_path,
                radius=10.0, length=200.0,
                radial_segments=24, height_segments=48,
                max_amplitude=0.8, bulge_width=0.9
            )
            
            xform = UsdGeom.Xformable(self._stage.GetPrimAtPath(t_path))
            xform.ClearXformOpOrder()
            xform.AddTranslateOp().Set(Gf.Vec3d(x, 0, z))
            
            bubble = V2Bubble(
                cylinder_radius=10.0, cylinder_length=200.0,
                max_radius=18.0, rise_speed=15.0 + random.uniform(-3, 3),
                starting_diameter_pct=0.10, max_diameter_pct=0.40
            )
            bubble.y = random.uniform(0, 160)
            
            b_path = f"/World/Bubbles/B_{i:02d}"
            visual = StressBubbleVisual(self._stage, b_path, x, z)
            visual.create(10.0, bubble.y)
            
            self.tendroids.append(tendroid)
            self.bubbles.append(bubble)
            self.visuals.append(visual)
    
    def _on_update(self, event):
        if not self._running:
            return
        dt = event.payload.get("dt", 1/60)
        
        for t, b, v in zip(self.tendroids, self.bubbles, self.visuals):
            if not b.update(dt):
                b.reset()
            r = b.get_current_radius()
            v.update(b.y, r)
            t.apply_deformation(b.y, r)
    
    def clear(self):
        self._running = False
        self._update_sub = None
        for t in self.tendroids:
            t.destroy()
        for v in self.visuals:
            v.destroy()
        self.tendroids = []
        self.bubbles = []
        self.visuals = []
        for path in ["/World/Tendroids", "/World/Bubbles"]:
            prim = self._stage.GetPrimAtPath(path)
            if prim.IsValid():
                self._stage.RemovePrim(path)
        carb.log_warn("[StressTest] Cleared")


def run_stress(count=15):
    global stress
    if stress:
        stress.clear()
    stress = WarpStressTest()
    stress.start(count)
    carb.log_warn(f"Commands: run_stress(N), stress.clear()")

run_stress(15)
