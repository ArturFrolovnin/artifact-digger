"""Level_6 reference layout: inspect, apply and verify in the running editor."""
import unreal, json, math
from pathlib import Path

ROOT = Path('D:/UEProject/ArcheoDig')
OUT = ROOT / 'Saved/Level6Replan'
OUT.mkdir(parents=True, exist_ok=True)
LEVEL = '/Game/TestLevel/Level_6/level_6_create_map'
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

def vec(v): return [v.x, v.y, v.z]
def inspect():
    world = editor.get_editor_world()
    assert world.get_path_name().split('.')[0] == LEVEL
    rows = []
    for a in actors.get_all_level_actors():
        c,e = a.get_actor_bounds(False)
        parts = []
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            parts.append(dict(mesh=mesh.get_path_name() if mesh else None, materials=[m.get_path_name() if m else None for m in comp.get_materials()]))
        r = a.get_actor_rotation()
        rows.append(dict(path=a.get_path_name(),label=a.get_actor_label(),folder=str(a.get_folder_path()),location=vec(a.get_actor_location()),rotation=[r.pitch,r.yaw,r.roll],scale=vec(a.get_actor_scale3d()),center=vec(c),extent=vec(e),parts=parts))
    data=dict(level=world.get_path_name(),dirty_maps=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()],dirty_assets=[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()],actors=rows)
    (OUT/'inventory.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    unreal.log('LEVEL6_INVENTORY_DONE '+str(len(rows)))

def bounds(rows):
    return [[min(a['center'][j]-a['extent'][j] for a in rows),max(a['center'][j]+a['extent'][j] for a in rows)] for j in range(3)]

def make_plan():
    data=json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))
    rows=data['actors']
    groups=[]
    def group(name, selected, x, y, district, turn=0):
        assert selected, name
        b=bounds(selected); cx=(b[0][0]+b[0][1])/2; cy=(b[1][0]+b[1][1])/2
        angle=math.radians(turn); c=math.cos(angle); s=math.sin(angle)
        transformed=[]
        for a in selected:
            pts=[]
            for dx in [-a['extent'][0],a['extent'][0]]:
                for dy in [-a['extent'][1],a['extent'][1]]:
                    px=a['center'][0]+dx-cx; py=a['center'][1]+dy-cy
                    pts.append([x*100+c*px-s*py,y*100+s*px+c*py])
            transformed.extend(pts)
        rect=[min(p[0] for p in transformed)/100,max(p[0] for p in transformed)/100,min(p[1] for p in transformed)/100,max(p[1] for p in transformed)/100]
        groups.append(dict(name=name,rows=selected,origin=[cx,cy],target=[x*100,y*100],turn=turn,folder='CityBlockout/'+district+'/'+name,rect=rect))
    group('University',[a for a in rows if a['folder']=='CityBlockout/University_Detailed'],60,7,'02_UniversityDistrict')
    for name,label,x,y,district,turn in [
        ('Dormitory','BO_Dormitory',60,-29,'02_UniversityDistrict',0),('Library','BO_Library',60,43,'02_UniversityDistrict',0),('TownHall','BO_Administration',60,78,'02_UniversityDistrict',0),
        ('Museum','BO_Museum',22,-24,'03_MuseumDistrict',0),('Hospital','BO_Hospital',15,78,'05_HealthcareDistrict',180),('CarDealership','BO_CarDealer',-30,77,'04_CommercialDistrict',180),
        ('RudyPawnshop','BO_Pawnshop',-13,-24,'03_MuseumDistrict',0),('GrahamShop','BO_Equipment',5,33,'04_CommercialDistrict',90),('CafeBar','BO_Cafe',-43,13,'04_CommercialDistrict',90),
        ('GeneralStore','SM_GeneralStore_Blockout',47,-80,'04_CommercialDistrict',0),('BusStop','SM_BusStop_Blockout',37,-80,'10_StreetProps',0)]:
        group(name,[a for a in rows if a['label']==label],x,y,district,turn)
    for name,x,y in [('ConspiracyHouse',20,-80),('HippieCoupleHouse',20,-62),('SlackerFriendsHouse',-3,-80),('IntellectualGrandpaHouse',-3,-62),('RelaxedNeighborHouse',-26,-80),('CreatorCoupleHouse',-26,-62),('PlayerHouse',-49,-80),('MiaHouse',-50,-66)]:
        selected=[a for a in rows if name in a['folder'] and not a['label'].startswith('BO_Plot_')]
        group(name,selected,x,y,'06_ResidentialDistrict')
    paths=[]
    def path(name,a,b,w=4): paths.append(dict(name=name,a=a,b=b,w=w))
    path('Campus', [40,-48],[40,94],4)
    path('WestArrival',[32,-92],[32,-48],4)
    path('WestLink',[32,-48],[40,-48],4)
    path('CentralSpine',[40,-3],[-56,-3],4.5)
    path('EastSpine',[40,58],[-56,58],4.5)
    path('CentralCross',[-4,-50],[-4,58],4)
    path('SouthPromenade',[-56,-92],[-56,94],4)
    path('WestResidential',[32,-91],[-60,-91],3)
    path('ResidentialLink',[40,-50],[-60,-50],4)
    for i,x in enumerate([10,-14.5,-36,-60]): path('ResidentialRow'+str(i),[x,-91],[x,-50],3)
    path('PawnshopLane',[-22,-50],[-22,-3],3)
    path('CafeLane',[-29,-3],[-29,58],3)
    path('HospitalApproach',[2,58],[2,94],3)
    path('CarDealerApproach',[-30,58],[-30,64.5],4)
    path('BusApproach',[32,-80],[35.6,-80],3)
    path('ShopApproach',[38.5,-80],[42.7,-80],3)
    # Broad level plazas meet entrances without ornamental steps.
    pads=[dict(name='MuseumSquare',rect=[-2.5,10,-41,-7],mat='Paving',folder='03_MuseumDistrict'),dict(name='Park',rect=[-78,-58,1,29],mat='Green',folder='07_Park')]
    path('ParkEntry',[-56,15],[-78,15],3)
    path('ParkCross',[-68,1],[-68,29],3)
    path('ParkWest',[-58,1],[-78,1],2)
    path('ParkEast',[-58,29],[-78,29],2)
    path('ParkSouth',[-78,1],[-78,29],2)
    # Entry connectors run from the southern boundary of each civic plot.
    for g in groups:
        r=g['rect']; x=(r[0]+r[1])/2; y=(r[2]+r[3])/2
        if g['name'] in ['University','Dormitory','Library','TownHall']:
            path(g['name']+'Entry',[40,y],[r[0]+0.3,y],3)
        elif g['name']=='Hospital': path('HospitalEntry',[2,y],[r[0]+0.3,y],3)
        elif g['name']=='GrahamShop': path('GrahamEntry',[-4,y],[r[0]+0.3,y],3)
        elif g['name']=='RudyPawnshop': path('RudyEntry',[-22,y],[r[0]+0.3,y],2.5)
        elif g['name']=='CafeBar': path('CafeEntry',[-56,y],[r[0]+0.3,y],3)
        elif 'House' in g['name']:
            front=min([10,-14.5,-36,-60],key=lambda v:abs(v-r[0]))
            path(g['name']+'Gate',[front,y],[r[0]+0.4,y],2)
    background=[]
    for i,(x,y,dx,dy,h) in enumerate([(65,-80,12,12,12),(57,-54,12,11,10.5),(24,-41,10,9,12),(29,18,12,12,12),(30,45,11,10,10.5),(10,7,12,10,12),(-13,3,10,8,10.5),(-18,46,11,10,12),(-28,-41,10,9,12),(-40,-24,12,11,10.5),(-68,-39,12,12,12),(-68,-15,13,12,10.5),(-66,47,12,10,12),(-66,77,14,12,12),(-41,43,10,10,10.5),(35,65,10,10,12)]):
        background.append(dict(name='Background_%02d'%(i+1),rect=[x-dx/2,x+dx/2,y-dy/2,y+dy/2],height=h))
    plan=dict(groups=groups,paths=paths,pads=pads,background=background)
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    return plan

if __name__=='__main__':
    inspect()
    make_plan()
