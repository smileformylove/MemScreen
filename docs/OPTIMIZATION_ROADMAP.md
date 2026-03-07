# Optimization Roadmap

## Goal

Improve maintainability, delivery speed, and runtime stability without disrupting MemScreen's primary product path:

1. recording
2. album / playback / retrieval
3. optional local AI

## Current architecture snapshot

### Frontend

- Entry: `frontend/flutter/lib/main.dart`
- Navigation shell: `frontend/flutter/lib/screens/home_scaffold.dart`
- Shared state: `frontend/flutter/lib/app_state.dart`
- HTTP clients: `frontend/flutter/lib/api/`

### Backend

- Entry: `memscreen/api/__main__.py`
- Route hub: `memscreen/api/app.py`
- Dependency wiring: `memscreen/api/deps.py`

### Core orchestration

- Chat: `memscreen/presenters/chat_presenter.py`
- Recording: `memscreen/presenters/recording_presenter.py`
- Video album: `memscreen/presenters/video_presenter.py`
- Process mining: `memscreen/presenters/process_mining_presenter.py`

### Domain / infrastructure

- Audio capture and routing: `memscreen/audio/audio_recorder.py`
- Memory kernel: `memscreen/memory/memory.py`
- Config center: `memscreen/config/__init__.py`
- Shared SQLite manager: `memscreen/storage/sqlite.py`

## Main problems

### 1. Oversized modules

The largest files currently combine too many concerns:

- `memscreen/presenters/chat_presenter.py`
- `memscreen/presenters/recording_presenter.py`
- `memscreen/audio/audio_recorder.py`
- `frontend/flutter/lib/app_state.dart`

This slows iteration, raises regression risk, and makes testing harder.

### 2. Backend boundary blur

`memscreen/api/app.py` directly coordinates route parsing, database reads, process-session linking, streaming, and presenter calls. That makes API changes risky and discourages route-level tests.

### 3. Storage access duplication

There is already a reusable SQLite manager, but many modules still open raw `sqlite3` connections directly. Schema, transactions, and query patterns are therefore spread across API routes, presenters, trackers, and services.

### 4. Frontend state concentration

`AppState` currently owns:

- connection lifecycle
- API client replacement
- recording defaults persistence
- recording start/stop orchestration
- tracking auto-bind logic
- floating-ball platform bridge
- watchdog timers and refresh versioning

That is a strong signal to split by domain.

### 5. Product-critical and AI paths are interleaved

Recorder and album should remain stable even when local model runtime is missing, slow, or disabled. Today those paths are better than before, but still coupled in a few places via presenter wiring and capability checks.

### 6. Documentation drift

Some docs no longer match the live HTTP surface or the Flutter-first architecture. Drift increases onboarding cost and makes refactors harder to trust.

## Prioritization principle

When tradeoffs appear, optimize in this order:

1. recorder reliability
2. video album responsiveness
3. process tracking correctness
4. chat / local AI ergonomics
5. packaging and developer experience

## Phased plan

## Phase 1: Baseline and contract cleanup

### Objectives

- make the current system observable
- align docs with real behavior
- identify highest-traffic bottlenecks before refactoring

### Work items

- Document the actual API surface in `docs/API_HTTP.md`
- Keep `docs/ARCHITECTURE.md` aligned with the Flutter + FastAPI runtime
- Add lightweight timing/log markers around:
  - recording start
  - recording stop
  - `/video/list`
  - `/chat`
  - tracking session save
- Capture startup and first-use timings for:
  - API boot
  - Flutter connect
  - first recording
  - first chat request

### Success criteria

- team can describe real request flow in one pass
- docs match runtime endpoints
- slowest user-visible paths are measured, not guessed

## Phase 2: Protect the recorder/album path

### Objectives

- improve the product-critical path before deeper refactors

### Work items

- move video metadata queries behind a repository/service boundary
- reduce repeated direct SQLite access in recording/video modules
- batch high-frequency input-tracking writes where safe
- cache or memoize expensive audio device discovery where appropriate
- ensure recording works with models disabled

### Success criteria

- recording start/stop becomes predictable
- video list stays responsive as local data grows
- tracking overhead does not meaningfully degrade recording

## Phase 3: Split the backend by domain

### Objectives

- make API and service evolution safer

### Target shape

- `memscreen/api/routers/chat.py`
- `memscreen/api/routers/models.py`
- `memscreen/api/routers/process.py`
- `memscreen/api/routers/recording.py`
- `memscreen/api/routers/video.py`
- `memscreen/api/routers/system.py`

### Work items

- keep `app.py` as composition root only
- move request/response models closer to their route groups
- move non-routing helpers out of `app.py`
- add route-level tests for critical flows

### Success criteria

- new endpoints no longer require editing a monolithic file
- route tests can mock presenters cleanly

## Phase 4: Split frontend state by domain

### Objectives

- reduce coupling inside Flutter
- make screen-specific changes easier to ship

### Target shape

- `ConnectionStore`
- `RecordingStore`
- `SettingsStore`
- `ChatStore`
- `ProcessStore`

### Work items

- move API reconnect logic out of the recording flow state
- isolate floating-ball integration behind a dedicated service/store
- minimize `notifyListeners()` blast radius
- keep screen widgets dependent only on the state they actually use

### Success criteria

- recording changes do not risk chat/settings behavior
- UI rebuild scope becomes smaller and easier to reason about

## Phase 5: Decompose presenter responsibilities

### Objectives

- reduce the size and role overlap of large Python classes

### Suggested extractions

- from `ChatPresenter`
  - thread persistence
  - streaming controller
  - visual evidence / OCR helper
  - model selection and auto-pull policy
- from `RecordingPresenter`
  - persistence repository
  - frame capture pipeline
  - post-recording analysis pipeline
  - screen/window target resolution
- from `AudioRecorder`
  - device discovery
  - ffmpeg backend
  - ScreenCaptureKit backend
  - CoreAudio output routing

### Success criteria

- each extracted module has one primary responsibility
- presenter files shrink substantially without feature loss

## Phase 6: Isolate AI capability from core product paths

### Objectives

- keep AI optional in both startup and runtime paths

### Work items

- treat capability services as adapters behind stable interfaces
- make graceful degradation explicit for model-unavailable scenarios
- separate recorder metadata enrichment from the act of recording itself
- move model catalog/download flows into a clearly bounded subsystem

### Success criteria

- recorder and album remain healthy even when models fail
- AI failures become recoverable instead of contagious

## Phase 7: Strengthen tests around the new boundaries

### Objectives

- protect refactors with smaller, more stable tests

### Work items

- add router tests for HTTP contract
- add repository tests for SQLite-backed queries
- add presenter/service tests with mocks instead of end-to-end-only coverage
- keep a small number of full integration tests for the real user flows

### Success criteria

- regression detection becomes faster and more local
- test suite reflects the current Flutter + FastAPI architecture

## Immediate execution batch

This is the recommended near-term order:

1. fix docs drift
2. measure recorder and album bottlenecks
3. centralize recording/video/process SQLite access
4. split backend routers
5. split Flutter state
6. decompose large presenters

## What not to do first

- do not begin with a broad memory/LLM redesign
- do not change packaging and runtime bootstrap before recorder stability is measured
- do not split files mechanically without first deciding ownership boundaries

## First concrete refactor candidates

- create a repository layer for recording/video/process SQLite operations
- move process-session persistence helpers out of `memscreen/api/app.py`
- split `AppState` recording logic into a dedicated store/service pair
- extract audio backend selection from `AudioRecorder`

## Deliverable expectation for the next batch

The next code batch should aim to produce:

- one backend repository module for recording/video metadata
- one smaller API router extraction as a pattern
- one Flutter state split that reduces `AppState` responsibility without changing UI behavior
