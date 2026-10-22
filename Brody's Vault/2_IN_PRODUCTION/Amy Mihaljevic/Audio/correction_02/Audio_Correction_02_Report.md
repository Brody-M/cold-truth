# Amy audio correction 02 — Editor candidate

The correction targets short low-frequency bursts still present in the prior soundtrack, then lowers the entire track by 6 dB. No normalization or makeup gain follows it. This is an unapproved listening candidate; low overall peaks never ruled out the reported P/B thumps.

Detection used the synchronized original provider audio, before the historical high-pass processing. 454 candidate bursts met the numerical thresholds. The method locally reduces a zero-phase low-frequency component below 180 Hz by 12–20 dB with 15 ms attack and 80 ms release. Higher voice content remains in the exact residual. No blanket treble removal, new compression, timing edit, or video render was performed.

Duration is unchanged at 570.560725624 seconds / 25,161,728 samples. Prior soundtrack: -30.89 LUFS, -19.93 dBTP. Correction: -37.14 LUFS, -24.81 dBTP. Integrated loudness changed -6.25 LU; candidate-event 20–110 Hz energy changed a median -14.27 dB beyond the global -6 dB gain. Zero decoded full-scale samples were found.

The 40-second before/after examples both use the actual 300–340 second passage, including strong candidate bursts around 304.70, 312.93, 318.88 and 339.55 seconds. The optional gain-only comparison isolates the difference made by localized processing after matching the requested global -6 dB change.

Numerical detection does not prove every event is a plosive. Low voice fundamentals, onset transitions and other short bass sounds can create false positives. The selective treatment can reduce voice body briefly near such events, so audible success and acceptable tone remain unverified until listening. The prior full-listen decision describes the historical soundtrack and does not approve this correction.

Official references: [iZotope De-plosive documentation](https://downloads.izotope.com/docs/rx6/26-de-plosive/index.html) describes low-frequency plosive energy, processing-frequency limits and the benefit of detecting before high-pass filtering. [iZotope voice-cleanup tutorial](https://www.izotope.com/community/blog/how-to-clean-up-voice-recordings-video-podcasts) explains why indiscriminate low cuts also remove voice body. These references inform this offline method; RX software was not installed or used.
