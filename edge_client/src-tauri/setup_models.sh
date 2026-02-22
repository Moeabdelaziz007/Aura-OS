#!/bin/bash
mkdir -p models
echo "🛰️ AuraOS: Downloading OCR neural models..."
curl -L -o models/text-detection.rten https://huggingface.co/robertknight/ocrs/resolve/main/text-detection.rten
curl -L -o models/text-recognition.rten https://huggingface.co/robertknight/ocrs/resolve/main/text-recognition.rten
echo "✅ Models secured in src-tauri/models/"
