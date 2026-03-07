import Foundation

final class NativeScreenRecorder {
    private var process: Process?
    private var outputURL: URL?
    private var startedAt: Date?
    private var mode: String = "fullscreen"
    private var region: [Double]?
    private var screenIndex: Int?
    private var screenDisplayId: Int?
    private var audioSourceUsed: String = "none"
    private var notice: String?

    func start(arguments: [String: Any]) -> [String: Any] {
        if let process, process.isRunning {
            return ["ok": false, "error": "Native recording is already running"]
        }

        let requestedMode = (arguments["mode"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        mode = requestedMode?.isEmpty == false ? requestedMode! : "fullscreen"
        region = arguments["region"] as? [Double]
        screenIndex = arguments["screenIndex"] as? Int
        if screenIndex == nil, let number = arguments["screenIndex"] as? NSNumber {
            screenIndex = number.intValue
        }
        screenDisplayId = arguments["screenDisplayId"] as? Int
        if screenDisplayId == nil, let number = arguments["screenDisplayId"] as? NSNumber {
            screenDisplayId = number.intValue
        }

        let requestedAudio = ((arguments["audioSource"] as? String) ?? "none").lowercased()
        var args = ["-x", "-v"]
        audioSourceUsed = "none"
        notice = nil

        if requestedAudio == "microphone" || requestedAudio == "mixed" {
            args.append("-g")
            audioSourceUsed = "microphone"
            if requestedAudio == "mixed" {
                notice = "Native macOS recording currently captures microphone audio only. System audio was not included."
            }
        } else if requestedAudio == "system_audio" {
            notice = "Native macOS recording currently does not capture system audio. Recording continues without system audio."
        }

        if mode == "fullscreen-single", let screenIndex {
            args.append("-D\(screenIndex + 1)")
        } else if mode == "region", let region, region.count == 4 {
            let left = Int(region[0])
            let top = Int(region[1])
            let width = max(1, Int(region[2] - region[0]))
            let height = max(1, Int(region[3] - region[1]))
            args.append("-R\(left),\(top),\(width),\(height)")
        }

        let outputURL = Self.makeOutputURL()
        self.outputURL = outputURL
        args.append(outputURL.path)

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
        process.arguments = args

        do {
            try FileManager.default.createDirectory(
                at: outputURL.deletingLastPathComponent(),
                withIntermediateDirectories: true
            )
            try process.run()
            self.process = process
            self.startedAt = Date()
            return [
                "ok": true,
                "filename": outputURL.path,
                "mode": mode,
                "audioSourceUsed": audioSourceUsed,
                "notice": notice as Any,
            ]
        } catch {
            self.process = nil
            self.outputURL = nil
            self.startedAt = nil
            return ["ok": false, "error": "Failed to start native recording: \(error.localizedDescription)"]
        }
    }

    func stop() -> [String: Any] {
        guard let process else {
            return ["ok": false, "error": "Native recording is not running"]
        }

        if process.isRunning {
            process.interrupt()
            process.waitUntilExit()
        }

        let duration = startedAt.map { Date().timeIntervalSince($0) } ?? 0
        let filename = outputURL?.path
        self.process = nil
        self.outputURL = nil
        self.startedAt = nil

        return [
            "ok": true,
            "filename": filename as Any,
            "durationSec": duration,
            "mode": mode,
            "audioSourceUsed": audioSourceUsed,
            "notice": notice as Any,
        ]
    }

    func status() -> [String: Any] {
        let isRecording = process?.isRunning == true
        let elapsed = startedAt.map { Date().timeIntervalSince($0) } ?? 0
        return [
            "isRecording": isRecording,
            "duration": 9999,
            "interval": 2.0,
            "outputDir": Self.outputDirectory().path,
            "frameCount": 0,
            "elapsedTime": elapsed,
            "mode": mode,
            "region": region as Any,
            "screenIndex": screenIndex as Any,
            "screenDisplayId": screenDisplayId as Any,
        ]
    }

    private static func outputDirectory() -> URL {
        URL(fileURLWithPath: NSHomeDirectory())
            .appendingPathComponent(".memscreen", isDirectory: true)
            .appendingPathComponent("videos", isDirectory: true)
    }

    private static func makeOutputURL() -> URL {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        let name = "native_\(formatter.string(from: Date())).mov"
        return outputDirectory().appendingPathComponent(name)
    }
}
