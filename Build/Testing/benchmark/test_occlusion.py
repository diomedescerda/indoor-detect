"""Boundary, integrity and capture-group resampling tests for occlusion analysis."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from analyze_occlusion import (area_stratum, build_instances, make_summaries,
                               read_labels, review_rows, sha256, summarize, validate_sources, verify_batch_sources, CONFIGS)


def label(annotation_id=1, image_id=1, **overrides):
    return dict(annotation_id=annotation_id, image_id=image_id, occlusion='partial',
                truncation=False, confidence='high', reason='A chair blocks part of the target.', **overrides)


class LabelIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'labels_batch_test.json'
        self.annotations = [dict(id=1, image_id=1), dict(id=2, image_id=4)]

    def read(self, records):
        self.path.write_text(json.dumps(records))
        return read_labels([self.path], self.annotations)

    def test_both_supported_containers(self):
        records = [label(), label(2, 4)]
        self.assertEqual(self.read(records), self.read({'records': records, 'status': 'provisional'}))
        self.assertEqual(self.read(records), self.read({'annotations': records}))

    def test_author_review_markers_and_initial_ai_label_survive(self):
        reviewed = {**label(), 'human_reviewed': True, 'human_reviewed_at': '2026-10-16T12:00:00Z',
                    'initial_ai_label': {**label(), 'occlusion': 'uncertain'}}
        records = self.read({'annotations': [reviewed, label(2, 4)]})
        self.assertEqual(records[1], reviewed)
        with self.assertRaisesRegex(ValueError, 'human_reviewed must be boolean'):
            self.read([{**reviewed, 'human_reviewed': 'true'}, label(2, 4)])

    def test_never_imputes_missing_labels(self):
        with self.assertRaisesRegex(ValueError, 'Missing 1'):
            self.read([label()])

    def test_rejects_duplicates_even_in_different_files(self):
        self.path.write_text(json.dumps([label(), label(2, 4)]))
        with self.assertRaisesRegex(ValueError, 'Duplicate label'):
            read_labels([self.path, self.path], self.annotations)

    def test_rejects_unknown_id_wrong_image_and_malformed_fields(self):
        invalid = [dict(annotation_id=999), dict(image_id=99), dict(occlusion='50%'),
                   dict(truncation='false'), dict(confidence='likely'), dict(reason=''), dict(annotation_id=True)]
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.read([{**label(), **changes}, label(2, 4)])


class SourceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.gt_path = Path(self.temp.name)/'labels.json'
        images = []
        for group in range(1, 34):
            for mount, lens in CONFIGS:
                image_id = len(images)+1
                images.append(dict(id=image_id, file_name=f'{image_id}.jpeg', capture_group=group,
                                   mount=mount, lens=lens, width=100, height=100))
        self.gt = dict(images=images, categories=[dict(id=1, name='chair')],
                       annotations=[dict(id=index+1, image_id=index%198+1, category_id=1,
                                         bbox=[0, 0, 10, 10]) for index in range(889)])
        self.gt_path.write_text(json.dumps(self.gt))
        self.run = dict(metadata=dict(gt_sha256=sha256(self.gt_path), confidence=.30,
                                      max_objects=2, detector_cap=15),
                        frames=[dict(image_id=image['id'], file_name=image['file_name'], predictions=[])
                                for image in images])

    def test_inspector_source_hashes_match_frozen_inputs(self):
        documents = {'batch.json': {'source_hashes': {'labels.json': 'ground-truth', 'images': {'photo.jpg': 'photo-hash'}}}}
        verify_batch_sources(documents, 'ground-truth', {'photo.jpg': 'photo-hash'})
        alternative = {'batch2.json': {'source_labels_sha256': 'ground-truth', 'source_images_sha256': {'photo.jpg': 'photo-hash'}}}
        verify_batch_sources(alternative, 'ground-truth', {'photo.jpg': 'photo-hash'})
        with self.assertRaisesRegex(ValueError, 'photo hash mismatch'):
            verify_batch_sources(alternative, 'ground-truth', {'photo.jpg': 'changed'})
        with self.assertRaisesRegex(ValueError, 'ground truth hash mismatch'):
            verify_batch_sources(documents, 'changed', {'photo.jpg': 'photo-hash'})
        with self.assertRaisesRegex(ValueError, 'photo hash mismatch'):
            verify_batch_sources(documents, 'ground-truth', {'photo.jpg': 'changed'})

    def test_complete_frozen_sources_are_accepted(self):
        images, frames, categories, groups = validate_sources(self.gt, self.run, self.gt_path)
        self.assertEqual((len(images), len(frames), len(groups)), (198, 198, 33))

    def test_modified_gt_hash_is_rejected(self):
        self.gt_path.write_text(self.gt_path.read_text()+' ')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            validate_sources(self.gt, self.run, self.gt_path)

    def test_duplicate_frames_and_wrong_configuration_and_settings_are_rejected(self):
        run = copy.deepcopy(self.run)
        run['frames'][-1] = run['frames'][0]
        with self.assertRaisesRegex(ValueError, 'frame IDs'):
            validate_sources(self.gt, run, self.gt_path)
        gt = copy.deepcopy(self.gt)
        gt['images'][1]['lens'] = '1x'
        with self.assertRaisesRegex(ValueError, 'capture groups'):
            validate_sources(gt, self.run, self.gt_path)
        run = copy.deepcopy(self.run)
        run['metadata']['max_objects'] = 3
        with self.assertRaisesRegex(ValueError, 'app cap 2'):
            validate_sources(self.gt, run, self.gt_path)


class MatchingAndStrataTests(unittest.TestCase):
    def test_area_boundaries_are_prespecified(self):
        self.assertEqual([area_stratum(value) for value in (0, .009999, .01, .099999, .10, 1)],
                         ['small', 'small', 'medium', 'medium', 'large', 'large'])
        for value in (-.01, float('nan'), float('inf')):
            with self.assertRaises(ValueError): area_stratum(value)

    def test_match_once_before_assigning_visibility_and_app_cap(self):
        image = dict(id=1, file_name='example.jpeg', capture_group=1,
                     mount='head_harness', lens='1x', width=100, height=100)
        annotations = [dict(id=index+1, image_id=1, category_id=1, bbox=[index*15, 0, 10, 10]) for index in range(3)]
        # Wrong-class and duplicate boxes consume output slots and remain FP. A .30
        # prediction is retained; .299 is removed. Match is over all GT, not each stratum.
        preds = [dict(image_id=1, category_id=2, bbox=[0, 0, 10, 10], score=.99),
                 dict(image_id=1, category_id=1, bbox=[0, 0, 10, 10], score=.9),
                 dict(image_id=1, category_id=1, bbox=[0, 0, 10, 10], score=.8),
                 dict(image_id=1, category_id=1, bbox=[15, 0, 10, 10], score=.30),
                 dict(image_id=1, category_id=1, bbox=[30, 0, 10, 10], score=.299)]
        gt = dict(images=[image], annotations=annotations, categories=[dict(id=1, name='chair'), dict(id=2, name='bed')])
        labels = {1: {**label(), 'occlusion': 'none'}, 2: {**label(2), 'occlusion': 'heavy', 'confidence': 'medium', 'truncation': True},
                  3: {**label(3), 'occlusion': 'uncertain'}}
        rows, totals = build_instances(gt, dict(frames=[dict(image_id=1, predictions=preds)]), labels)
        self.assertEqual([row['tp'] for row in rows if row['mode']=='detector'], [1, 1, 0])
        self.assertEqual([row['tp'] for row in rows if row['mode']=='app_output'], [1, 0, 0])
        self.assertEqual([(row['tp'], row['fp'], row['fn']) for row in totals], [(2, 2, 1), (1, 1, 2)])
        tables = make_summaries(rows, [1], np.zeros((5, 1), dtype=int))
        self.assertEqual(sum(row['gt'] for row in tables['severity'] if row['mode']=='detector'), 2)
        self.assertEqual(tables['uncertainty'][0]['gt'], 1)
        self.assertEqual(len(tables['sensitivity']), 18)
        self.assertEqual(sum(row['gt'] for row in tables['by_class_area'] if row['mode'] == 'detector'), 2)
        self.assertTrue(all(row['sparse_stratum'] for row in tables['by_class_area']))
        self.assertTrue(all(row['occlusion'] != 'uncertain' for row in tables['sensitivity']))
        self.assertTrue(all(row['gt'] == 0 for row in tables['sensitivity'] if row['occlusion'] == 'heavy'))
        self.assertTrue(all(row['gt'] == 1 for row in tables['sensitivity'] if row['occlusion'] == 'none'))
        self.assertEqual(len(review_rows(rows)), 3)
        self.assertTrue(all(row['human_review_status']=='pending' for row in review_rows(rows)))

    def test_detector_cap_15_and_app_cap_2(self):
        image = dict(id=1, file_name='example.jpeg', capture_group=1,
                     mount='head_harness', lens='1x', width=1000, height=100)
        annotations = [dict(id=index+1, image_id=1, category_id=1, bbox=[index*15, 0, 10, 10]) for index in range(16)]
        gt = dict(images=[image], annotations=annotations, categories=[dict(id=1, name='chair')])
        preds = [dict(image_id=1, category_id=1, bbox=ann['bbox'], score=.9-index*.01) for index, ann in enumerate(annotations)]
        _, totals = build_instances(gt, dict(frames=[dict(image_id=1, predictions=preds)]), {ann['id']: label(ann['id']) for ann in annotations})
        self.assertEqual([row['tp'] for row in totals], [15, 2])
        self.assertEqual([row['fn'] for row in totals], [1, 14])


class BootstrapTests(unittest.TestCase):
    def test_resamples_whole_group_counts_not_individuals_or_group_means(self):
        # Group 1 has 1/1, group 2 has 0/3. Pooled recall is 1/4, not .5.
        rows = [dict(capture_group=1, tp=1, occlusion='none', confidence='high')]
        rows += [dict(capture_group=2, tp=0, occlusion='none', confidence='high')]*3
        draws = np.array([[0, 0], [0, 1], [1, 1]])
        result = summarize(rows, [1, 2], draws)
        self.assertEqual((result['gt'], result['tp'], result['fn'], result['recall']), (4, 1, 3, .25))
        self.assertAlmostEqual(result['recall_ci95_low'], .0125)
        self.assertAlmostEqual(result['recall_ci95_high'], .9625)
        self.assertEqual(result['capture_groups_with_gt'], 2)

    def test_zero_denominator_draws_are_counted_not_forced_to_zero(self):
        rows = [dict(capture_group=1, tp=1, occlusion='none', confidence='high')]
        result = summarize(rows, [1, 2], np.array([[0, 0], [1, 1]]))
        self.assertEqual(result['bootstrap_valid_draws'], 1)
        self.assertEqual((result['recall_ci95_low'], result['recall_ci95_high']), (1, 1))
        empty = summarize([], [1, 2], np.array([[0, 1]]))
        self.assertIsNone(empty['recall'])
        self.assertIsNone(empty['recall_ci95_low'])
        self.assertEqual(empty['bootstrap_valid_draws'], 0)


if __name__ == '__main__':
    unittest.main()
