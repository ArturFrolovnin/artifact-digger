"""Pure validation failure tests; no Blender/Unreal, assets or scene mutations."""
import copy
import math
import unittest

from common import PipelineError, compatible, expected_ue_bounds, validate_bounds


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.rig={'position_tolerance_cm':.002,'rotation_tolerance_deg':.02}
        self.bones=[dict(name='root',parent=None,translation=[0,0,0],rotation_xyzw=[0,0,0,1],scale=[1,1,1]),
                    dict(name='pelvis',parent='root',translation=[0,0,99],rotation_xyzw=[0,0,0,1],scale=[1,1,1])]

    def test_quaternion_sign_does_not_change_pose(self):
        other=copy.deepcopy(self.bones)
        other[1]['rotation_xyzw']=[0,0,0,-1]
        compatible(other,self.bones,self.rig)

    def test_reject_new_missing_or_reparented_bone(self):
        for change in ('added','missing','parent'):
            other=copy.deepcopy(self.bones)
            if change=='added':
                b=copy.deepcopy(other[1]);b['name']='extra';other.append(b)
            elif change=='missing':other.pop()
            else:other[1]['parent']=None
            with self.subTest(change=change),self.assertRaises(PipelineError):
                compatible(other,self.bones,self.rig)

    def test_reject_changed_rest_pose_or_scale(self):
        for change in ('position','rotation','scale'):
            other=copy.deepcopy(self.bones)
            if change=='position':other[1]['translation'][0]=.01
            elif change=='rotation':other[1]['rotation_xyzw']=[0,0,math.sin(.1),math.cos(.1)]
            else:other[1]['scale']=[100,100,100]
            with self.subTest(change=change),self.assertRaises(PipelineError):
                compatible(other,self.bones,self.rig)

    def test_centimetres_and_handedness(self):
        b=expected_ue_bounds([[-.5,-.2,0],[.6,.1,1.8]])
        self.assertEqual(b,[[-50,-10,0],[60,20,180]])
        validate_bounds(b,b,.2)
        with self.assertRaises(PipelineError):validate_bounds([[v*100 for v in row] for row in b],b,.2)
        with self.assertRaises(PipelineError):validate_bounds([[-50,-20,0],[60,10,180]],b,.2)


if __name__=='__main__':
    unittest.main()
