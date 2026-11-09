"""Check artifact integrity and submission metadata; missing evidence is a failure.

Manual verification flags are attestations by the team, not independently checked
identity, contribution, course-policy or repository-access facts.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[2]


def check():
    issues, checks = [], []
    meta = json.loads((ROOT/'PROJECT_METADATA.json').read_text())
    group = meta.get('group_number')
    if not isinstance(group,int) or isinstance(group,bool) or group < 1:
        issues.append('Actual positive integer group_number has not been supplied.')
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?',meta.get('repository_url','')):
        issues.append('A real, published GitHub repository URL is required.')
    try: dt.date.fromisoformat(meta.get('demo_date',''))
    except ValueError: issues.append('Assigned demo_date is missing; enter YYYY-MM-DD from the course schedule.')
    for flag in ['team_roster_verified','contributions_verified','course_ai_policy_reviewed','repository_access_verified']:
        if meta.get(flag) is not True:issues.append(f'Team attestation pending: {flag}.')
    members = meta.get('members',[])
    if not members: issues.append('No team members listed.')
    for member in members:
        for key in ['name','contribution','evidence']:
            if not str(member.get(key,'')).strip():issues.append(f'Member {member.get("name","unnamed")}: {key} is missing.')
    group_label=str(group or 'TBD')
    report=ROOT/'SUBMISSION'/f'Group{group_label}-Project14-F26-Final Project Report.PDF'
    deck_pdf=ROOT/'SUBMISSION'/f'Group{group_label}-Project14-FA26-Group-DEMO-Presentation.PDF'
    deck_pptx=deck_pdf.with_suffix('.pptx')
    for label,path in [('report',report),('demo_pdf',deck_pdf),('demo_pptx',deck_pptx)]:
        if not path.exists():issues.append(f'Missing {label}: {path.name}')
    if report.exists():
        reader=PdfReader(report);pages=len(reader.pages)
        checks.append({'check':'Report page count','value':pages,'pass':5<=pages<=10})
        if not 5<=pages<=10:issues.append('Report must be 5-10 pages.')
        full=' '.join(p.extract_text() or '' for p in reader.pages)
        compact=re.sub(r'\s+',' ',full).lower()
        compact_letters=re.sub(r'[^a-z0-9]','',compact)
        for required in ['abstract','introduction','problem statement','related works','system architecture','datasets','evaluations','visualization interface designs','contributions','conclusions','references']:
            if re.sub(r'[^a-z0-9]','',required) not in compact_letters:issues.append(f'Report section not found: {required}')
        if 'review draft:' in compact:issues.append('Report still identifies itself as a review draft; rebuild after metadata verification.')
    if deck_pdf.exists():
        pages=len(PdfReader(deck_pdf).pages);checks.append({'check':'Demo PDF slide count','value':pages,'pass':pages==10})
        if pages!=10:issues.append('The demo PDF must have the planned 10 slides.')
    if deck_pptx.exists():
        prs=Presentation(deck_pptx);count=len(prs.slides)
        checks.append({'check':'Editable deck slide count','value':count,'pass':count==10})
        if count!=10:issues.append('Editable deck does not have 10 slides.')
        last=' '.join(shape.text for shape in prs.slides[-1].shapes if shape.has_text_frame)
        if not meta.get('repository_url') or meta['repository_url'] not in last:
            issues.append('The final slide does not contain the actual repository URL.')
    test_file=ROOT/'EVALUATIONS/results/tests.xml'
    if test_file.exists():
        suites=list(ET.parse(test_file).getroot().iter('testsuite'))
        errors=sum(int(x.attrib.get('failures',0))+int(x.attrib.get('errors',0)) for x in suites)
        count=sum(int(x.attrib.get('tests',0)) for x in suites)
        checks.append({'check':'Saved automated test run','value':count,'pass':errors==0 and count>0})
        if errors or not count:issues.append('Saved test run contains failures/errors or no tests.')
    else:issues.append('Missing machine-readable automated test evidence.')
    for relative in ['README.md','DATA/README.md','CODE/run.py','EVALUATIONS/results/metrics.json','SUBMISSION/demo/speaker_notes.md']:
        if not (ROOT/relative).exists():issues.append(f'Missing required project artifact: {relative}')
    return {'ready_for_submission':not issues,'checks':checks,'blocking_issues':issues,
            'notice':'Repository access, contributions and course-policy compliance require truthful manual verification; this script does not certify them.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'EVALUATIONS/results/submission_validation.json')
    args=parser.parse_args();result=check();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    sys.exit(0 if result['ready_for_submission'] else 1)
if __name__=='__main__':main()
