"""
Convert HuggingFace embedding model to OpenVINO IR format
This only needs to be run once to prepare the model
"""
import torch
from transformers import AutoModel, AutoTokenizer
import openvino as ov
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_embedding_model(
    model_name: str = "mixedbread-ai/mxbai-embed-large-v1",
    output_dir: str = "./models/mxbai-embed-large-ov"
):
    """
    Convert embedding model to OpenVINO IR format

    Args:
        model_name: HuggingFace model name
        output_dir: Directory to save OpenVINO model
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading model: {model_name}")

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    logger.info("Model loaded successfully")

    # Create dummy inputs for tracing
    dummy_text = "This is a sample text for model conversion"
    inputs = tokenizer(
        dummy_text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )

    logger.info("Creating dummy inputs for model export")

    # Prepare input shapes for OpenVINO
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # Export to ONNX first (intermediate step)
    onnx_path = output_path / "model.onnx"

    logger.info(f"Exporting to ONNX: {onnx_path}")

    torch.onnx.export(
        model,
        (input_ids, attention_mask),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "last_hidden_state": {0: "batch_size", 1: "sequence_length"}
        },
        opset_version=14
    )

    logger.info("ONNX export complete")

    # Convert ONNX to OpenVINO IR
    logger.info("Converting ONNX to OpenVINO IR format...")

    ov_model = ov.convert_model(str(onnx_path))

    # Save OpenVINO model
    ir_path = output_path / "model.xml"
    ov.save_model(ov_model, str(ir_path))

    logger.info(f"✅ OpenVINO model saved to: {ir_path}")

    # Save tokenizer
    tokenizer.save_pretrained(output_path)
    logger.info(f"✅ Tokenizer saved to: {output_path}")

    # Clean up ONNX file (optional)
    # onnx_path.unlink()

    logger.info("=" * 50)
    logger.info("Conversion complete!")
    logger.info(f"Model path: {ir_path}")
    logger.info("=" * 50)

    return str(ir_path)


if __name__ == "__main__":
    import sys

    model_name = "mixedbread-ai/mxbai-embed-large-v1"
    output_dir = "./models/mxbai-embed-large-ov"

    if len(sys.argv) > 1:
        model_name = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    print(f"Converting {model_name} to OpenVINO format...")
    print(f"Output directory: {output_dir}")
    print()

    try:
        model_path = convert_embedding_model(model_name, output_dir)
        print(f"\n✅ Success! Use this path in your service:")
        print(f"   {model_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
