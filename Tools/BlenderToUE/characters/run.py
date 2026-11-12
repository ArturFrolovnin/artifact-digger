"""Run in the already open Unreal editor console (Cmd mode), e.g. py ".../run.py" --npc EllieRowan."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from common import load_config, require, write_json, digest, file_hash


def blender_call(cfg, reference, export):
    # Reuse the installed Blender MCP client's connection helper and configured port.
    # This does not create another MCP server or launch a Blender process.
    import tomllib
    settings=tomllib.loads((Path(cfg['project'])/'.codex/config.toml').read_text(encoding='utf-8-sig'))['mcp_servers']['blender']
    args=settings['args']
    directory=Path(args[args.index('--directory')+1])
    # Loading the helper directly avoids importing the MCP server package and
    # its unrelated yaml/server dependencies into Unreal's Python interpreter.
    import importlib.util
    helper=directory/'blmcp/tools_helpers/connection.py'
    require(helper.is_file(),'Installed Blender MCP connection helper not found: '+str(helper))
    spec=importlib.util.spec_from_file_location('_character_blender_connection',helper)
    connection=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(connection)
    send_code=connection.send_code
    env=settings.get('env',{})
    saved={k:os.environ.get(k) for k in ('BLENDER_MCP_HOST','BLENDER_MCP_PORT')}
    try:
        for k in saved:
            if k in env:os.environ[k]=env[k]
        code=("import sys,importlib,json\n"
              "sys.path.insert(0,%r)\nimport blender_export\nimportlib.reload(blender_export)\n"
              "result=blender_export.execute(json.loads(%r),json.loads(%r),export=%r)" %
              (str(HERE),json.dumps(cfg),json.dumps(reference),export))
        response=send_code(code,strict_json=True)
        require(response.get('status')=='ok',response.get('message','Blender execution failed'))
        return response['result']
    finally:
        for k,v in saved.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v


def run(npc,mode='all'):
    import unreal
    import importlib
    import unreal_import
    importlib.reload(unreal_import)
    cfg=load_config(npc,unreal.Paths.project_dir())
    log=Path(cfg['log_dir']);log.mkdir(parents=True,exist_ok=True)
    report={'npc':npc,'mode':mode,'asset':cfg['unreal_asset'],'status':'RUNNING'}
    try:
        reference=unreal_import.discover_reference(cfg)
        if mode=='all':
            live=blender_call(cfg,reference,export=False)
            cached=json.loads((log/'export.json').read_text(encoding='utf-8')) if (log/'export.json').is_file() else {}
            current=(cached.get('scene_hash')==live['scene_hash'] and cached.get('config_hash')==digest(cfg)
                     and cached.get('reference_hash')==reference['skeleton_hash'] and Path(cfg['fbx']).is_file()
                     and cached.get('fbx_sha256')==file_hash(cfg['fbx']))
            exported=cached if current else blender_call(cfg,reference,export=True)
            report['export_skipped']=current
        else:
            exported=blender_call(cfg,reference,export=mode!='validate')
        report['blender']=exported
        if mode in ('all','reimport'):
            previous=json.loads((log/'import.json').read_text(encoding='utf-8')) if (log/'import.json').is_file() else {}
            target=cfg['unreal_asset']
            exists=unreal.EditorAssetLibrary.does_asset_exist(target)
            mesh=unreal.load_asset(target) if exists else None
            require(target not in unreal_import.dirty_content(),'Target has unsaved changes; refusing import/skip')
            unchanged=(mode=='all' and exists and previous.get('fbx_sha256')==exported['fbx_sha256']
                       and previous.get('scene_hash')==exported['scene_hash'] and previous.get('config_hash')==digest(cfg)
                       and previous.get('skeleton_hash')==reference['skeleton_hash']
                       and previous.get('asset_file_hash')==unreal_import.package_hash(mesh))
            if unchanged:
                report['unreal']=unreal_import.validate_mesh(cfg,mesh,reference,exported)
                report['unreal'].update(status='SKIPPED',operation='UNCHANGED',changed_assets=[],skeleton_unchanged=True,maps_unchanged=True)
            else:
                report['unreal']=unreal_import.execute(cfg,reference,exported,require_existing=mode=='reimport')
        report['status']='SUCCESS'
        write_json(log/'result.json',report)
        (log/'error.txt').unlink(missing_ok=True)
        unreal.log('CHARACTER_PIPELINE SUCCESS %s %s -> %s; log: %s' % (npc,mode,cfg['unreal_asset'],log))
        return report
    except Exception:
        report.update(status='FAILED',error=traceback.format_exc())
        write_json(log/'result.json',report)
        (log/'error.txt').write_text(report['error'],encoding='utf-8')
        unreal.log_error('CHARACTER_PIPELINE FAILED %s; details: %s' % (npc,log/'error.txt'))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--npc',required=True)
    parser.add_argument('--mode',choices=['validate','export','all','reimport'],default='all')
    args=parser.parse_args()
    run(args.npc,args.mode)
