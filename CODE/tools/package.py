"""Package shareable project files; exclude runtime uploads, caches and secrets."""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[2]


def included(path: Path) -> bool:
    rel=path.relative_to(ROOT)
    if not path.is_file():return False
    if any(p in {'.git','.venv','__pycache__','.pytest_cache','build'} for p in rel.parts):return False
    if rel.parts[:2]==('DATA','runtime'):return False
    if path.name=='.env' or path.suffix.lower() in {'.pyc','.ttf','.otf','.woff','.woff2'}:return False
    return True


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT.parent)
    args=parser.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if output==ROOT or ROOT in output.parents:raise SystemExit('Use an output directory outside the repository.')
    paths=sorted(p for p in ROOT.rglob('*') if included(p) and p.name!='FILE_MANIFEST.json')
    manifest={'project':'DocWeave / CSE 573 Project 14','remote_published':False,
              'note':'SHA-256 hashes cover the included files except this manifest. Metadata still requires team verification.',
              'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
    (ROOT/'FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    full=output/'DocWeave-Project14-Complete.zip'
    with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in paths+[ROOT/'FILE_MANIFEST.json']:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
    latex=output/'DocWeave-IEEE-LaTeX-Source.zip'
    report=ROOT/'SUBMISSION/report'
    with zipfile.ZipFile(latex,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(report.rglob('*')):
            if included(p):z.write(p,p.relative_to(report))
    meta=json.loads((ROOT/'PROJECT_METADATA.json').read_text());g=str(meta.get('group_number') or 'TBD')
    mapping={ROOT/'SUBMISSION'/f'Group{g}-Project14-F26-Final Project Report.PDF':'DocWeave-Final-Report.pdf',
             ROOT/'SUBMISSION'/f'Group{g}-Project14-FA26-Group-DEMO-Presentation.PDF':'DocWeave-Demo.pdf',
             ROOT/'SUBMISSION'/f'Group{g}-Project14-FA26-Group-DEMO-Presentation.pptx':'DocWeave-Demo.pptx',
             ROOT/'SUBMISSION/demo/speaker_notes.md':'DocWeave-Speaker-Notes.md',
             ROOT/'START_HERE.md':'DocWeave-Start-Here.md',
             ROOT/'EVALUATIONS/results/metrics.json':'DocWeave-Measured-Results.json'}
    for src,name in mapping.items():shutil.copy2(src,output/name)
    print(json.dumps({'repository_zip':str(full),'repository_files':len(paths)+1,'repository_zip_bytes':full.stat().st_size,'latex_zip':str(latex),'standalone_files':list(mapping.values())},indent=2))
if __name__=='__main__':main()
