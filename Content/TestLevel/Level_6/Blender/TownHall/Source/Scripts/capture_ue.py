"""Capture four existing-editor views without adding scene objects."""
import unreal, math, time, json
from pathlib import Path
out=Path('D:/UEProject/ArcheoDig/Content/TestLevel/Level_6/Blender/TownHall/Previews')
views=[
    ('UE_01_ThreeQuarter',(2850,-9450,2250),(5600,-7100,380)),
    ('UE_02_Character',(3450,-7600,184),(5550,-7100,340)),
    ('UE_03_Entrance',(3550,-7100,440),(5550,-7100,440)),
    ('UE_04_Neighbors',(-1000,-11600,5800),(3600,-5800,250)),
]
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
_th_capture={'i':0,'phase':0,'at':time.monotonic(),'handle':None}
def _th_capture_tick(dt):
    s=_th_capture
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
_th_capture['handle']=unreal.register_slate_post_tick_callback(_th_capture_tick)

