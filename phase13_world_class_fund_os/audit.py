
from __future__ import annotations
from pathlib import Path
import hashlib, json, datetime, os

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def build_manifest(root='.'):
    root=Path(root)
    files=[]
    for p in root.rglob('*'):
        if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts:
            files.append({'path': str(p.relative_to(root)).replace('\\','/'), 'sha256': file_sha256(p), 'bytes': p.stat().st_size})
    files.sort(key=lambda x:x['path'])
    digest=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    return {'version':'V1300_PHASE13_WORLD_CLASS_FUND_OS_TRUE_LATEST','generated_utc':datetime.datetime.utcnow().isoformat()+'Z','file_count':len(files),'repository_sha256':digest,'files':files}
