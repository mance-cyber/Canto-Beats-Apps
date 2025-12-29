
import torch
import logging
import sys

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_load_vad():
    print("Testing Silero VAD model loading...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    try:
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        print("Successfully loaded model from hub.")
        
        print("Unpacking utils...")
        (get_speech_timestamps,
         save_audio,
         read_audio,
         VADIterator,
         collect_chunks) = utils
        print("Utils unpacked.")

        print(f"Moving model to {device}...")
        model = model.to(device)
        print("Model moved to device.")
        
        print("ALL SUCCESS!")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_load_vad()
