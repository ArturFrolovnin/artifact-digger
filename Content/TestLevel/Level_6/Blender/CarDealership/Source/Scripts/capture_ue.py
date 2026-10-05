"""Capture five existing-editor views without adding scene objects."""
import unreal, math, time, json
from pathlib import Path
out=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/CarDealership/Previews')
views=[
    ('UE_01_ThreeQuarter',(-500,-4100,2300),(-3085,-7400,270)),
    ('UE_02_Character',(-4200,-5450,194),(-3085,-6900,240)),
    ('UE_03_Showroom',(-3085,-4700,300),(-3085,-6700,320)),
    ('UE_04_Service',(-450,-7650,330),(-2350,-7800,275)),
    ('UE_05_Neighbors',(-6500,-2500,4500),(-2000,-7150,180)),
]
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
_car_capture={'i':0,'phase':0,'at':time.monotonic(),'handle':None}
def _car_capture_tick(dt):
    s=_car_capture
    if time.monotonic()<s['at']:return
    if s['i']>=len(views):
        unreal.unregister_slate_post_tick_callback(s['handle'])
        (out/'ue_capture_complete.txt').write_text(json.dumps([x[0]+'.png' for x in views]))
        return
    name,loc,target=views[s['i']]
    if s['phase']==0:
        d=[target[i]-loc[i] for i in range(3)]
        rot=unreal.Rotator(pitch=math.degrees(math.atan2(d[2],math.hypot(d[0],d[1]))),yaw=math.degrees(math.atan2(d[1],d[0])),roll=0)
        editor.set_level_viewport_camera_info(unreal.Vector(*loc),rot)
        s['phase']=1;s['at']=time.monotonic()+3
    else:
        unreal.AutomationLibrary.take_high_res_screenshot(1400,1000,str(out/(name+'.png')))
        s['i']+=1;s['phase']=0;s['at']=time.monotonic()+3
_car_capture['handle']=unreal.register_slate_post_tick_callback(_car_capture_tick)
