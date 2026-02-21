// 🔌 The Optic Nerve: Rust-Python Synaptic Bridge
// Version: 0.1.1
// Pillar: HyperMind (Perception)

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod vision;
mod audio;

use tauri::{AppHandle, Manager};
use tokio::sync::mpsc;
use futures_util::{StreamExt, SinkExt};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use serde::{Deserialize, Serialize};
use std::time::Duration;

use vision::VisionSensor;
use audio::AudioSensor;

#[derive(Serialize, Deserialize, Debug, Clone)]
struct BrainCommand {
    cmd: String,
    pillar: Option<String>,
    action: Option<String>,
    params: Option<serde_json::Value>,
}

struct SynapticBridge {
    tx: mpsc::UnboundedSender<Message>,
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let (tx, mut rx) = mpsc::unbounded_channel::<Message>();
            let tx_vision = tx.clone();
            let tx_audio = tx.clone();

            // Register Synaptic Bridge State
            app.manage(SynapticBridge { tx });

            let _handle = app.handle().clone();

            // 👁️ Visual Sensory Loop (Unblocked v0.1.1)
            let (vtx, mut vrx) = mpsc::channel::<Vec<u8>>(2); // Backpressure Capacity: 2
            tauri::async_runtime::spawn(async move {
                if let Ok(sensor) = VisionSensor::new() {
                    sensor.start_stream(vtx).await;
                }
            });

            // Pipe vision to WS
            let tx_vision_bridge = tx.clone();
            tauri::async_runtime::spawn(async move {
                while let Some(frame) = vrx.recv().await {
                    let mut payload = vec![0x01]; 
                    payload.extend(frame);
                    let _ = tx_vision_bridge.send(Message::Binary(payload));
                }
            });

            // 👂 Audio Sensory Loop
            let (atx, mut arx) = mpsc::unbounded_channel::<Vec<u8>>();
            let audio_sensor = AudioSensor::new(atx);
            if let Ok(_stream) = audio_sensor.start_capture() {
                tauri::async_runtime::spawn(async move {
                    while let Some(chunk) = arx.recv().await {
                        let mut payload = vec![0x02]; // Header: Audio Chunk
                        payload.extend(chunk);
                        let _ = tx_audio.send(Message::Binary(payload));
                    }
                });
            }

            // 🛰️ Synaptic Bridge (WebSocket Client)
            tauri::async_runtime::spawn(async move {
                let addr = "ws://127.0.0.1:8000";
                println!("🛰️ AuraOS: Establishing Synaptic Bridge to {}...", addr);

                loop {
                    match connect_async(addr).await {
                        Ok((mut ws_stream, _)) => {
                            println!("✅ Synaptic Bridge: ONLINE.");
                            
                            loop {
                                tokio::select! {
                                    // Send messages from Rust to Python
                                    Some(msg) = rx.recv() => {
                                        if let Err(_) = ws_stream.send(msg).await {
                                            break;
                                        }
                                    }
                                    // Receive commands from Python Brain
                                    Some(Ok(msg)) = ws_stream.next() => {
                                        if let Message::Text(text) = msg {
                                            println!("🧠 Brain Command: {}", text);
                                        }
                                    }
                                }
                            }
                        }
                        Err(e) => {
                            eprintln!("❌ Synaptic Bridge: OFFLINE ({}). Retrying in 5s...", e);
                            tokio::time::sleep(Duration::from_secs(5)).await;
                        }
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![stream_sensory_data])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
