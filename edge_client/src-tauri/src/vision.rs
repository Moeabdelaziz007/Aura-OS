// 🖼️ vision_sensor.rs: Zero-Copy Native Screen Capture (V2 - Unblocked)
// Pillar: Peripheral Senses (Eyes)

use scrap::{Display, Capturer};
use std::io::ErrorKind;
use std::time::Duration;
use tokio::time::sleep;
use image::{ImageBuffer, Rgba, codeck::jpeg::JpegEncoder};
use tokio::sync::mpsc;

pub struct VisionSensor {
    capturer: Capturer,
    width: usize,
    height: usize,
}

impl VisionSensor {
    pub fn new() -> Result<Self, String> {
        let display = Display::primary().map_err(|e| e.to_string())?;
        let width = display.width();
        let height = display.height();
        let capturer = Capturer::new(display).map_err(|e| e.to_string())?;
        
        Ok(Self {
            capturer,
            width,
            height,
        })
    }

    /// Primary Sensory Loop with Backpressure Management
    pub async fn start_stream(mut self, tx: mpsc::Sender<Vec<u8>>) {
        loop {
            match self.capturer.frame() {
                Ok(frame) => {
                    // Vision: Direct Buffer Access
                    let frame_data = frame.to_vec(); // Required for thread handover
                    let width = self.width as u32;
                    let height = self.height as u32;
                    let tx_clone = tx.clone();

                    // Priority 2: Offload CPU-heavy JPEG encoding to a blocking thread
                    tokio::task::spawn_blocking(move || {
                        let mut buffer = Vec::new();
                        let mut encoder = JpegEncoder::new_with_quality(&mut buffer, 75);
                        
                        let img_buffer: ImageBuffer<Rgba<u8>, Vec<u8>> = 
                            ImageBuffer::from_raw(width, height, frame_data)
                            .expect("Failed to cast frame to ImageBuffer");

                        if encoder.encode_image(&img_buffer).is_ok() {
                            // Backpressure: If channel is full, drop the frame to keep latency zero.
                            // In tokio mpsc, try_send returns error if full.
                            match tx_clone.try_send(buffer) {
                                Ok(_) => (), 
                                Err(_) => {
                                    // SILENT DROP: The 'Now' is more important than the 'Then'.
                                }
                            }
                        }
                    });

                    // Target ~10 FPS adaptive (AetherCore standard)
                    sleep(Duration::from_millis(100)).await;
                }
                Err(ref e) if e.kind() == ErrorKind::WouldBlock => {
                    sleep(Duration::from_millis(16)).await;
                }
                Err(e) => {
                    eprintln!("⚠️ Vision Sensor Anomaly: {}", e);
                    sleep(Duration::from_secs(2)).await;
                }
            }
        }
    }
}
