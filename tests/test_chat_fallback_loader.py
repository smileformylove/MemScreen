import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from memscreen.services.chat_fallback_loader import ChatFallbackDataService
from memscreen.storage import ProcessSessionRepository, RecordingMetadataRepository


class ChatFallbackLoaderTest(unittest.TestCase):
  def test_loads_recordings_and_process_sessions(self):
    with TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      recording_db = tmp_path / 'recordings.db'
      process_db = tmp_path / 'process.db'

      recordings = RecordingMetadataRepository(str(recording_db))
      recordings.insert_recording(
          filename=str(tmp_path / 'demo.mp4'),
          frame_count=120,
          fps=30.0,
          duration=4.0,
          file_size=1024,
          recording_mode='fullscreen',
          window_title='Window: Terminal · Session',
          content_tags='["coding"]',
          content_keywords='["python"]',
          content_summary='Terminal coding session',
          audio_source='mixed',
      )

      sessions = ProcessSessionRepository(str(process_db))
      sessions.insert_session(
          events=[{'time': '2026-03-09 10:00:00', 'text': 'keyboard: press (a)', 'type': 'keypress'}],
          start_time='2026-03-09 10:00:00',
          end_time='2026-03-09 10:00:00',
      )

      service = ChatFallbackDataService(
          recording_db_path=str(recording_db),
          process_db_path=str(process_db),
      )

      recording_rows = service.load_recent_recordings(limit=5)
      self.assertEqual(len(recording_rows), 1)
      self.assertEqual(recording_rows[0]['basename'], 'demo.mp4')
      self.assertEqual(recording_rows[0]['recording_mode'], 'fullscreen')

      process_rows = service.load_recent_process_sessions(limit=5, include_events=True)
      self.assertEqual(len(process_rows), 1)
      self.assertEqual(process_rows[0]['event_count'], 1)
      self.assertEqual(len(process_rows[0]['events']), 1)


if __name__ == '__main__':
  unittest.main()
