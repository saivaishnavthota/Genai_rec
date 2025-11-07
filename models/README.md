# Mistral-7B Model Setup

## Download Instructions

To use Mistral-7B-Instruct with this application, you need to download the GGUF model file:

### 1. Download the Model

Visit: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF

Download: **`mistral-7b-instruct-v0.2.Q4_K_M.gguf`** (approximately 4.37 GB)

### 2. Place the Model

Put the downloaded file in this directory:
```
GENAI-main/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

### 3. Verify Setup

The application will automatically detect the model and switch from fallback mode to full Mistral-7B generation.

## Model Details

- **Model**: Mistral-7B-Instruct-v0.2
- **Quantization**: Q4_K_M (4-bit quantization, medium quality)
- **Size**: ~4.37 GB
- **Performance**: 5-15 tokens/sec on modern 8-core CPU
- **Memory**: ~6 GB RAM required

## Alternative Models

If you prefer a different quantization level:

- **Q4_K_S**: Smaller, faster, slightly lower quality (~3.8 GB)
- **Q5_K_M**: Larger, slower, higher quality (~5.1 GB)
- **Q8_0**: Largest, slowest, highest quality (~7.2 GB)

Update the `mistral_model_path` in `backend/app/config.py` if using a different file.

## Troubleshooting

If the model doesn't load:
1. Check file path and name match exactly
2. Ensure sufficient RAM (6+ GB free)
3. Verify file isn't corrupted (re-download if needed)
4. Check logs for specific error messages

The application will run in fallback mode with predefined responses if the model isn't available.
