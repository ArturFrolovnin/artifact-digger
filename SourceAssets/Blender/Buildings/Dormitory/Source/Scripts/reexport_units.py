"""Compatibility entry point: use the existing exporter, including separate doors."""
import bpy
from pathlib import Path
script=Path(bpy.data.filepath).parent/'Scripts/export_fbx.py'
exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'))
