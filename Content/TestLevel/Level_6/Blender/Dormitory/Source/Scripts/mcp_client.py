"""Local stdio MCP client. No implicit blend saving or exporting."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code')
    parser.add_argument('--screenshot')
    args = parser.parse_args()
    env = dict(os.environ, BLENDER_MCP_HOST='localhost', BLENDER_MCP_PORT='9875', PYTHONDONTWRITEBYTECODE='1')
    params = StdioServerParameters(command=r'D:\program\blender\blender_mcp\mcp\.venv\Scripts\python.exe', args=['-B', '-m', 'blmcp'], cwd=r'D:\program\blender\blender_mcp\mcp', env=env)
    async with stdio_client(params) as (rd, wr):
        async with ClientSession(rd, wr) as session:
            await session.initialize()
            if args.code:
                response = await asyncio.wait_for(session.call_tool('execute_blender_code', {'code': Path(args.code).read_text(encoding='utf-8-sig')}), 90)
            elif args.screenshot:
                response = await asyncio.wait_for(session.call_tool('get_screenshot_of_area_as_image', {'area_ui_type': 'VIEW_3D'}), 40)
            else:
                response = await session.call_tool('get_objects_summary', {})
            for block in response.content:
                if block.type == 'image' and args.screenshot:
                    path = Path(args.screenshot)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(base64.b64decode(block.data))
                    print(json.dumps({'screenshot': str(path.resolve())}))
                elif block.type == 'text':
                    print(block.text)

if __name__ == '__main__':
    asyncio.run(main())
