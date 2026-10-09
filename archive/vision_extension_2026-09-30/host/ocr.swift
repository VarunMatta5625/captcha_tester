import Foundation
import Vision
import AppKit

// Apple Vision OCR, accurate mode, no language correction (captchas are random strings).
// Usage: ./ocr img1.png img2.png ...  -> prints "path<TAB>text" per image (spaces removed)
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("\(path)\t"); continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg).perform([req])
    let text = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined()
    print("\(path)\t\(text.replacingOccurrences(of: " ", with: ""))")
}
