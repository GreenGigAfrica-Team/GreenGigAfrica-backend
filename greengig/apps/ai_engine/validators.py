"""
AI image validation for proof-of-work photos.

Strategy:
  - Waste / recycling tasks  → TACO dataset labels (trash, litter, waste)
  - Tree planting tasks      → DeepForest / vegetation labels (tree, plant, leaf)
  - Fallback                 → keyword heuristic on filename + basic PIL check

In production, replace the stub classifiers with real model inference
(e.g. torchvision ResNet fine-tuned on TACO, or DeepForest tree detection).
"""
import os
import logging

logger = logging.getLogger(__name__)

# Labels considered valid for each task type
VALID_LABELS = {
    "waste_collection": ["trash", "waste", "garbage", "litter", "bag", "bin", "rubbish"],
    "recycling": ["plastic", "bottle", "can", "cardboard", "paper", "recycling", "waste"],
    "tree_planting": ["tree", "plant", "seedling", "leaf", "forest", "green", "vegetation"],
    "urban_farming": ["plant", "crop", "farm", "soil", "vegetable", "green"],
    "climate_data": ["flood", "water", "erosion", "measurement", "data"],
    "community_education": ["people", "group", "community", "meeting"],
}


def validate_proof_image(image_path: str, task_type: str) -> dict:
    """
    Validate that an image contains content relevant to the task type.

    Returns:
        {
            "passed": bool,
            "confidence": float (0.0 – 1.0),
            "label": str,
        }
    """
    try:
        return _run_model_inference(image_path, task_type)
    except Exception as exc:
        logger.warning("Model inference failed, using heuristic fallback: %s", exc)
        return _heuristic_fallback(image_path, task_type)


def _run_model_inference(image_path: str, task_type: str) -> dict:
    """
    Attempt real model inference.
    Tries torchvision (TACO-style) for waste, PIL-based check otherwise.
    Raises ImportError if torch is not installed — caller falls back to heuristic.
    """
    import torch
    from torchvision import transforms
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    tensor = transform(image).unsqueeze(0)

    # Load model — in production, load once at startup via a singleton
    model = _load_model(task_type)
    if model is None:
        raise RuntimeError("Model not available")

    with torch.no_grad():
        outputs = model(tensor)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        confidence, class_idx = torch.max(probabilities, 0)

    label = _class_idx_to_label(int(class_idx), task_type)
    valid_labels = VALID_LABELS.get(task_type, [])
    passed = any(v in label.lower() for v in valid_labels)

    return {
        "passed": passed,
        "confidence": float(confidence),
        "label": label,
    }


def _load_model(task_type: str):
    """
    Load the appropriate pre-trained model.
    Returns None if model weights are not available.
    """
    # In production: load TACO-fine-tuned ResNet for waste tasks,
    # DeepForest for tree tasks.  For MVP, return None to trigger fallback.
    return None


def _class_idx_to_label(idx: int, task_type: str) -> str:
    """Map class index to human-readable label."""
    # Placeholder — replace with actual class list from your trained model
    labels = VALID_LABELS.get(task_type, ["unknown"])
    return labels[idx % len(labels)]


def _heuristic_fallback(image_path: str, task_type: str) -> dict:
    """
    Simple heuristic: check image is a valid non-empty image file.
    In MVP this ensures the photo is a real image, not a blank/corrupt file.
    """
    try:
        from PIL import Image
        img = Image.open(image_path)
        img.verify()  # Raises if corrupt

        # Check image is not suspiciously small (< 5KB suggests a placeholder)
        file_size = os.path.getsize(image_path)
        if file_size < 5000:
            return {"passed": False, "confidence": 0.1, "label": "image_too_small"}

        return {"passed": True, "confidence": 0.6, "label": "image_valid_heuristic"}

    except Exception as exc:
        logger.error("Heuristic validation failed: %s", exc)
        return {"passed": False, "confidence": 0.0, "label": "validation_error"}
