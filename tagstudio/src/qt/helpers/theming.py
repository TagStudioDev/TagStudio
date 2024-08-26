from pathlib import Path

def get_style(style: str) -> str:
    current_file = Path(__file__).resolve()
    return (current_file.parent.parent / "style" / f"{style}.qss").read_text()