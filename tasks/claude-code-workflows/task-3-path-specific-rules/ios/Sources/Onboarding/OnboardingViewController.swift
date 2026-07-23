import UIKit

final class OnboardingViewController: UIViewController {
    @IBOutlet weak var titleLabel: UILabel!
    @IBOutlet weak var subtitleLabel: UILabel!
    @IBOutlet weak var skipButton: UIButton!

    override func viewDidLoad() {
        super.viewDidLoad()
        titleLabel.text = NSLocalizedString("onboarding_welcome_title", comment: "")
        subtitleLabel.text = NSLocalizedString("onboarding_welcome_subtitle", comment: "")
        skipButton.setTitle(NSLocalizedString("SkipButton", comment: ""), for: .normal)
    }
}
