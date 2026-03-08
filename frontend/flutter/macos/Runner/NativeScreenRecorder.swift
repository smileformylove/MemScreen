import AppKit
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
    private var requestedDuration: Int = 9999
    private var requestedInterval: Double = 2.0
    var onRecordingFinished: (([String: Any]) -> Void)?

    func start(arguments: [String: Any]) -> [String: Any] {
        if let process, process.isRunning {
            return ["ok": false, "error": "Native recording is already running"]
        }

        let requestedMode = (arguments["mode"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        mode = requestedMode?.isEmpty == false ? requestedMode! : "fullscreen"
        region = arguments["region"] as? [Double]
        screenIndex = Self.parseInt(arguments["screenIndex"])
        if screenIndex == nil {
            screenIndex = Self.parseInt(arguments["screen_index"])
        }
        screenDisplayId = Self.parseInt(arguments["screenDisplayId"])
        if screenDisplayId == nil {
            screenDisplayId = Self.parseInt(arguments["screen_display_id"])
        }
        requestedDuration = Self.parseInt(arguments["duration"]) ?? 9999
        requestedInterval = Self.parseDouble(arguments["interval"]) ?? 2.0

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

        if requestedDuration > 0 && requestedDuration < 36000 {
            args.append("-V\(requestedDuration)")
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
        process.terminationHandler = { [weak self, weak process] _ in
            guard let self, let process, self.process === process else { return }
            let result = self.finishRecording(consumedByCallback: true)
            DispatchQueue.main.async {
                self.onRecordingFinished?(result)
            }
        }

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

        process.terminationHandler = nil
        if process.isRunning {
            process.interrupt()
            process.waitUntilExit()
        }

        return finishRecording(consumedByCallback: false)
    }

    func consumeFinishedRecordingIfNeeded() -> [String: Any] {
        guard let process else {
            return ["ok": false, "consumed": false]
        }
        guard !process.isRunning else {
            return ["ok": false, "consumed": false]
        }
        var result = finishRecording(consumedByCallback: false)
        result["consumed"] = true
        return result
    }

    private func finishRecording(consumedByCallback: Bool) -> [String: Any] {
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
            "consumedByCallback": consumedByCallback,
        ]
    }

    func status() -> [String: Any] {
        let isRecording = process?.isRunning == true
        let elapsed = startedAt.map { Date().timeIntervalSince($0) } ?? 0
        return [
            "isRecording": isRecording,
            "duration": requestedDuration,
            "interval": requestedInterval,
            "outputDir": Self.outputDirectory().path,
            "frameCount": 0,
            "elapsedTime": elapsed,
            "mode": mode,
            "region": region as Any,
            "screenIndex": screenIndex as Any,
            "screenDisplayId": screenDisplayId as Any,
        ]
    }

    func screens() -> [[String: Any]] {
        let allScreens = NSScreen.screens
        let mainDisplayID = Self.displayID(for: NSScreen.main)
        return allScreens.enumerated().map { index, screen in
            let frame = screen.frame
            let displayID = Self.displayID(for: screen)
            return [
                "index": index,
                "name": screen.localizedName,
                "width": Int(frame.width),
                "height": Int(frame.height),
                "is_primary": displayID != nil && displayID == mainDisplayID,
                "display_id": displayID as Any,
            ]
        }
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

    private static func parseInt(_ value: Any?) -> Int? {
        if let intValue = value as? Int {
            return intValue
        }
        if let number = value as? NSNumber {
            return number.intValue
        }
        return nil
    }

    private static func parseDouble(_ value: Any?) -> Double? {
        if let doubleValue = value as? Double {
            return doubleValue
        }
        if let number = value as? NSNumber {
            return number.doubleValue
        }
        return nil
    }

    private static func displayID(for screen: NSScreen?) -> Int? {
        guard let screen,
              let raw = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else {
            return nil
        }
        return raw.intValue
    }
}
