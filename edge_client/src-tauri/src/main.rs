// 🔌 The Optic Nerve: Rust-Python Synaptic Bridge
// Version: 0.1.1
// Pillar: HyperMind (Perception)

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod vision;
mod audio;
mod action;

use tauri::{AppHandle, Manager};
use tokio::sync::mpsc;
use futures_util::{StreamExt, SinkExt};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use serde::{Deserialize, Serialize};
use std::time::Duration;

use vision::VisionSensor;
use audio::AudioSensor;
use action::{ActionExecutor, UIAction};

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

#[tauri::command]
async fn stream_sensory_data(
    _app: AppHandle,
    state: tauri::State<'_, SynapticBridge>,
    command: BrainCommand,
) -> Result<(), String> {
    let payload = serde_json::to_string(&command).map_err(|e| e.to_string())?;
    state.tx.send(Message::Text(payload)).map_err(|e| e.to_string())?;
    Ok(())
}

fn get_bridge_url() -> String {
    std::env::var("AURA_BRIDGE_URL").unwrap_or_else(|_| {
        println!("⚠️ Warning: AURA_BRIDGE_URL not set. Defaulting to insecure localhost.");
        "ws://127.0.0.1:8000".to_string()
    })
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
            std::thread::spawn(move || {
                if let Ok(sensor) = VisionSensor::new() {
                    sensor.start_stream(vtx);
                }
            });

            // Pipe vision to WS
            let tx_vision_bridge = tx_vision.clone();
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
                let addr = get_bridge_url();
                println!("🛰️ AuraOS: Establishing Synaptic Bridge to {}...", addr);

                loop {
                    match connect_async(&addr).await {
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
                                            // Handle UI action execution
                                            if let Ok(ui_action) = serde_json::from_str::<UIAction>(&text) {
                                                // Execute UI actions on a blocking thread to avoid blocking the async loop
                                                tokio::task::spawn_blocking(move || {
                                                    ActionExecutor::execute(&ui_action);
                                                });
                                            }
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    static ENV_LOCK: Mutex<()> = Mutex::new(());

    #[test]
    fn test_get_bridge_url_default() {
        let _lock = ENV_LOCK.lock().unwrap();

        let original = std::env::var("AURA_BRIDGE_URL");
        std::env::remove_var("AURA_BRIDGE_URL");
        assert_eq!(get_bridge_url(), "ws://127.0.0.1:8000");

        if let Ok(val) = original {
            std::env::set_var("AURA_BRIDGE_URL", val);
        }
    }

    #[test]
    fn test_get_bridge_url_env_set() {
        let _lock = ENV_LOCK.lock().unwrap();

        let original = std::env::var("AURA_BRIDGE_URL");
        std::env::set_var("AURA_BRIDGE_URL", "wss://example.com:9000");
        assert_eq!(get_bridge_url(), "wss://example.com:9000");

        if let Ok(val) = original {
            std::env::set_var("AURA_BRIDGE_URL", val);
        } else {
            std::env::remove_var("AURA_BRIDGE_URL");
        }
    }
}
