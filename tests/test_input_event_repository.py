import datetime
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from memscreen.process_mining import ProcessMiningAnalyzer
from memscreen.storage import InputEventRepository


class InputEventRepositoryTest(unittest.TestCase):
  def test_round_trip_and_filters(self):
    with TemporaryDirectory() as tmp:
      db_path = Path(tmp) / 'input.db'
      repo = InputEventRepository(str(db_path))

      first_id = repo.insert_event(
          event_type='keyboard',
          action='press',
          content='a',
          details='',
          operate_time='2026-03-09T10:00:00+08:00',
      )
      second_id = repo.insert_event(
          event_type='mouse',
          action='press',
          content='left',
          details='Position: (10, 20)',
          operate_time='2026-03-09T10:00:02+08:00',
      )

      self.assertEqual(first_id, 1)
      self.assertEqual(second_id, 2)
      self.assertEqual(repo.get_latest_event_id(), 2)

      recent = repo.list_recent_events(limit=5)
      self.assertEqual(len(recent), 2)
      self.assertEqual(recent[0]['id'], 2)

      since_first = repo.list_recent_events(limit=5, since_id=1)
      self.assertEqual([row['id'] for row in since_first], [2])

      keyboard_only = repo.list_events(operate_type='keyboard')
      self.assertEqual(len(keyboard_only), 1)
      self.assertEqual(keyboard_only[0]['content'], 'a')

  def test_process_mining_analyzer_uses_repository_data(self):
    with TemporaryDirectory() as tmp:
      db_path = Path(tmp) / 'input.db'
      repo = InputEventRepository(str(db_path))
      repo.insert_event(
          event_type='keyboard',
          action='press',
          content='a',
          details='',
          operate_time='2026-03-09T10:00:00+08:00',
      )
      repo.insert_event(
          event_type='mouse',
          action='press',
          content='left',
          details='Position: (10, 20)',
          operate_time='2026-03-09T10:00:02+08:00',
      )

      analyzer = ProcessMiningAnalyzer(str(db_path))
      events = analyzer.load_event_logs(
          start_time=datetime.datetime.fromisoformat('2026-03-09T09:59:00+08:00'),
          end_time=datetime.datetime.fromisoformat('2026-03-09T10:05:00+08:00'),
      )

      self.assertEqual(len(events), 2)
      self.assertEqual(events[0]['activity'], 'keyboard_press')
      self.assertEqual(events[1]['activity'], 'mouse_press')
      self.assertEqual(events[1]['resource'], 'mouse')


if __name__ == '__main__':
  unittest.main()
