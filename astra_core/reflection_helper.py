def handle_reflection():
    """Dynamically imports and handles reflection processing."""
    from astra_core.processing import process_reflection  # ✅ Move import inside function to avoid circular dependency
    print("🧠 Astra is processing a reflection...")
    process_reflection()
