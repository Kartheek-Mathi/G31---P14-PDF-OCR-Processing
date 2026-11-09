"""Build a ten-slide demo from saved evidence and verified project metadata.

Requires python-pptx, Pillow and LibreOffice for PDF export. The script refuses
silent success when PDF conversion fails. It does not publish to GitHub.
"""
from __future__ import annotations
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'SUBMISSION'
NAVY = '142B43'
TEAL = '087C8B'
INK = '163248'
MUTED = '536A79'
LIGHT = 'EDF5F7'
WHITE = 'FFFFFF'
AMBER = '9A5A0B'
LINE = 'D7E4E8'
WIDTH = 13.333333
HEIGHT = 7.5


def box(slide, x, y, w, h, fill=WHITE, border=None, radius=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                  Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if border:
        shape.line.color.rgb = RGBColor.from_string(border)
    else:
        shape.line.fill.background()
    return shape


def text(slide, x, y, w, h, value, size=22, color=INK, bold=False, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame; frame.clear(); frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(.02)
    frame.margin_top = frame.margin_bottom = Inches(.02)
    for i, line in enumerate(value.split('\n')):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = line; p.alignment = align; p.space_after = Pt(7)
        p.font.name = 'Arial'; p.font.size = Pt(size); p.font.bold = bold
        p.font.color.rgb = RGBColor.from_string(color)
    return shape


def photo(slide, path, x, y, w, h):
    with Image.open(path) as im:
        ratio = im.width / im.height
    ow, oh = w, w / ratio
    if oh > h: oh, ow = h, h * ratio
    return slide.shapes.add_picture(str(path), Inches(x+(w-ow)/2), Inches(y+(h-oh)/2), width=Inches(ow), height=Inches(oh))


def add_base(prs, n, label, title, subtitle=''):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = RGBColor.from_string(WHITE)
    box(slide, 0, 0, WIDTH, .12, TEAL)
    text(slide, .58, .32, 11.7, .3, label.upper(), 11, TEAL, True)
    text(slide, .58, .83, 12.1, .75, title, 30, NAVY, True)
    if subtitle: text(slide, .6, 1.57, 12.0, .5, subtitle, 15, MUTED)
    box(slide, .6, 7.05, 12.1, .012, LINE)
    text(slide, .6, 7.15, 10.8, .23, 'DOCWEAVE  /  CSE 573  /  PROJECT 14  /  SYNTHETIC PILOT', 9, MUTED)
    text(slide, 12.0, 7.12, .7, .3, f'{n:02d} / 10', 10, MUTED, align=PP_ALIGN.RIGHT)
    return slide


def card(slide, x, y, w, h, label, body, accent=TEAL, body_size=19):
    box(slide, x, y, w, h, LIGHT, LINE, True)
    text(slide, x+.2, y+.2, w-.4, .48, label, 21, accent, True)
    text(slide, x+.2, y+.85, w-.4, h-1.0, body, body_size, INK)


def main():
    meta = json.loads((ROOT/'PROJECT_METADATA.json').read_text())
    m = json.loads((ROOT/'EVALUATIONS/results/metrics.json').read_text())
    model = json.loads((ROOT/'DATA/models/bilstm.json').read_text())
    test = ET.parse(ROOT/'EVALUATIONS/results/tests.xml').getroot().find('testsuite')
    test_count = int(test.attrib['tests'])-int(test.attrib.get('failures', 0))-int(test.attrib.get('errors', 0))
    group = str(meta.get('group_number') or 'TBD')
    roster = ', '.join(p['name'] for p in meta.get('members', []) if p.get('name'))
    if not meta.get('team_roster_verified'): roster += '  |  Full roster pending verification'
    repo = meta.get('repository_url') or 'REPOSITORY URL REQUIRED BEFORE SUBMISSION'
    metadata_complete = all(meta.get(k) for k in ['group_number','repository_url','demo_date','team_roster_verified','contributions_verified','course_ai_policy_reviewed','repository_access_verified'])
    prs = Presentation(); prs.slide_width = Inches(WIDTH); prs.slide_height = Inches(HEIGHT)
    prs.core_properties.title = meta['project_title']
    prs.core_properties.subject = 'CSE 573 Project 14 demo: measured synthetic pilot'
    prs.core_properties.author = ', '.join(p['name'] for p in meta.get('members', []) if p.get('name'))
    prs.core_properties.comments = 'AI-assisted generated reference implementation. Team metadata and contributions require verification.'
    notes = []
    def note(s, duration, content):
        s.notes_slide.notes_text_frame.text = content + f'\nSuggested time: {duration} seconds.'
        notes.append((len(prs.slides), duration, content))

    # 1. Cover
    s = prs.slides.add_slide(prs.slide_layouts[6]); box(s, 0, 0, WIDTH, HEIGHT, NAVY)
    box(s, .65, .65, 3.7, .48, TEAL, radius=True)
    text(s, .82, .73, 3.4, .25, 'EVIDENCE-LINKED DOCUMENT INTELLIGENCE', 10, WHITE, True)
    text(s, .7, 1.65, 11.5, 1.1, 'DocWeave', 57, WHITE, True)
    text(s, .73, 2.92, 10.9, 1.25, 'PDF knowledge graphs for\nworkflow digitalization', 32, WHITE)
    text(s, .75, 4.61, 11.8, .45, f'Group {group}  /  Project 14  /  CSE 573  /  Fall 2026', 20, 'A9DFE5', True)
    text(s, .75, 5.27, 11.8, .65, roster, 17, WHITE)
    box(s, .75, 6.42, 11.8, .53, '213D56')
    text(s, .93, 6.53, 11.4, .3, 'Runnable prototype + measured synthetic experiments. Not a real-enterprise accuracy claim.', 14, WHITE)
    note(s, 35, 'Introduce DocWeave and the actual team. This package is an AI-assisted generated reference implementation. The displayed results were measured on fictional, reproducible workflow PDFs. Replace Group TBD and verify the entire team roster before presenting. The project demonstrates evidence-linked processing rather than unrestricted document understanding.')

    # 2. Problem
    s = add_base(prs, 2, 'Problem definition', 'A matching sentence is not always a supported answer.', 'Connect related statements while keeping the original PDF evidence visible.')
    card(s, .6, 2.2, 5.85, 2.75, 'The user question', 'Which council supervises the team managing Atlas40 Service?\nThe answer needs two linked facts.', body_size=21)
    card(s, 6.7, 2.2, 6.0, 2.75, 'Bounded system contract', 'Input: native or image-only PDFs\nOutput: typed facts, source pages and evidence paths\nScope: eight workflow predicates; English, closed entity grammar', body_size=19)
    box(s, .6, 5.22, 12.1, 1.18, NAVY, radius=True)
    text(s, .82, 5.42, 11.65, .72, 'Atlas40 Service  >  Cedar40 Team  >  Assurance40 Council\n           MANAGED_BY                           REPORTS_TO', 22, WHITE, align=PP_ALIGN.CENTER)
    note(s, 60, 'Use the actual fixture rather than an abstract example. The service sentence identifies Cedar40 Team; a second sentence says that Cedar40 Team reports to Assurance40 Council. Define success as recovering both supporting chunks and retaining their document/page links. Explain the closed schema: arbitrary invoices or legal narratives may yield text but no recognized relationships. Tables, coreference and general legal interpretation are not evaluated.')

    # 3. Architecture
    s = add_base(prs, 3, 'System architecture', 'One evidence contract connects every stage.', 'The tested core runs locally without cloud credentials.')
    stages = [('01  READ', 'pypdf native text\nPDFium previews\nTesseract fallback'),
              ('02  EXTRACT', 'Rule / logistic / LSTM\nType + direction checks\nNegation guard'),
              ('03  STORE', 'Atomic SQLite writes\nDocuments and edges\nHashed source identity'),
              ('04  EXPLORE', 'TF-IDF + path ranking\nDraggable graph\nSource-linked answers')]
    for i,(label,body) in enumerate(stages):
        card(s, .6+i*3.08, 2.28, 2.84, 2.35, label, body, body_size=17)
        if i < 3: text(s, 3.45+i*3.08, 3.16, .25, .45, '>', 25, TEAL, True)
    box(s, .6, 4.95, 12.08, .75, NAVY)
    text(s, .82, 5.12, 11.65, .44, 'document hash  /  page  /  chunk  /  exact quote  /  extraction method', 21, WHITE, align=PP_ALIGN.CENTER)
    text(s, .65, 6.08, 12.0, .55, 'Optional adapters: local Ollama LLM, Neo4j export, Docling conversion. Live services were not evaluated.', 17, MUTED)
    note(s, 70, 'Trace PDF bytes through the implemented modules: pdf_io.py, extractors.py, store.py and retrieval.py. Native pages avoid OCR; image-only pages use one bounded Tesseract batch. Re-ingestion is transactional and idempotent for identical bytes. Every edge retains its quote and page. Optional adapters are implemented code, not tested integrations; do not present LlamaCloud, dense pretrained retrieval or a live LLM run as completed work.')

    # 4. Algorithms
    s = add_base(prs, 4, 'Algorithms', 'Compare a simple baseline with a learned sequence model.', 'Keep entity handling fixed so extraction methods can be compared.')
    card(s, .6, 2.18, 3.87, 2.55, 'Conservative rules', 'Typed relation patterns\nTransparent but incomplete\nNo training data', body_size=20)
    card(s, 4.72, 2.18, 3.87, 2.55, 'TF-IDF + logistic', 'Unigram / bigram features\nC = 1; train split only\nStrong classical baseline', body_size=20)
    card(s, 8.84, 2.18, 3.87, 2.55, 'BiLSTM', f'32-dimensional embeddings\nBidirectional hidden size 32\n{model["parameter_count"]:,} trainable parameters', body_size=19)
    text(s, .7, 5.06, 12.0, .55, 'Entity masking  >  relation label  >  typed direction  >  quote-backed triple', 22, NAVY, True)
    text(s, .7, 5.83, 11.95, .75, 'Retrieval: lexical similarity + a bonus for chunks on a complete supported path.\nAnswers are deterministic path endpoints, with abstention when no path is found.', 20, MUTED)
    note(s, 65, 'The neural model is trained from scratch, not an LLM or pretrained transformer. Explain masking of entity identities and the nine labels, including NO_RELATION. Use the training split only for learning and the development split for checkpoint choice. The earliest best development checkpoint is epoch 5. The handcrafted question planner is an important limitation: the graph ranking bonus is evidence-path membership, not a learned reranker or general reasoning engine.')

    # 5. Data
    s = add_base(prs, 5, 'Datasets', 'WorkflowBench-S: explicit labels, fictional documents.', 'Original AI-assisted synthetic fixtures; no private or externally scraped records.')
    for i,(value,label) in enumerate([('48','one-page native PDFs'),('480','labeled statements'),('63','test questions'),('4','derived scan pages')]):
        x=.65+i*3.07; text(s,x,2.2,2.85,.83,value,43,TEAL,True);text(s,x,3.1,2.85,.55,label,18,INK)
    box(s,.65,4.05,12.0,.95,NAVY)
    text(s,.85,4.27,11.6,.45,'30 TRAIN DOCUMENTS     /     9 DEVELOPMENT     /     9 TEST',23,WHITE,True,PP_ALIGN.CENTER)
    text(s,.75,5.26,11.8,.58,'Normalize Unicode and whitespace; preserve pages; mask entity names; split conservatively.',19,INK)
    text(s,.75,6.03,11.8,.65,'Entity-disjoint splits, but normal-test wording overlaps training. A separate 72-statement slice uses unseen phrasing.',18,AMBER,True)
    note(s,60,'State the exact counts and synthetic origin. Each native PDF has eight positive relations and two non-assertive statements. Splits are 300/90/90 statements with disjoint entities. Gold labels are written independently of parsing, but both labels and documents share the same fixture design, so annotation independence is limited. Four scan pages derive from test documents and are correlated smoke tests, not a real-world OCR benchmark.')

    # 6. Design
    s=add_base(prs,6,'Evaluation design','Measure meaning, complete evidence and failure behavior.','Separate ordinary testing from a deliberate phrasing stress test.')
    card(s,.6,2.18,5.85,3.55,'Extraction experiments','90 standard-test statements\n72 unseen-phrase statements\n72 exact affirmative test triples\n\nMetrics: macro F1, triple precision / recall / F1',body_size=20)
    card(s,6.7,2.18,6.0,3.55,'Retrieval experiments','54 answerable + 9 unsupported queries\nSame corpus and neural graph in both modes\nLexical ranking versus graph-assisted ranking\n\nMetrics: Recall@5, MRR, complete-path coverage',body_size=19)
    text(s,.68,6.05,12.0,.62,'Also measured: CER / WER for four scans, per-query latency, automated tests and browser smoke checks.',18,MUTED)
    note(s,90,'Explain the ablation: same chunks and graph, different ranking score; both modes calculate a diagnostic graph trace, so this is not a graph-free latency comparison. Emphasize complete evidence coverage for two-hop questions rather than first-relevant-hit metrics alone. Bootstrap confidence intervals resample documents, not individual correlated question variants. Unanswerable examples are all annual-budget questions; their perfect abstention score does not establish general out-of-domain safety. OCR evaluates four actual scans in one batch.')

    # 7. Actual results
    s=add_base(prs,7,'Measured findings','Complete paths help; simpler models remain competitive.','All values below come from the included experiment outputs.')
    photo(s,ROOT/'EVALUATIONS/figures/relation-comparison.png',.6,2.18,6.2,3.55)
    text(s,7.12,2.28,5.4,.5,'EVIDENCE RETRIEVAL',16,TEAL,True)
    rows=[('Metric','TF-IDF','Graph'),('Recall@5','0.741','1.000'),('Two-hop complete@5','0.000','1.000')]
    for i,row in enumerate(rows):
        y=2.95+i*.64
        if i==0:box(s,7.12,y-.06,5.5,.59,LIGHT)
        text(s,7.22,y,3.12,.45,row[0],17,INK,i==0)
        text(s,10.43,y,.98,.45,row[1],18,INK,i>0,PP_ALIGN.CENTER)
        text(s,11.55,y,1.0,.45,row[2],18,TEAL,i>0,PP_ALIGN.CENTER)
    text(s,7.17,5.03,5.4,.76,f'OCR CER {100*m["ocr"]["character_error_rate"]:.2f}% / WER {100*m["ocr"]["word_error_rate"]:.2f}%\nFour correlated scan pages only.',17,MUTED)
    box(s,.65,6.05,12.0,.63,NAVY)
    text(s,.85,6.19,11.6,.32,'Unseen phrasing: logistic F1 0.833 > BiLSTM 0.708. Template accuracy is not generalization.',17,WHITE,True)
    note(s,85,'Report the measured advantage without hiding the artificial setting. Standard test macro F1 is 1.000 for both learned classifiers, but stress-test macro F1 is 0.833 for logistic and 0.708 for BiLSTM. The neural model mislabels oversees as alerts and secures communications as management in repeated templates. Graph Recall@5 is 1.000 versus 0.741, with lexical document-bootstrap interval approximately 0.667 to 0.806. Two-hop complete@5 is zero for lexical mode and one for graph mode on eighteen narrow-schema questions. This is a designed proof of integration, not state-of-the-art performance.')

    # 8. UI source
    s=add_base(prs,8,'UI / source inspection','Start with the source, then inspect the extracted facts.','Actual running interface, not a mockup.')
    slide_crop=ROOT/'EVALUATIONS/figures/02-documents-slide.png'
    with Image.open(ROOT/'EVALUATIONS/screenshots/02-documents.png') as image:
        image.crop((548,220,1495,740)).save(slide_crop)
    photo(s,slide_crop,.68,2.03,11.98,4.35)
    text(s,.72,6.54,11.8,.35,'Select a PDF  >  compare page and text  >  inspect eight relationships  >  export evidence',18,TEAL,True,PP_ALIGN.CENTER)
    note(s,85,'Switch to the live local application or use this screenshot as the allowed fallback. Open workflow-40.pdf. Show the original page and extracted text side by side, then the eight relationship records. Change the page selector on a multi-page upload if available. Explain the distinction between a PDF/OCR error and a relation-classifier error. The system can extract text from unsupported documents without inventing relationships. The screenshot was captured from the real app through a local API bridge because direct browser networking was restricted in the build environment.')

    # 9. UI graph + search
    s=add_base(prs,9,'UI / graph and answers','Inspect the graph, the evidence and the unsupported case.','The evidence inspector and the answer trace use the same stored provenance.')
    photo(s,ROOT/'EVALUATIONS/figures/03-graph-crop.png',.6,2.2,6.0,3.55)
    photo(s,ROOT/'EVALUATIONS/figures/04-search-crop.png',6.85,2.2,5.85,3.55)
    text(s,.65,5.9,5.85,.46,'Graph: select an edge to inspect its source.',17,INK,True)
    text(s,6.9,5.9,5.8,.46,'Answer: Assurance40 Council + two sources.',17,INK,True)
    box(s,.65,6.45,12.0,.42,LIGHT)
    text(s,.85,6.51,11.6,.27,'Unsupported example: "What is the annual budget of Atlas40 Service?"  >  explicit abstention',15,AMBER,True)
    note(s,100,'Focus the graph on Atlas40 Service and click MANAGED_BY. Show the source quote and the note that its model score is not calibrated. Ask the council question and trace Service to Team to Council. Click both citations. Then ask the annual-budget question to demonstrate abstention. Explain that graph visualizations and exact quotes do not guarantee predicate correctness; a mislabeled relation can still point to a real sentence. The current question parser is handcrafted and its behavior on unfamiliar query language remains a limitation.')

    # 10. Plan + mandatory repository link
    s=add_base(prs,10,'Project plan / repository','Finish team verification and the repository handoff.',('Verified team metadata and repository link are included; confirm the final Canvas deadlines.' if metadata_complete else 'Do not submit this review copy with placeholder group or repository information.'))
    rows=[('Delivered in this package',f'Runnable app, eight-page report, 10-slide demo, {test_count} passing tests.',('Verified contribution record is included in the report.' if meta.get('contributions_verified') else 'AI-assisted build; team ownership not assigned.')),
          ('Before the assigned demo','Verify local browser access; rehearse 12 minutes; assign presenters.',('Demo date: '+meta['demo_date']+'; confirm the assigned presenters.' if meta.get('demo_date') else 'Actual team members and demo date pending.')),
          ('Before December 9, 2026','Review course AI policy; verify contributions; test repository access.',('Complete final instructor checks using the verified team record.' if meta.get('contributions_verified') else 'Assign named owners and record real evidence.'))]
    for i,(title,task,owner) in enumerate(rows):
        y=2.17+i*1.04
        box(s,.65,y,12.0,.91,LIGHT)
        text(s,.85,y+.12,3.15,.6,title,18,TEAL,True)
        text(s,4.1,y+.1,8.25,.35,task,17,INK)
        text(s,4.1,y+.5,8.25,.28,owner,13,MUTED)
    box(s,.65,5.65,12.0,1.05,NAVY)
    text(s,.85,5.8,11.6,.25,'GITHUB REPOSITORY / VERIFY INSTRUCTOR ACCESS',12,'A9DFE5',True)
    link=text(s,.85,6.15,11.6,.38,repo,19,WHITE,True)
    if meta.get('repository_url'):link.text_frame.paragraphs[0].runs[0].hyperlink.address=repo
    note(s,70,'State actual ownership only after the team has verified it. The provided package is not evidence that any member previously implemented its modules. Assign real presenters and responsibilities, record completed contributions with files or commits, and review the course AI-use policy. A GitHub remote was not available during the artifact build. Publish the repository, verify instructor access, insert its real URL in PROJECT_METADATA.json and regenerate this slide. The final report is due December 9, 2026 at the time shown in Canvas; one person submits for the group.')

    OUT.mkdir(exist_ok=True)
    stem=f'Group{group}-Project14-FA26-Group-DEMO-Presentation'
    pptx=OUT/(stem+'.pptx');prs.save(pptx)
    notes_path=OUT/'demo/speaker_notes.md';notes_path.parent.mkdir(exist_ok=True)
    notes_path.write_text('# DocWeave demo speaker notes\n\nSuggested speaking time: 720 seconds (12 minutes), including the live/screenshot demonstration. Adjust pacing after rehearsal.\n\n'+ '\n\n'.join(f'## Slide {i} - {seconds} seconds\n\n{content}' for i,seconds,content in notes)+'\n')
    assert len(prs.slides)==10 and sum(n[1] for n in notes)==720
    exe=shutil.which('libreoffice') or shutil.which('soffice')
    if not exe:raise SystemExit(f'Created {pptx}. Install LibreOffice to export the required PDF, then rerun.')
    with tempfile.TemporaryDirectory(prefix='docweave-slides-') as tmp:
        profile=Path(tmp)/'profile';export=Path(tmp)/'export';export.mkdir()
        command=[exe,'-env:UserInstallation='+profile.as_uri(),'--headless','--convert-to','pdf','--outdir',str(export),str(pptx)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=120)
        (ROOT/'EVALUATIONS/results/demo_build.log').write_text(result.stdout+result.stderr)
        generated=export/(stem+'.pdf')
        if result.returncode or not generated.exists():raise RuntimeError('LibreOffice PDF export failed: '+result.stdout+result.stderr)
        pdf=OUT/(stem+'.PDF');shutil.copy2(generated,pdf)
    from pypdf import PdfReader
    count=len(PdfReader(pdf).pages)
    if count!=10:raise RuntimeError(f'Expected 10 PDF slides, found {count}')
    print(json.dumps({'pptx':str(pptx),'pdf':str(pdf),'slides':count,'seconds':720,'repository_url_present':bool(meta.get('repository_url'))},indent=2))

if __name__=='__main__':main()
