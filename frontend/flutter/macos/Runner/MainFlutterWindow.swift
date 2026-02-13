import Cocoa
import FlutterMacOS

private let flutterWindowReadyNotification = Notification.Name("MemScreenFlutterWindowReady")

class MainFlutterWindow: NSWindow {
    override func awakeFromNib() {
        let flutterViewController = FlutterViewController()
        let windowFrame = self.frame
        self.contentViewController = flutterViewController
        self.setFrame(windowFrame, display: true)
        RegisterGeneratedPlugins(registry: flutterViewController)
        super.awakeFromNib()
        if let appDelegate = NSApp.delegate as? AppDelegate {
            appDelegate.attachMainFlutterWindow(self, controller: flutterViewController)
        }
        NotificationCenter.default.post(
            name: flutterWindowReadyNotification,
            object: self,
            userInfo: ["flutterViewController": flutterViewController]
        )
    }
}
