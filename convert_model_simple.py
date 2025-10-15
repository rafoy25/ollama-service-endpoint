"""
Simplified model conversion using optimum-intel
"""
import sys
import os

# Set UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Disable HF symlink warnings
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from pathlib import Path
from transformers import AutoTokenizer, AutoModel
import torch
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def convert_model(model_name="mixedbread-ai/mxbai-embed-large-v1", output_dir="./models/mxbai-embed-large-ov"):
    """Convert HF model to OpenVINO using simple ONNX export"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading model: {model_name}")

    # Download model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, torchscript=True)
    model.eval()

    logger.info("Model loaded successfully")

    # Save tokenizer
    tokenizer.save_pretrained(output_path)
    logger.info(f"Tokenizer saved to {output_path}")

    # Create example input
    dummy_text = "This is a sample sentence for model conversion"
    inputs = tokenizer(dummy_text, return_tensors="pt", padding=True, truncation=True, max_length=512)

    logger.info("Creating traced model...")

    # Trace the model
    with torch.no_grad():
        traced_model = torch.jit.trace(model, (inputs['input_ids'], inputs['attention_mask']))

    # Save traced model
    traced_path = output_path / "traced_model.pt"
    torch.jit.save(traced_model, str(traced_path))
    logger.info(f"Traced model saved to {traced_path}")

    # Now convert to OpenVINO using mo command
    logger.info("Converting to OpenVINO IR format...")

    import openvino as ov

    # Convert directly from PyTorch model
    ov_model = ov.convert_model(traced_model, example_input=(inputs['input_ids'], inputs['attention_mask']))

    # Save
    ir_path = output_path / "model.xml"
    ov.save_model(ov_model, str(ir_path), compress_to_fp16=False)

    logger.info(f"SUCCESS! Model saved to: {ir_path}")
    logger.info(f"Tokenizer saved to: {output_path}")

    return str(ir_path)


if __name__ == "__main__":
    try:
        model_path = convert_model()
        print(f"\nConversion complete! Model path: {model_path}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
