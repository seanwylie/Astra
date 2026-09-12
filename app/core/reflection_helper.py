def handle_reflection(curiosity_level):
    """Dynamically imports and handles reflection processing."""
    from app.core.processing import process_reflection  # ✅ Move import inside function to avoid circular dependency
    print("🧠 Astra is processing a reflection...")
    process_reflection()
