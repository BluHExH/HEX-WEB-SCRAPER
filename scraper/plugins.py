"""
Plugin architecture for HEX Web Scraper
"""

from typing import Any, Callable, Dict

from .logger import get_logger

logger = get_logger(__name__)

# Registry for transformation functions
TRANSFORMERS = {}


def register_transformer(name: str):
    """Decorator to register a transformer function"""

    def decorator(func: Callable):
        TRANSFORMERS[name] = func
        return func

    return decorator


@register_transformer("price_to_float")
def price_to_float(value: str) -> float:
    """Convert price string to float"""
    if not value:
        return 0.0

    # Remove currency symbols and commas
    cleaned = value.replace("$", "").replace("€", "").replace("£", "").replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not convert '{value}' to float")
        return 0.0


@register_transformer("date_parser")
def date_parser(value: str) -> str:
    """Parse date string to standardized format"""
    # This is a simplified implementation
    # In a real-world scenario, you would use a library like dateutil
    return value.strip()


@register_transformer("normalize_text")
def normalize_text(value: str) -> str:
    """Normalize text by removing extra whitespace and converting to title case"""
    if not value:
        return ""

    return " ".join(value.split()).title()


class PluginManager:
    """Manage plugins and transformations"""

    def __init__(self):
        self.transformers = TRANSFORMERS

    def apply_transformations(
        self, data: Dict[str, Any], transformations: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply transformations to data fields"""
        transformed_data = data.copy()

        for field, transformer_name in transformations.items():
            if field in transformed_data and transformer_name in self.transformers:
                try:
                    transformed_data[field] = self.transformers[transformer_name](
                        transformed_data[field]
                    )
                except Exception as e:
                    logger.error(
                        f"Error applying transformation '{transformer_name}' to field '{field}': {e}"
                    )

        return transformed_data
