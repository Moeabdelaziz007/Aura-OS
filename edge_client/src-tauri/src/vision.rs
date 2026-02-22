use image::{codecs::jpeg::JpegEncoder, ImageBuffer, Rgba};
use lazy_static::lazy_static;
use ocrs::{ImageSource, OcrEngine, OcrEngineParams};
use regex::Regex;
use rten::Model;
use rten_imageproc::BoundingRect;
use scrap::{Capturer, Display};
use std::io::ErrorKind;
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::mpsc;
// removed tokio sleep

pub struct VisionSensor {
    capturer: Capturer,
    width: usize,
    height: usize,
    ocr_engine: Option<Arc<OcrEngine>>,
}

impl VisionSensor {
    pub fn new() -> Result<Self, String> {
        let mut ocr_engine = None;

        // Try to load OCR engine
        let det_model_path = "models/text-detection.rten";
        let rec_model_path = "models/text-recognition.rten";

        if Path::new(det_model_path).exists() && Path::new(rec_model_path).exists() {
            if let Ok(det_model) = Model::load_file(det_model_path) {
                if let Ok(rec_model) = Model::load_file(rec_model_path) {
                    let params = OcrEngineParams {
                        detection_model: Some(det_model),
                        recognition_model: Some(rec_model),
                        ..Default::default()
                    };
                    if let Ok(engine) = OcrEngine::new(params) {
                        ocr_engine = Some(Arc::new(engine));
                        println!("🛡️ Vision Sensor: OCR Engine active.");
                    }
                }
            }
        } else {
            println!("⚠️ Vision Sensor: OCR models missing. Redaction will use static fallback.");
        }

        let display = Display::primary().map_err(|e| e.to_string())?;
        let width = display.width();
        let height = display.height();
        let capturer = Capturer::new(display).map_err(|e| e.to_string())?;

        Ok(Self {
            capturer,
            width,
            height,
            ocr_engine,
        })
    }

    /// Primary Sensory Loop with Backpressure Management
    pub fn start_stream(mut self, tx: mpsc::Sender<Vec<u8>>) {
        let ocr_engine = self.ocr_engine.clone();

        loop {
            match self.capturer.frame() {
                Ok(frame) => {
                    let frame_data = frame.to_vec();
                    let width = self.width as u32;
                    let height = self.height as u32;
                    let tx_clone = tx.clone();
                    let ocr_engine_clone = ocr_engine.clone();

                    std::thread::spawn(move || {
                        let scrubber = ZeroTrustScrubber::new(ocr_engine_clone);
                        let scrubbed_data = scrubber.scrub_pii(&frame_data, width, height);

                        let mut buffer = Vec::new();
                        let mut encoder = JpegEncoder::new_with_quality(&mut buffer, 75);

                        let img_buffer: ImageBuffer<Rgba<u8>, Vec<u8>> =
                            ImageBuffer::from_raw(width, height, scrubbed_data)
                                .expect("Failed to cast frame to ImageBuffer");

                        if encoder.encode_image(&img_buffer).is_ok() {
                            let metadata = b"{\"nodes\": []}";

                            let mut packet = Vec::new();
                            packet.extend_from_slice(&(metadata.len() as u32).to_le_bytes());
                            packet.extend_from_slice(metadata);
                            packet.extend_from_slice(&buffer);

                            let _ = tx_clone.blocking_send(packet);
                        }
                    });

                    std::thread::sleep(Duration::from_millis(100));
                }
                Err(ref e) if e.kind() == ErrorKind::WouldBlock => {
                    std::thread::sleep(Duration::from_millis(16));
                }
                Err(e) => {
                    eprintln!("⚠️ Vision Sensor Anomaly: {}", e);
                    std::thread::sleep(Duration::from_secs(2));
                }
            }
        }
    }
}

/// REVERSE ENG #1: TinyML Privacy Scrubbing Engine
struct ZeroTrustScrubber {
    // Regex patterns for PII detection
    credit_card_pattern: Regex,
    email_pattern: Regex,
    password_field_pattern: Regex,
    ocr_engine: Option<Arc<OcrEngine>>,
}

lazy_static! {
    // Credit card pattern: Matches common credit card formats (Visa, MasterCard, Amex, etc.)
    static ref CREDIT_CARD_RE: Regex = Regex::new(
        r"\b(?:\d[ -]*?){13,16}\b"
    ).expect("Invalid credit card regex");

    // Email pattern: Matches standard email formats
    static ref EMAIL_RE: Regex = Regex::new(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ).expect("Invalid email regex");

    // Password field pattern: Detects common password field indicators in UI
    static ref PASSWORD_FIELD_RE: Regex = Regex::new(
        r"(?i)(password|passwd|pwd|pass|secret|pin)\s*[:=]"
    ).expect("Invalid password field regex");
}

impl ZeroTrustScrubber {
    fn new(ocr_engine: Option<Arc<OcrEngine>>) -> Self {
        Self {
            credit_card_pattern: CREDIT_CARD_RE.clone(),
            email_pattern: EMAIL_RE.clone(),
            password_field_pattern: PASSWORD_FIELD_RE.clone(),
            ocr_engine,
        }
    }

    /// Redacts sensitive UI areas (Passwords, Credit Cards, Emails) at the Edge
    ///
    /// Args:
    ///     data: Raw RGBA frame data
    ///     w: Width of the frame
    ///     h: Height of the frame
    ///
    /// Returns:
    ///     Scrubbed RGBA frame data with sensitive regions redacted
    fn scrub_pii(&self, data: &[u8], w: u32, h: u32) -> Vec<u8> {
        let mut scrubbed_data = data.to_vec();

        if let Some(engine) = &self.ocr_engine {
            // Prepare image for OCR
            let img_buffer: ImageBuffer<Rgba<u8>, &[u8]> =
                ImageBuffer::from_raw(w, h, data).expect("Failed to cast data");

            // Convert to Greyscale for ocrs
            let grey_img = image::ImageBuffer::from_fn(w, h, |x, y| {
                let pixel = img_buffer.get_pixel(x, y);
                // Standard luma transform
                let luma = (0.299 * pixel[0] as f32
                    + 0.587 * pixel[1] as f32
                    + 0.114 * pixel[2] as f32) as u8;
                image::Luma([luma])
            });

            let ocrs_img =
                ImageSource::from_bytes(grey_img.as_raw(), (grey_img.width(), grey_img.height()))
                    .expect("Invalid image source");

            if let Ok(ocr_input) = engine.prepare_input(ocrs_img) {
                // 1. Detect Words (Layout)
                if let Ok(words) = engine.detect_words(&ocr_input) {
                    // 2. Recognize Content (Batch-oriented API)
                    if let Ok(recognized_batches) =
                        engine.recognize_text(&ocr_input, &[words.clone()])
                    {
                        if let Some(recognized_words) = recognized_batches.first() {
                            for (rect, recognized) in words.iter().zip(recognized_words.iter()) {
                                let text = recognized.to_string();

                                // Check if word contains PII
                                if self.credit_card_pattern.is_match(&text)
                                    || self.email_pattern.is_match(&text)
                                    || self.password_field_pattern.is_match(&text)
                                {
                                    // Redact the word's bounding box
                                    let bbox = rect.bounding_rect();
                                    self.redact_rect(
                                        &mut scrubbed_data,
                                        w,
                                        h,
                                        bbox.top() as i32,
                                        bbox.left() as i32,
                                        bbox.width() as u32,
                                        bbox.height() as u32,
                                    );
                                }
                            }
                        }
                    }
                }
            }
        } else {
            // Fallback: Redact known sensitive areas if OCR engine is missing
            self.redact_rect(
                &mut scrubbed_data,
                w,
                h,
                (h as i32 - 100).max(0),
                (w as i32 - 400).max(0),
                400,
                100,
            );
        }

        scrubbed_data
    }

    fn redact_rect(
        &self,
        data: &mut [u8],
        w: u32,
        h: u32,
        top: i32,
        left: i32,
        width: u32,
        height: u32,
    ) {
        let bytes_per_pixel = 4;
        let end_y = (top + height as i32).min(h as i32);
        let end_x = (left + width as i32).min(w as i32);

        for y in top.max(0)..end_y {
            for x in left.max(0)..end_x {
                let pixel_offset = (y as usize * w as usize + x as usize) * bytes_per_pixel;
                if pixel_offset + bytes_per_pixel <= data.len() {
                    data[pixel_offset] = 0;
                    data[pixel_offset + 1] = 0;
                    data[pixel_offset + 2] = 0;
                    data[pixel_offset + 3] = 255;
                }
            }
        }
    }
}
