import pytest
import json

# Imagine this is a helper function from your app architecture
def calculate_bricks_needed(length: float, width: float, height: float = 2.4) -> int:
    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("Dimensions must be positive values.")
    
    perimeter = 2 * (length + width)
    area = perimeter * height
    base_bricks = area * 60
    total_with_margin = base_bricks * 1.10
    return int(round(total_with_margin))

# --- Your Unit Tests ---

def test_standard_brick_calculation():
    """Test standard room sizing (4m x 5m) yields expected structural counts."""
    # Perimeter = 18m -> Area = 43.2m² -> Base = 2592 -> With 10% Margin = 2851.2
    assert calculate_bricks_needed(4.0, 5.0) == 2851

def test_invalid_dimensions_raise_error():
    """Ensure our calculation boundaries reject nonsensical or negative metrics."""
    with pytest.raises(ValueError):
        calculate_bricks_needed(-4.0, 5.0)