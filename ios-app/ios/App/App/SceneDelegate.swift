import UIKit
import Capacitor

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        guard let windowScene = scene as? UIWindowScene else { return }

        window = UIWindow(windowScene: windowScene)
        window?.rootViewController = MainViewController()
        window?.makeKeyAndVisible()

        SceneDelegateProxy.shared.scene(scene, willConnectTo: session, options: connectionOptions)
    }

    func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
        SceneDelegateProxy.shared.scene(scene, openURLContexts: URLContexts)
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
        SceneDelegateProxy.shared.scene(scene, continue: userActivity)
    }
}

// TermChamp (2026-10-28): the web view's own surface. The app scrolls inside its page, so the web view
// itself is pinned (capacitor.config.json ios.scrollEnabled false). Two things still showed through at
// the top: iOS 26's scroll-edge blur under the clock, and the web view's fixed light background in
// dark mode — together a white haze over a dark screen. Hide the edge effects and give the web view
// the page's own colour for the phone's light/dark setting.
class MainViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        guard let wv = webView else { return }
        let bg = UIColor { t in
            t.userInterfaceStyle == .dark
                ? UIColor(red: 10 / 255, green: 15 / 255, blue: 28 / 255, alpha: 1)
                : UIColor(red: 244 / 255, green: 246 / 255, blue: 251 / 255, alpha: 1)
        }
        view.backgroundColor = bg
        wv.isOpaque = false
        wv.backgroundColor = bg
        wv.scrollView.backgroundColor = bg
        #if compiler(>=6.2)
        if #available(iOS 26.0, *) {
            wv.scrollView.topEdgeEffect.isHidden = true
            wv.scrollView.bottomEdgeEffect.isHidden = true
        }
        #endif
    }
}
