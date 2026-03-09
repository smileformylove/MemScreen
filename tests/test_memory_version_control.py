import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from memscreen.memory.memory_version_control import MemoryVersionControl
from memscreen.storage import MemoryVersionRepository


class MemoryVersionControlTest(unittest.TestCase):
  def test_repository_round_trip(self):
    with TemporaryDirectory() as tmp:
      db_path = Path(tmp) / 'versions.db'
      repo = MemoryVersionRepository(str(db_path))

      repo.insert_version(
          version_id='v1',
          memory_id='mem-1',
          content='hello',
          metadata={'category': 'fact'},
          parent_version=None,
          change_type='add',
          created_at='2026-03-09T10:00:00',
      )
      repo.insert_version(
          version_id='v2',
          memory_id='mem-1',
          content='hello world',
          metadata={'category': 'fact', 'tag': 'updated'},
          parent_version='v1',
          change_type='update',
          created_at='2026-03-09T10:00:01',
      )

      version = repo.get_version('v2')
      self.assertIsNotNone(version)
      self.assertEqual(version['memory_id'], 'mem-1')
      self.assertEqual(version['metadata']['tag'], 'updated')

      history = repo.list_versions('mem-1', limit=10)
      self.assertEqual([row['version_id'] for row in history], ['v2', 'v1'])
      self.assertEqual(repo.list_memory_ids(), ['mem-1'])
      self.assertEqual(repo.get_stats()['total_versions'], 2)

  def test_version_control_rollback_keeps_history(self):
    with TemporaryDirectory() as tmp:
      db_path = Path(tmp) / 'versions.db'
      vc = MemoryVersionControl(str(db_path))

      first = vc.create_version(
          memory_id='mem-1',
          content='first',
          metadata={'category': 'fact'},
          change_type='add',
      )
      second = vc.create_version(
          memory_id='mem-1',
          content='second',
          metadata={'category': 'fact', 'rev': 2},
          parent_version=first,
          change_type='update',
      )

      self.assertIsNotNone(vc.get_version(first))
      self.assertTrue(vc.rollback_to_version('mem-1', first))

      history = vc.get_version_history('mem-1', limit=10)
      self.assertEqual(len(history), 3)
      self.assertEqual(history[0]['change_type'], 'rollback')
      self.assertEqual(history[0]['content'], 'first')
      self.assertEqual(history[0]['parent_version'], first)
      self.assertEqual(history[1]['version_id'], second)

      stats = vc.get_stats()
      self.assertEqual(stats['total_versions'], 3)
      self.assertEqual(stats['total_memories'], 1)
      self.assertEqual(vc.get_all_memories(), ['mem-1'])


if __name__ == '__main__':
  unittest.main()
