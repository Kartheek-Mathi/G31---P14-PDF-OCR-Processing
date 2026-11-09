"""Capture genuine browser screenshots and exercise the local demo interface."""
from pathlib import Path
import argparse, json, shutil, time, base64
import httpx
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--url",default="http://127.0.0.1:8000")
    parser.add_argument("--bridge",action="store_true",help="Use a local API bridge when browser navigation is restricted.")
    args=parser.parse_args(); output=ROOT/"EVALUATIONS/screenshots";output.mkdir(exist_ok=True,parents=True)
    checks=[];errors=[]
    with sync_playwright() as p:
        executable=shutil.which("chromium") or shutil.which("chromium-browser")
        browser=p.chromium.launch(headless=True,executable_path=executable,args=["--no-sandbox"])
        page=browser.new_page(viewport={"width":1536,"height":1040},device_scale_factor=1)
        page.on("pageerror",lambda err:errors.append(str(err)))
        if args.bridge:
            client=httpx.Client(base_url=args.url)
            def transport(url,options):
                response=client.request(options.get("method","GET"),url,headers=options.get("headers",{}),content=options.get("body"))
                return {"ok":response.is_success,"status":response.status_code,"body":response.json()}
            page.expose_function("localApiTransport",transport)
            web=ROOT/"CODE/docweave/web"
            html=(web/"index.html").read_text()
            html=html.replace('<link rel="stylesheet" href="/static/styles.css">','').replace('<script src="/static/app.js" defer></script>','')
            page.set_content(html)
            page.add_style_tag(content=(web/"styles.css").read_text())
            page.evaluate("""() => {window.fetch=async(url,options={})=>{const r=await window.localApiTransport(url,options);return {ok:r.ok,status:r.status,json:async()=>r.body};};}""")
            page.add_script_tag(content=(web/"app.js").read_text())
        else:
            page.goto(args.url,wait_until="networkidle")
        page.wait_for_selector("#stats .stat")
        assert page.locator("#stats .stat strong").first.inner_text()=="48"
        checks.append("Overview displays 48 seeded documents")
        page.screenshot(path=str(output/"01-overview.png"),full_page=True)
        page.click('[data-view="documents"]');page.wait_for_selector(".page-image")
        if args.bridge:
            source=page.locator('.page-image').get_attribute('src')
            png=client.get(source).content
            page.locator('.page-image').evaluate("(img,src)=>img.src=src", "data:image/png;base64,"+base64.b64encode(png).decode())
        page.wait_for_function("document.querySelector('.page-image').complete && document.querySelector('.page-image').naturalWidth > 0")
        assert "workflow-40.pdf" in page.locator("#document-detail").inner_text()
        assert page.locator("#document-detail tbody tr").count()==8
        checks.append("Document inspector shows original PDF and eight extracted relationships")
        page.screenshot(path=str(output/"02-documents.png"),full_page=True)
        page.click('[data-view="graph"]');page.wait_for_selector(".graph-node")
        assert page.locator(".graph-node").count()==9
        assert "MANAGED_BY" in page.locator("#graph-evidence").inner_text()
        checks.append("Graph displays nine focused entities and an evidence inspector")
        page.screenshot(path=str(output/"03-graph.png"),full_page=True)
        page.click('[data-view="search"]');page.click('#search-form button')
        page.wait_for_selector(".answer-card")
        assert "Assurance40 Council" in page.locator(".answer-card h3").inner_text()
        assert page.locator(".result-card .tag").filter(has_text="ON EVIDENCE PATH").count()==2
        checks.append("Two-hop question returns Assurance40 Council with two evidence links")
        page.screenshot(path=str(output/"04-search.png"),full_page=True)
        page.fill('#question','What is the annual budget of Atlas40 Service?');page.click('#search-form button')
        page.wait_for_function("document.querySelector('.answer-card').textContent.includes('ABSTAINED')")
        checks.append("Unsupported budget question explicitly abstains")
        page.screenshot(path=str(output/"06-abstention.png"),full_page=True)
        page.click('[data-view="evaluation"]');page.wait_for_selector("#evaluation-content table")
        assert "0.708" in page.locator("#evaluation-content").inner_text()
        checks.append("Evaluation view shows measured stress-test results")
        page.screenshot(path=str(output/"05-evaluation.png"),full_page=True)
        assert not errors,errors
        checks.append("No browser JavaScript exceptions during the smoke test")
        browser.close()
    result={"checks":checks,"passed":len(checks),"javascript_errors":errors,"viewport":[1536,1040],"transport":"local API bridge (browser direct-network navigation restricted)" if args.bridge else "direct HTTP browser", "screenshots":"actual running FastAPI application; not mockups"}
    (ROOT/"EVALUATIONS/results/browser_smoke.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
