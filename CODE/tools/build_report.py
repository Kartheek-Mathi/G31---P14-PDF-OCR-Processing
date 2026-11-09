"""Build the IEEE report from actual saved metrics and truthful project metadata."""
from pathlib import Path
import json, shutil, subprocess, re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"SUBMISSION/report"

def tex(text):
    substitutions={"\\":r"\textbackslash{}","&":r"\&","%":r"\%","$":r"\$","#":r"\#","_":r"\_","{":r"\{","}":r"\}","~":r"\textasciitilde{}","^":r"\textasciicircum{}"}
    return "".join(substitutions.get(c,c) for c in str(text))

def main():
    meta=json.loads((ROOT/"PROJECT_METADATA.json").read_text()); m=json.loads((ROOT/"EVALUATIONS/results/metrics.json").read_text())
    model=json.loads((ROOT/"DATA/models/bilstm.json").read_text())
    group=str(meta.get("group_number") or "TBD")
    members=meta.get("members") or []
    authors=", ".join(member["name"] for member in members if member.get("name")) or "Team roster not supplied"
    ready=bool(meta.get("group_number") and meta.get("team_roster_verified") and meta.get("contributions_verified") and meta.get("repository_url") and meta.get("course_ai_policy_reviewed") and meta.get("repository_access_verified") and all(p.get("name") and p.get("contribution") and p.get("evidence") for p in members))
    notice="" if ready else r"\begin{center}\footnotesize\textbf{Review draft:} group metadata, complete team roster, contribution statements and repository link require verification before submission.\end{center}"
    contribution_notice=("The following statements record the team's verified completed work." if meta.get("contributions_verified") else
        "Individual work histories were not supplied. This package was generated with AI assistance at the request of Jatin Kumar Reddimalla; it is not evidence that any named team member personally completed a particular module. The table must be completed with actual, verified contributions before submission. The course's AI-use policy must also be checked.")
    rows=[]
    for member in members:
        description=member.get("contribution") or "Contribution not supplied; must be verified."
        if member.get("evidence"): description+=" Evidence: "+member["evidence"]
        rows.append(tex(member.get("name","Name not supplied"))+" & "+tex(description)+r"\\")
    if not meta.get("team_roster_verified"): rows.append(r"Remaining team roster & Names and contributions not supplied.\\")
    team={"GroupNumber":tex(group),"AuthorNames":tex(authors),"MetadataNotice":notice,
          "RepositoryURL":tex(meta.get("repository_url") or "Repository URL not supplied"),
          "ContributionNotice":tex(contribution_notice),"ContributionRows":"\n".join(rows),
          "ContributionCaption":("Verified team contribution record" if meta.get("contributions_verified") else "Team contribution record (verification pending)")}
    (REPORT/"team.tex").write_text("\n".join("\\newcommand{\\"+k+"}{"+v+"}" for k,v in team.items())+"\n")
    test_file=ROOT/"EVALUATIONS/results/tests.xml";tests=ET.parse(test_file).getroot().find("testsuite")
    macros={"ModelParameters":f"{model['parameter_count']:,}","SelectedEpoch":str(model['selected_epoch']),"RawBytes":f"{m['data']['raw_bytes']:,}",
        "OCRcer":f"{100*m['ocr']['character_error_rate']:.2f}","OCRwer":f"{100*m['ocr']['word_error_rate']:.2f}",
        "LexicalLatency":f"{m['retrieval']['lexical']['latency_median_ms']:.2f}","GraphLatency":f"{m['retrieval']['graph']['latency_median_ms']:.2f}",
        "TestCount":str(int(tests.attrib['tests'])-int(tests.attrib.get('failures',0))-int(tests.attrib.get('errors',0)))}
    (REPORT/"metrics.tex").write_text("\n".join("\\newcommand{\\"+k+"}{"+v+"}" for k,v in macros.items())+"\n")
    (REPORT/"assets").mkdir(exist_ok=True)
    for name in ["architecture.pdf","relation-comparison.pdf","retrieval-by-type.pdf","02-documents-crop.png","03-graph-crop.png","04-search-crop.png"]:
        shutil.copy2(ROOT/"EVALUATIONS/figures"/name,REPORT/"assets"/name)
    build=REPORT/"build";build.mkdir(exist_ok=True)
    commands=[["pdflatex","-interaction=nonstopmode","-halt-on-error","-output-directory=build","main.tex"],
              [(shutil.which("bibtex") or shutil.which("bibtex.original") or "bibtex"),"build/main"],
              ["pdflatex","-interaction=nonstopmode","-halt-on-error","-output-directory=build","main.tex"],
              ["pdflatex","-interaction=nonstopmode","-halt-on-error","-output-directory=build","main.tex"]]
    logs=[]
    for command in commands:
        if shutil.which(command[0]) is None: raise SystemExit(f"Install {command[0]} (TeX Live/MiKTeX with IEEEtran) to rebuild.")
        result=subprocess.run(command,cwd=REPORT,capture_output=True,text=True)
        logs.append(result.stdout+result.stderr)
        if result.returncode:
            (ROOT/"EVALUATIONS/results/report_build.log").write_text("\n".join(logs))
            raise SystemExit(result.stdout[-4000:]+result.stderr)
    output=ROOT/"SUBMISSION"/f"Group{group}-Project14-F26-Final Project Report.PDF"
    shutil.copy2(build/"main.pdf",output)
    from pypdf import PdfReader
    count=len(PdfReader(output).pages)
    (ROOT/"EVALUATIONS/results/report_build.log").write_text("\n".join(logs))
    print(json.dumps({"file":str(output),"pages":count,"metadata_ready":ready},indent=2))
    if not 5<=count<=10: raise SystemExit(f"Report is {count} pages; required range is 5-10. Adjust content, not IEEE formatting.")
if __name__=="__main__":main()
