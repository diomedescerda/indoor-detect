import unittest
from evaluate import iou,match,scores,bootstrap
import numpy as np

class MatchingTests(unittest.TestCase):
    def test_one_to_one_and_wrong_class(self):
        gt=[dict(category_id=1,bbox=[0,0,10,10])]
        preds=[dict(category_id=c,bbox=[0,0,10,10],score=s) for c,s in [(1,.9),(1,.8),(62,.7)]]
        matched,fp,fn=match(gt,preds)
        self.assertEqual((len(matched),len(fp),len(fn)),(1,2,0))
    def test_empty_images_and_misses(self):
        gt=[dict(category_id=1,bbox=[0,0,10,10])]
        self.assertEqual(len(match(gt,[])[2]),1)
        self.assertEqual(len(match([],[dict(category_id=1,bbox=[0,0,10,10],score=.9)])[1]),1)
        self.assertIsNone(scores(0,0,0)['recall'])
    def test_touching_and_degenerate(self):
        self.assertEqual(iou([0,0,10,10],[10,0,10,10]),0)
        self.assertEqual(iou([0,0,0,10],[0,0,10,10]),0)
    def test_paired_bootstrap_known_extreme(self):
        a=[dict(tp=1,fp=0,fn=0,gt=1,predictions=1)]*3
        b=[dict(tp=0,fp=0,fn=1,gt=1,predictions=0)]*3
        result=bootstrap(a,b,np.array([[0,1,2],[2,2,0]]))
        self.assertEqual(result,dict(delta_f1=1.,ci95_low=1.,ci95_high=1.))
if __name__=='__main__':unittest.main()
