#!/usr/bin/env python3
"""DocWeave command-line entrypoint. Run from any current working directory."""
from pathlib import Path
import argparse, json, os
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description="Local PDF-to-graph workflow prototype")
    sub = parser.add_subparsers(dest="command",required=True)
    serve=sub.add_parser("serve"); serve.add_argument("--port",type=int,default=8000)
    serve.add_argument("--extractor",choices=["rules","logistic","neural","ollama"],default="neural")
    seed=sub.add_parser("seed"); seed.add_argument("--extractor",choices=["rules","logistic","neural","ollama"],default="neural")
    ingest=sub.add_parser("ingest"); ingest.add_argument("file",type=Path); ingest.add_argument("--extractor",default="neural")
    search=sub.add_parser("search"); search.add_argument("question"); search.add_argument("--method",choices=["lexical","graph"],default="graph")
    neo=sub.add_parser("export-neo4j"); neo.add_argument("--database",default="neo4j")
    doc=sub.add_parser("convert-docling"); doc.add_argument("file",type=Path); doc.add_argument("output",type=Path)
    args=parser.parse_args()
    if args.command=="serve":
        import uvicorn
        from docweave.server import create_app
        uvicorn.run(create_app(ROOT,args.extractor),host="127.0.0.1",port=args.port)
        return
    if args.command=="convert-docling":
        from docweave.adapters import docling_markdown
        docling_markdown(args.file,args.output); return
    from docweave.store import Store
    store=Store(ROOT/"DATA/runtime/docweave.sqlite3")
    if args.command in {"seed","ingest"}:
        from docweave.pipeline import Pipeline
        from docweave.extractors import get_extractor
        engine=Pipeline(store,ROOT/"DATA/runtime/uploads",get_extractor(args.extractor,ROOT/"DATA/models"))
        paths=sorted((ROOT/"DATA/raw").glob("*.pdf")) if args.command=="seed" else [args.file]
        for path in paths: print(json.dumps(engine.ingest(path.read_bytes(),path.name,allow_ocr=args.command!="seed")))
    elif args.command=="search":
        from docweave.retrieval import Retriever
        print(json.dumps(Retriever(store.all_chunks(),store.all_triples()).search(args.question,args.method),indent=2))
    elif args.command=="export-neo4j":
        from docweave.adapters import export_neo4j
        password=os.environ.get("NEO4J_PASSWORD")
        if not password: parser.error("Set NEO4J_PASSWORD in your environment; do not commit it.")
        count=export_neo4j(store.all_triples(),os.getenv("NEO4J_URI","bolt://127.0.0.1:7687"),os.getenv("NEO4J_USER","neo4j"),password,args.database)
        print(json.dumps({"relationships_imported":count}))
if __name__=="__main__": main()
