"""
Convert embedding model to OpenVINO with STATIC shapes for NPU compatibility
NPU requires fixed input dimensions (no dynamic shapes)
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
import openvino as ov
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def convert_model_static(
    model_name="mixedbread-ai/mxbai-embed-large-v1",
    output_dir="./models/mxbai-embed-large-ov-npu",
    max_seq_length=512,
    batch_size=1
):
    """
    Convert model with STATIC shapes for NPU compatibility

    Args:
        model_name: HuggingFace model name
        output_dir: Output directory for OpenVINO model
        max_seq_length: Fixed sequence length (default: 512)
        batch_size: Fixed batch size (default: 1)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting model with STATIC shapes for NPU")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Max sequence length: {max_seq_length}")

    # Load model and tokenizer
    logger.info("Downloading model from HuggingFace...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    # Save tokenizer
    tokenizer.save_pretrained(output_path)
    logger.info(f"Tokenizer saved to {output_path}")

    # Create example input with FIXED shapes
    logger.info(f"Creating static shape inputs [{batch_size}, {max_seq_length}]...")

    # Create fixed-size dummy inputs
    input_ids = torch.zeros((batch_size, max_seq_length), dtype=torch.long)
    attention_mask = torch.ones((batch_size, max_seq_length), dtype=torch.long)

    logger.info("Tracing model with static shapes...")
    with torch.no_grad():
        # Trace with fixed shapes (no dynamic axes)
        traced_model = torch.jit.trace(
            model,
            (input_ids, attention_mask),
            strict=False
        )

    # Save traced model
    traced_path = output_path / "traced_model_static.pt"
    torch.jit.save(traced_model, str(traced_path))
    logger.info(f"Traced model saved to {traced_path}")

    # Convert to OpenVINO with STATIC shapes
    logger.info("Converting to OpenVINO IR format (static shapes)...")

    # Convert with explicit static shapes
    ov_model = ov.convert_model(
        traced_model,
        example_input=(input_ids, attention_mask),
        input=[
            (batch_size, max_seq_length),  # input_ids shape
            (batch_size, max_seq_length)   # attention_mask shape
        ]
    )

    # Save OpenVINO model
    ir_path = output_path / "model.xml"
    ov.save_model(ov_model, str(ir_path), compress_to_fp16=False)

    logger.info(f"SUCCESS! OpenVINO model saved to: {ir_path}")
    logger.info(f"Model configuration:")
    logger.info(f"  - Static batch size: {batch_size}")
    logger.info(f"  - Static sequence length: {max_seq_length}")
    logger.info(f"  - NPU compatible: YES")

    # Verify model shapes
    logger.info("\nVerifying model inputs:")
    core = ov.Core()
    model_ir = core.read_model(str(ir_path))

    for input_layer in model_ir.inputs:
        logger.info(f"  Input: {input_layer.any_name}")
        logger.info(f"    Shape: {input_layer.shape}")
        logger.info(f"    Type: {input_layer.element_type}")

    return str(ir_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert model for NPU with static shapes")
    parser.add_argument("--model", default="mixedbread-ai/mxbai-embed-large-v1", help="HuggingFace model name")
    parser.add_argument("--output", default="./models/mxbai-embed-large-ov-npu", help="Output directory")
    parser.add_argument("--max-length", type=int, default=512, help="Max sequence length (static)")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size (static)")

    args = parser.parse_args()

    print(f"\nConverting {args.model} to OpenVINO (NPU-compatible)...")
    print(f"Output directory: {args.output}")
    print(f"Static shapes: batch_size={args.batch_size}, max_length={args.max_length}\n")

    try:
        model_path = convert_model_static(
            model_name=args.model,
            output_dir=args.output,
            max_seq_length=args.max_length,
            batch_size=args.batch_size
        )
        print(f"\nConversion complete! Model path: {model_path}")
        print("\nNOTE: This model has STATIC shapes and will:")
        print("  - Work on NPU (static shapes required)")
        print("  - Pad/truncate all inputs to max_length=512")
        print("  - Process one embedding at a time (batch_size=1)")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
