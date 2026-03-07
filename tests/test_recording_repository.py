import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from memscreen.storage import RecordingMetadataRepository


class RecordingMetadataRepositoryTest(unittest.TestCase):
  def test_round_trip(self):
    with TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      db_path = tmp_path / 'recordings.db'
      filename = str(tmp_path / 'demo.mp4')

      repo = RecordingMetadataRepository(str(db_path))
      repo.ensure_schema()
      repo.ensure_saved_regions_schema()
      rowid = repo.insert_recording(
          filename=filename,
          frame_count=120,
          fps=30.0,
          duration=4.0,
          file_size=1024,
          recording_mode='fullscreen',
          audio_source='mixed',
      )

      self.assertGreater(rowid, 0)

      row = repo.get_recording(filename)
      self.assertIsNotNone(row)
      self.assertEqual(row['frame_count'], 120)
      self.assertEqual(row['audio_source'], 'mixed')
      self.assertEqual(row['recording_mode'], 'fullscreen')

      metrics = repo.get_recording_metrics(filename)
      self.assertEqual(metrics, (120, 30.0, row['timestamp'], 4.0))

      deleted = repo.delete_recording(filename)
      self.assertEqual(deleted, 1)
      self.assertIsNone(repo.get_recording(filename))

  def test_handles_legacy_schema(self):
    with TemporaryDirectory() as tmp:
      tmp_path = Path(tmp)
      db_path = tmp_path / 'legacy.db'
      repo = RecordingMetadataRepository(str(db_path))

      conn = sqlite3.connect(db_path)
      try:
        conn.execute(
            '''
            CREATE TABLE recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                frame_count INTEGER,
                fps REAL,
                duration REAL,
                file_size INTEGER
            )
            ''',
        )
        conn.execute(
            '''
            INSERT INTO recordings (filename, timestamp, frame_count, fps, duration, file_size)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (str(tmp_path / 'legacy.mp4'), '2026-03-07 10:00:00', 10, 5.0, 2.0, 256),
        )
        conn.commit()
      finally:
        conn.close()

      rows = repo.list_recordings()
      self.assertEqual(len(rows), 1)
      self.assertEqual(rows[0]['recording_mode'], 'fullscreen')
      self.assertEqual(rows[0]['analysis_status'], 'pending')
      self.assertIsNone(rows[0]['audio_source'])


if __name__ == '__main__':
  unittest.main()
