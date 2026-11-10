"""Run in the current Unreal Editor: reimport Library and import only its Parts."""
import unreal,json
from pathlib import Path
project=Path(unreal.Paths.project_dir()).resolve()
source=project/'SourceAssets/Blender/Buildings/Library/Source'
IMPORT_CONFIG=json.loads((source/'model_config.json').read_text(encoding='utf-8'))
script=source.parent.parent/'RudyPawnshop/Source/finish_ue_import.py'
exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'))
