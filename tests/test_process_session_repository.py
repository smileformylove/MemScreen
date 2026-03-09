import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from memscreen.services import session_analysis
from memscreen.storage import ProcessSessionRepository


class ProcessSessionRepositoryTest(unittest.TestCase):
  def test_round_trip(self):
    with TemporaryDirectory() as tmp:
      db_path = Path(tmp) / 'process.db'
      repo = ProcessSessionRepository(str(db_path))

      session_id = repo.insert_session(
          events=[
              {'time': '2026-03-09 10:00:00', 'text': 'keyboard: press (a)', 'type': 'keypress'},
              {'time': '2026-03-09 10:00:01', 'text': 'mouse: press (left)', 'type': 'click'},
          ],
          start_time='2026-03-09 10:00:00',
          end_time='2026-03-09 10:00:01',
      )

      self.assertGreater(session_id, 0)

      rows = repo.list_sessions(limit=5, include_events=True)
      self.assertEqual(len(rows), 1)
      self.assertEqual(rows[0]['session_id'], session_id)
      self.assertEqual(rows[0]['keystrokes'], 1)
      self.assertEqual(rows[0]['clicks'], 1)
      self.assertEqual(len(rows[0]['events']), 2)

      summary = repo.get_session(session_id)
      self.assertIsNotNone(summary)
      self.assertEqual(summary['event_count'], 2)

      deleted = repo.delete_session(session_id)
      self.assertEqual(deleted, 1)
      self.assertIsNone(repo.get_session(session_id))

  def test_session_analysis_contract_is_unchanged(self):
    with TemporaryDirectory() as tmp:
      db_path = str(Path(tmp) / 'process.db')
      events = [
          {'time': '2026-03-09 10:00:00', 'text': 'keyboard: press (a)', 'type': 'keypress'},
          {'time': '2026-03-09 10:00:02', 'text': 'mouse: press (left)', 'type': 'click'},
      ]

      session_id = session_analysis.save_session(
          events,
          '2026-03-09 10:00:00',
          '2026-03-09 10:00:02',
          db_path,
      )
      self.assertGreater(session_id, 0)

      rows = session_analysis.load_sessions(limit=10, db_path=db_path)
      self.assertEqual(len(rows), 1)
      self.assertEqual(rows[0][0], session_id)
      self.assertEqual(rows[0][3], 2)

      summary = session_analysis.get_session_summary(session_id, db_path=db_path)
      self.assertEqual(summary, rows[0])

      loaded_events = session_analysis.get_session_events(session_id, db_path=db_path)
      self.assertEqual(loaded_events, events)

      analysis = session_analysis.get_session_analysis(
          session_id,
          event_count=2,
          keystrokes=1,
          clicks=1,
          start_time='2026-03-09 10:00:00',
          end_time='2026-03-09 10:00:02',
          db_path=db_path,
      )
      self.assertIsNotNone(analysis)
      self.assertEqual(analysis['event_count'], 2)
      self.assertIn('patterns', analysis)

      deleted_count = session_analysis.delete_all_sessions(db_path=db_path)
      self.assertEqual(deleted_count, 1)
      self.assertEqual(session_analysis.load_sessions(limit=10, db_path=db_path), [])


if __name__ == '__main__':
  unittest.main()
