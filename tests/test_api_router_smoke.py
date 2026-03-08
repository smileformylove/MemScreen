import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

import memscreen.api.routers.process as process_router_module
from memscreen.api import deps
from memscreen.api.app import app


class _DummyChatPresenter:
  def __init__(self):
    self.active = 't1'

  def get_available_models(self):
    return ['m1', 'm2']

  def get_current_model(self):
    return 'm1'

  def set_model(self, model):
    self.model = model
    return model in {'m1', 'm2'}

  def list_chat_threads(self):
    return [{'id': 't1', 'title': 'one'}]

  def get_active_thread_id(self):
    return self.active

  def create_chat_thread(self, title):
    self.active = 't2'
    return {'id': 't2', 'title': title}

  def switch_chat_thread(self, thread_id):
    if thread_id not in {'t1', 't2'}:
      return False
    self.active = thread_id
    return True

  def get_thread_history(self, thread_id=None):
    class Msg:
      def __init__(self, role, content, timestamp):
        self.role = role
        self.content = content
        self.timestamp = timestamp

    return [Msg('user', 'hello', '2026-03-07 10:00:00')]


class _DummyVideoItem:
  def to_dict(self):
    return {'filename': '/tmp/demo.mp4', 'duration': 1.0}


class _DummyVideoPresenter:
  def get_video_list(self):
    return [_DummyVideoItem()]

  def resolve_playable_path(self, filename):
    return filename + '.playable'


class _DummyRecordingPresenter:
  def __init__(self):
    self.last_start_error = None
    self._mode = {
        'mode': 'fullscreen',
        'bbox': None,
        'screen_index': None,
        'screen_display_id': None,
    }
    self.audio_recorder = type(
        'AudioRecorder',
        (),
        {'diagnose_source': lambda self, source: {'source': getattr(source, 'value', str(source)), 'ok': True}},
    )()
    self.started = False

  def set_recording_mode(self, mode, **kwargs):
    self._mode = {
        'mode': mode,
        'bbox': kwargs.get('bbox'),
        'screen_index': kwargs.get('screen_index'),
        'screen_display_id': kwargs.get('screen_display_id'),
    }
    return True

  def set_audio_source(self, source):
    self.audio_source = source

  def set_video_format(self, video_format):
    self.video_format = video_format

  def set_audio_output_format(self, audio_format):
    self.audio_format = audio_format

  def set_audio_denoise(self, enabled):
    self.audio_denoise = enabled

  def start_recording(self, duration=60, interval=2.0):
    self.started = True
    self.duration = duration
    self.interval = interval
    return True

  def stop_recording(self):
    self.started = False

  def get_recording_status(self):
    return {
        'is_recording': self.started,
        'duration': getattr(self, 'duration', 0),
        'interval': getattr(self, 'interval', 0),
    }

  def get_recording_mode(self):
    return dict(self._mode)

  def get_available_screens(self):
    return [
        {
            'index': 0,
            'name': 'Main',
            'width': 100,
            'height': 100,
            'is_primary': True,
            'display_id': 1,
        }
    ]

  def reanalyze_recording_content(self, filename):
    return {'ok': True, 'filename': filename, 'content_summary': 'done'}


class _DummyProcessPresenter:
  def __init__(self):
    self.is_tracking = False

  def start_tracking(self):
    self.is_tracking = True
    return True

  def stop_tracking(self):
    self.is_tracking = False
    return True

  def get_recent_events(self, limit=10000):
    return [
        {'operate_type': 'keyboard', 'action': 'press', 'content': 'a', 'timestamp': '2026-03-07 10:00:00'},
        {'operate_type': 'mouse', 'action': 'press', 'content': 'left', 'timestamp': '2026-03-07 10:00:01'},
    ]

  def get_tracking_status(self):
    return {'is_tracking': self.is_tracking, 'event_count': 2}

  def mark_tracking_baseline(self):
    return self.is_tracking

  def advance_tracking_baseline(self):
    return True


class ApiRouterSmokeTest(unittest.TestCase):
  def setUp(self):
    self.client = TestClient(app)
    self.old_chat = deps._chat_presenter
    self.old_chat_init = deps._chat_presenter_initialized
    self.old_video = deps._video_presenter
    self.old_video_init = deps._video_presenter_initialized
    self.old_recording = deps._recording_presenter
    self.old_recording_init = deps._recording_presenter_initialized
    self.old_process = deps._process_mining_presenter
    self.old_process_init = deps._process_mining_presenter_initialized
    self.old_db_fn = deps.get_process_db_path
    self.old_persist = process_router_module.persist_process_session_memory
    self.old_delete = process_router_module.delete_process_session_memory
    self.old_delete_all = process_router_module.delete_all_process_session_memories
    self.old_models_dir_env = os.environ.get('MEMSCREEN_OLLAMA_MODELS_DIR')

    deps._chat_presenter = _DummyChatPresenter()
    deps._chat_presenter_initialized = True
    deps._video_presenter = _DummyVideoPresenter()
    deps._video_presenter_initialized = True
    deps._recording_presenter = _DummyRecordingPresenter()
    deps._recording_presenter_initialized = True
    deps._process_mining_presenter = _DummyProcessPresenter()
    deps._process_mining_presenter_initialized = True
    os.environ['MEMSCREEN_OLLAMA_MODELS_DIR'] = '/Volumes/TestDrive/models/ollama'
    process_router_module.persist_process_session_memory = lambda **kwargs: False
    process_router_module.delete_process_session_memory = lambda session_id: 0
    process_router_module.delete_all_process_session_memories = lambda: 0

    self.temp_dir = TemporaryDirectory()
    deps.get_process_db_path = lambda: str(Path(self.temp_dir.name) / 'process.db')

  def tearDown(self):
    self.temp_dir.cleanup()
    deps._chat_presenter = self.old_chat
    deps._chat_presenter_initialized = self.old_chat_init
    deps._video_presenter = self.old_video
    deps._video_presenter_initialized = self.old_video_init
    deps._recording_presenter = self.old_recording
    deps._recording_presenter_initialized = self.old_recording_init
    deps._process_mining_presenter = self.old_process
    deps._process_mining_presenter_initialized = self.old_process_init
    deps.get_process_db_path = self.old_db_fn
    process_router_module.persist_process_session_memory = self.old_persist
    process_router_module.delete_process_session_memory = self.old_delete
    process_router_module.delete_all_process_session_memories = self.old_delete_all
    if self.old_models_dir_env is None:
      os.environ.pop('MEMSCREEN_OLLAMA_MODELS_DIR', None)
    else:
      os.environ['MEMSCREEN_OLLAMA_MODELS_DIR'] = self.old_models_dir_env

  def test_router_paths_are_available(self):
    response = self.client.get('/openapi.json')
    self.assertEqual(response.status_code, 200)
    paths = response.json()['paths']
    for path in [
      '/chat',
      '/chat/stream',
      '/chat/models',
      '/chat/history',
      '/models/catalog',
      '/video/list',
      '/recording/start',
      '/process/sessions',
      '/process/sessions/from-tracking',
      '/config',
      '/health',
    ]:
      self.assertIn(path, paths)

  def test_models_catalog_exposes_qwen35_and_storage(self):
    response = self.client.get('/models/catalog')
    self.assertEqual(response.status_code, 200)
    payload = response.json()
    self.assertEqual(payload['models_dir'], '/Volumes/TestDrive/models/ollama')
    self.assertTrue(payload['models_dir_external'])
    self.assertEqual(payload['current_chat_model'], 'm1')
    self.assertEqual(payload['available_chat_models'], ['m1', 'm2'])
    names = {item['name'] for item in payload['models']}
    self.assertIn('qwen3:0.6b', names)
    self.assertIn('qwen3:1.7b', names)
    self.assertIn('qwen3:4b', names)
    self.assertIn('qwen3-vl:2b', names)
    self.assertIn('qwen3-vl:4b', names)

  def test_chat_video_and_system_routes(self):
    self.assertEqual(self.client.get('/chat/models').json()['models'], ['m1', 'm2'])
    self.assertEqual(self.client.get('/chat/model').json()['model'], 'm1')
    self.assertEqual(self.client.get('/chat/threads').json()['active_thread_id'], 't1')
    self.assertEqual(self.client.get('/chat/history').json()['messages'][0]['content'], 'hello')
    self.assertEqual(self.client.get('/video/list').json()['videos'][0]['filename'], '/tmp/demo.mp4')
    self.assertEqual(self.client.get('/config').status_code, 200)
    self.assertEqual(self.client.get('/health').status_code, 200)

  def test_recording_routes(self):
    start = self.client.post('/recording/start', json={
        'duration': 9,
        'interval': 1.5,
        'mode': 'fullscreen-single',
        'screen_index': 0,
        'screen_display_id': 1,
        'video_format': 'mp4',
        'audio_format': 'wav',
        'audio_denoise': True,
    })
    self.assertEqual(start.status_code, 200)
    self.assertTrue(start.json()['ok'])

    status = self.client.get('/recording/status')
    self.assertEqual(status.status_code, 200)
    self.assertTrue(status.json()['is_recording'])
    self.assertEqual(status.json()['mode'], 'fullscreen-single')

    screens = self.client.get('/recording/screens')
    self.assertEqual(screens.status_code, 200)
    self.assertEqual(screens.json()['screens'][0]['display_id'], 1)

    stop = self.client.post('/recording/stop')
    self.assertEqual(stop.status_code, 200)
    self.assertTrue(stop.json()['ok'])

  def test_process_routes(self):
    saved = self.client.post('/process/sessions', json={
        'events': [{'time': '2026-03-07 09:00:00', 'text': 'keyboard: press (a)', 'type': 'keypress'}],
        'start_time': '2026-03-07 09:00:00',
        'end_time': '2026-03-07 09:00:00',
    })
    self.assertEqual(saved.status_code, 200)
    session_id = saved.json()['session_id']

    sessions = self.client.get('/process/sessions')
    self.assertEqual(sessions.status_code, 200)
    self.assertEqual(len(sessions.json()['sessions']), 1)

    events = self.client.get(f'/process/sessions/{session_id}')
    self.assertEqual(events.status_code, 200)
    self.assertEqual(len(events.json()['events']), 1)

    analysis = self.client.get(f'/process/sessions/{session_id}/analysis')
    self.assertEqual(analysis.status_code, 200)
    self.assertEqual(analysis.json()['event_count'], 1)

    tracking_start = self.client.post('/process/tracking/start')
    self.assertEqual(tracking_start.status_code, 200)
    self.assertTrue(tracking_start.json()['is_tracking'])

    mark = self.client.post('/process/tracking/mark-start')
    self.assertEqual(mark.status_code, 200)

    from_tracking = self.client.post('/process/sessions/from-tracking')
    self.assertEqual(from_tracking.status_code, 200)
    self.assertEqual(from_tracking.json()['events_saved'], 2)

    tracking_stop = self.client.post('/process/tracking/stop')
    self.assertEqual(tracking_stop.status_code, 200)

    deleted = self.client.delete(f'/process/sessions/{session_id}')
    self.assertEqual(deleted.status_code, 200)
    self.assertEqual(deleted.json()['deleted'], 1)


if __name__ == '__main__':
  unittest.main()
