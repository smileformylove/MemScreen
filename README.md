# MemScreen

## Ask Screen Anything

MemScreen is a memory system to manage screen you watch everyday. you can also call it as ASA, which means "Ask Screen Anything" with a visual memory system! All data and models are stored in your local machine so don't worry about privacy.

### Key Features

- [x] Capture your screen in your local machine

- [x] Understand and Memorize your screen with local models(MLLM and OCR)

- [x] MemScreen can also be used as personal assistant to answer your questions about any other history, without any contents of screens.

- [x] **Process Mining**: Analyze keyboard and mouse interaction patterns to discover workflows, frequent sequences, and time-based patterns

## Installation

```
git clone https://github.com/smileformylove/MemScreen
cd MemScreen
pip install -r requirements.txt
```

### Model

```
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest
```

The performance of small models is limited. And you can also download large models to get better performance, especially for qwen3 and qwen2.5vl.

## Usage

### Capture your screen
```
python -W ignore memscreen.py
```

### Visualize your screen

```
python screenshot_ui.py
```
Here is the interface:
![alt text](./assests/screenshot_view.jpg)

### Chat with your memscreen

```
python chat_ui.py
```
Here is the interface:
![alt text](./assests/chat_view.jpg)

### Process Mining Analysis

MemScreen now includes process mining capabilities to analyze keyboard and mouse interaction data. This feature helps you discover:

- **Activity Frequency**: Most common keyboard and mouse actions
- **Frequent Sequences**: Common patterns of user interactions
- **Time Patterns**: Hourly and daily activity distributions
- **Workflow Discovery**: Directly-follows relationships and transition probabilities
- **Common Patterns**: Typing sessions, click patterns, keyboard shortcuts

#### Basic Usage

Analyze all collected keyboard and mouse data:
```bash
python memscreen.py --analyze
```

Analyze data within a specific time range:
```bash
python memscreen.py --analyze --start-time "2025-01-01 00:00:00" --end-time "2025-01-02 00:00:00"
```

Export analysis results to JSON:
```bash
python memscreen.py --analyze --export-json process_mining_report.json
```

#### Standalone Process Mining Script

You can also use the process mining module directly:
```bash
python process_mining.py --db ./db/screen_capture.db --start "2025-01-01T00:00:00" --end "2025-01-02T00:00:00" --output report.json
```

#### Analysis Output

The analysis report includes:
- **Summary**: Total events and time range
- **Activity Frequency**: Count of each activity type
- **Frequent Sequences**: Common activity sequences with occurrence counts
- **Time Patterns**: Average durations, hourly/daily distributions
- **Workflow Patterns**: Activity nodes, directly-follows relationships, transition probabilities
- **Common Patterns**: Typing sessions, click patterns, shortcut usage

## Citation

```
@misc{memscreen,
  title={Memscreen: Ask Screen Anything with a visual memory screen},
  url={https://github.com/smileformylove/MemScreen},
}
```

## Thanks

Thanks to the code of [mem0](https://github.com/mem0ai/mem0).

## License

MemScreen is released under the [MIT](https://github.com/smileformylove/MemScreen/blob/master/LICENSE).