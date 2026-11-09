'use strict';
const $ = (s) => document.querySelector(s);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let documents = [], selectedDocument = null, selectedPage = 1;
const titles = {overview:'From documents to evidence.', documents:'Read the source. Inspect the structure.', graph:'Relationships you can verify.', search:'Answers grounded in a source.', evaluation:'Evidence for the system itself.'};
async function api(url, options={}) {
  const response = await fetch(url, options);
  const content = await response.json();
  if (!response.ok) throw new Error(typeof content.detail === 'string' ? content.detail : `Request failed (${response.status}).`);
  return content;
}
function message(text, error=false) { const box=$('#message'); box.textContent=text; box.hidden=!text; if(error) box.scrollIntoView({block:'nearest'}); }
async function showView(view) {
  document.querySelectorAll('.view').forEach(el=>el.classList.toggle('active',el.id===`view-${view}`));
  document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.view===view));
  $('#page-title').textContent=titles[view]; message('');
  try {
    if(view==='documents') await loadDocuments();
    if(view==='graph') await loadGraph();
    if(view==='evaluation') await loadEvaluation();
  } catch(error) { message(error.message,true); }
}
async function loadStatus(){
  const s=await api('/api/status');
  $('#engine').textContent=`${s.extractor.toUpperCase()} / LOCAL`;
  $('#stats').innerHTML=[[s.documents,'SOURCE DOCUMENTS'],[s.nodes,'MAPPED ENTITIES'],[s.triples,'GROUNDED RELATIONS'],[s.chunks,'EVIDENCE CHUNKS']].map(([n,label])=>`<div class="stat"><strong>${n}</strong><span>${label}</span></div>`).join('');
}
async function loadDocuments(){
  documents=await api('/api/documents'); drawDocumentList();
  const preferred=documents.find(d=>d.id===selectedDocument) || documents.find(d=>d.filename==='workflow-40.pdf') || documents[0];
  if(preferred) await selectDocument(preferred.id);
}
function drawDocumentList(){
  const filter=$('#doc-filter').value.toLowerCase();
  $('#documents-list').innerHTML=documents.filter(d=>d.filename.toLowerCase().includes(filter)).map(d=>`<button class="doc-item ${d.id===selectedDocument?'active':''}" data-doc="${esc(d.id)}"><strong>${esc(d.filename)}</strong><small>${d.pages} page &middot; ${d.triples} relationships</small></button>`).join('');
}
async function selectDocument(id){
  selectedDocument=id; drawDocumentList();
  const d=await api(`/api/documents/${encodeURIComponent(id)}`);
  selectedPage = Math.max(1, Math.min(selectedPage, d.pages));
  const page=d.page_data[selectedPage-1];
  $('#document-detail').innerHTML=`<div class="section-heading"><div><h3>${esc(d.filename)}</h3><span class="muted small">${d.pages} page(s) &middot; ${esc(d.extractor)} &middot; Content-addressed source</span></div><div><select id="page-selector" aria-label="Document page">${d.page_data.map(p=>`<option value="${p.page}" ${p.page===selectedPage?'selected':''}>Page ${p.page}</option>`).join('')}</select> <a class="button secondary" href="/api/documents/${esc(id)}/file">Original PDF</a></div></div><div class="document-panels"><div><div class="mini-label">ORIGINAL / PAGE ${selectedPage}</div><img class="page-image" src="/api/documents/${esc(id)}/pages/${selectedPage}" alt="Original page ${selectedPage} of ${esc(d.filename)}"></div><div><div class="mini-label">EXTRACTED TEXT / ${esc(page.method.toUpperCase())}</div><div class="extracted-text">${esc(page.text)}</div><p class="muted small">Text displayed as data. Document instructions are never executed.</p></div></div><div class="section-heading" style="margin-top:22px"><h3>Extracted relationships</h3><span class="tag">${d.triples.length} SOURCE-LINKED</span></div><div class="table-wrap"><table><thead><tr><th>SUBJECT</th><th>RELATION</th><th>OBJECT</th></tr></thead><tbody>${d.triples.map(t=>`<tr><td>${esc(t.subject)}</td><td><code>${esc(t.predicate)}</code></td><td>${esc(t.object)}</td></tr>`).join('')}</tbody></table></div>`;
  $('#page-selector').addEventListener('change', e=>{selectedPage=Number(e.target.value);selectDocument(id).catch(error=>message(error.message,true));});
  const active=$(`[data-doc="${id}"]`); if(active) active.scrollIntoView({block:'nearest'});
}
async function upload(file){
  if(!file) return;
  const data=new FormData(); data.append('file',file);
  message('Processing the selected PDF locally.');
  try { const result=await api('/api/ingest',{method:'POST',body:data}); selectedDocument=result.id; await loadDocuments(); await loadStatus(); message(`Processed ${result.filename}: ${result.triples} grounded relationships. ${result.empty_pages?`${result.empty_pages} page(s) had no usable text.`:''}`); }
  catch(error){message(error.message,true);} finally {$('#upload').value='';}
}
function edgeEvidence(edge){
  $('#graph-evidence').innerHTML=`<span class="eyebrow">RELATIONSHIP INSPECTOR</span><h3>${esc(edge.subject)}</h3><span class="tag">${esc(edge.predicate)}</span><h3>${esc(edge.object)}</h3><div class="quote">${esc(edge.quote)}</div><div class="detail-pair"><small>SOURCE</small>${esc(edge.filename)} &middot; page ${edge.page}</div><div class="detail-pair"><small>EXTRACTOR</small>${esc(edge.method)}</div><div class="detail-pair"><small>MODEL SCORE / NOT CALIBRATED</small>${Number(edge.confidence).toFixed(3)}</div><button class="button secondary" data-open-document="${esc(edge.document_id)}" data-page="${edge.page}">Inspect source document</button>`;
}
async function loadGraph(){
  const graph=await api(`/api/graph?focus=${encodeURIComponent($('#graph-focus').value)}&limit=45`);
  $('#graph-count').textContent=`${graph.nodes.length} entities / ${graph.edges.length} relationships${graph.truncated?' (subset)':''}`;
  const svg=$('#graph-svg'); svg.replaceChildren(); const ns='http://www.w3.org/2000/svg';
  function el(name,attrs={},text){const n=document.createElementNS(ns,name); for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v); if(text!==undefined)n.textContent=text; return n;}
  const defs=el('defs'); const marker=el('marker',{id:'arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'}); marker.append(el('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#93b0bb'}));defs.append(marker);svg.append(defs);
  if(!graph.nodes.length){svg.append(el('text',{x:435,y:285,'text-anchor':'middle',fill:'#617483'},'No matching entities. Try an indexed entity name.'));return;}
  const centerIndex=graph.nodes.findIndex(n=>n.type==='Service');
  const central=graph.nodes[centerIndex>=0?centerIndex:0]; const others=graph.nodes.filter(n=>n.id!==central.id);
  const positions=new Map([[central.id,{x:435,y:300}]]);
  others.forEach((n,i)=>{const a=-Math.PI/2+i*2*Math.PI/others.length;positions.set(n.id,{x:435+300*Math.cos(a),y:300+225*Math.sin(a)});});
  const edgeElements=[];
  for(const edge of graph.edges){
    const group=el('g');const line=el('line',{class:'edge-line','marker-end':'url(#arrow)'});const hit=el('line',{class:'edge-hit',tabindex:0,role:'button','aria-label':`${edge.subject} ${edge.predicate} ${edge.object}`});const label=el('text',{class:'edge-label','text-anchor':'middle'},edge.predicate);
    group.append(line,hit,label);svg.append(group);group.addEventListener('click',()=>edgeEvidence(edge));hit.addEventListener('keydown',e=>{if(e.key==='Enter')edgeEvidence(edge);});edgeElements.push({edge,line,hit,label});
  }
  const nodeElements=[];
  for(const node of graph.nodes){
    const g=el('g',{class:`graph-node ${node.type==='Service'?'service':''}`,tabindex:0,role:'button','aria-label':node.label});
    g.append(el('circle',{r:48}),el('text',{'text-anchor':'middle',y:-1},node.label.split(' ').slice(0,-1).join(' ')),el('text',{'text-anchor':'middle',y:15,class:'type'},node.type.toUpperCase()));
    svg.append(g);nodeElements.push({node,g});
    g.addEventListener('click',()=>{document.querySelectorAll('.graph-node').forEach(n=>n.classList.remove('selected'));g.classList.add('selected');const edge=graph.edges.find(e=>e.source===node.id||e.target===node.id);if(edge)edgeEvidence(edge);});
    g.addEventListener('pointerdown',event=>{g.setPointerCapture(event.pointerId);const move=e=>{const matrix=svg.getScreenCTM();const point=new DOMPoint(e.clientX,e.clientY).matrixTransform(matrix.inverse());positions.set(node.id,{x:Math.min(810,Math.max(60,point.x)),y:Math.min(545,Math.max(55,point.y))});redraw();};const up=()=>{g.removeEventListener('pointermove',move);g.removeEventListener('pointerup',up);};g.addEventListener('pointermove',move);g.addEventListener('pointerup',up);});
  }
  function redraw(){for(const{node,g}of nodeElements){const p=positions.get(node.id);g.setAttribute('transform',`translate(${p.x},${p.y})`);}for(const{edge,line,hit,label}of edgeElements){const a=positions.get(edge.source),b=positions.get(edge.target);const dx=b.x-a.x,dy=b.y-a.y,len=Math.max(1,Math.hypot(dx,dy));const attrs={x1:a.x+dx/len*49,y1:a.y+dy/len*49,x2:b.x-dx/len*53,y2:b.y-dy/len*53};for(const[k,v]of Object.entries(attrs)){line.setAttribute(k,v);hit.setAttribute(k,v);}const fraction=edge.source===central.id||edge.target===central.id?0.5:0.3;label.setAttribute('x',a.x+(b.x-a.x)*fraction);label.setAttribute('y',a.y+(b.y-a.y)*fraction-8);}}
  redraw(); const initial=graph.edges.find(e=>e.predicate==='MANAGED_BY')||graph.edges[0]; if(initial)edgeEvidence(initial);
}
async function search(event){
  if(event)event.preventDefault();const button=$('#search-form button');button.disabled=true;message('');
  try{
    const response=await api('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('#question').value,method:$('#retrieval-method').value,k:5})});const t=response.trace;
    $('#search-results').innerHTML=`<div class="answer-card"><span class="eyebrow">${t.answers.length?'EVIDENCE-PATH ANSWER':'ABSTAINED / NO SUPPORTED ANSWER'}</span><h3>${esc(t.message)}</h3><div class="path-row">${t.path.map(p=>`<code>${esc(p)}</code>`).join('<span>&rarr;</span>')}<span class="muted">${t.edges.length} evidence link(s)</span></div><p class="small muted" style="margin-bottom:0">Deterministic graph trace; not LLM-generated. ${response.method==='lexical'?'This trace is separate from the TF-IDF ranking shown below.':''}</p></div><div class="section-heading"><h3>Retrieved source evidence</h3><span class="muted small">${esc(response.method)} ranking &middot; ${response.milliseconds.toFixed(1)} ms on this request</span></div>${response.results.map((r,i)=>`<article class="card result-card"><div class="result-rank">${i+1}</div><div class="result-body"><small>${esc(r.filename)} / PAGE ${r.page}</small><p>${esc(r.text)}</p><button class="text-button" data-open-document="${esc(r.document_id)}" data-page="${r.page}">Open original evidence &rarr;</button></div><div class="result-meta">${r.graph_support?'<span class="tag">ON EVIDENCE PATH</span>':'<span class="tag neutral">LEXICAL MATCH</span>'}<div>Ranking score ${r.score.toFixed(3)}</div></div></article>`).join('')}`;
  }catch(error){message(error.message,true);}finally{button.disabled=false;}
}
async function loadEvaluation(){
  const m=await api('/api/evaluations');const p=n=>(n*100).toFixed(1)+'%';
  $('#evaluation-content').innerHTML=`<div class="notice"><strong>Synthetic pilot, not a generalization claim.</strong> The standard test shares phrasing families with training. The unseen-paraphrase slice is harder, and the classical model performs better there.</div><div class="eval-grid"><article class="card"><div class="section-heading"><h3>Required evidence recovered</h3><span class="tag">RECALL@5</span></div><p class="muted small">54 answerable questions / 9 held-out source documents</p>${['lexical','graph'].map(k=>`<div class="comparison-row"><div><span class="method-label">${k==='lexical'?'TF-IDF lexical baseline':'Ontology-guided graph + TF-IDF'}</span><br><span class="metric-badge">Document-bootstrap 95% CI: ${m.retrieval[k].recall_at_5_ci95_document_bootstrap.map(p).join(' - ')}</span></div><strong>${p(m.retrieval[k].recall_at_5)}</strong></div>`).join('')}<p class="muted small">A perfect interval on a small, schema-aligned benchmark is not evidence of real-world certainty.</p></article><article class="card"><div class="section-heading"><h3>Relation classification</h3><span class="tag neutral">MACRO F1</span></div><table><thead><tr><th>METHOD</th><th>STANDARD TEST</th><th>UNSEEN PHRASING</th></tr></thead><tbody>${['rules','logistic','neural'].map(k=>`<tr><td>${{rules:'Rule baseline',logistic:'TF-IDF + logistic',neural:'BiLSTM'}[k]}</td><td>${m.relation_classification[k].test.macro_f1.toFixed(3)}</td><td>${m.relation_classification[k].paraphrase_stress.macro_f1.toFixed(3)}</td></tr>`).join('')}</tbody></table><p class="muted small">90 standard test statements; 72 positive paraphrase-stress statements. BiLSTM was selected on dev data only.</p></article><article class="card"><h3>Image-only OCR smoke test</h3><div class="comparison-row"><span>Character error rate</span><strong>${p(m.ocr.character_error_rate)}</strong></div><div class="comparison-row"><span>Word error rate</span><strong>${p(m.ocr.word_error_rate)}</strong></div><p class="muted small">4 derived pages; clean and mildly degraded scans. Native text was empty on all four. One Tesseract batch.</p></article><article class="card"><h3>Answer support and abstention</h3><div class="comparison-row"><span>Exact supported endpoint</span><strong>${p(m.answers.exact_match)}</strong></div><div class="comparison-row"><span>Unsupported-question abstention</span><strong>${p(m.answers.unanswerable_abstention)}</strong></div><p class="muted small">54 answerable and 9 unanswerable questions. Handcrafted query planning; no human usability study.</p></article></div>`;
}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
$('#overview-demo').addEventListener('click',()=>showView('documents'));
$('#try-question').addEventListener('click',async()=>{await showView('search');await search();});
$('#doc-filter').addEventListener('input',drawDocumentList);
$('#documents-list').addEventListener('click',e=>{const b=e.target.closest('[data-doc]');if(b)selectDocument(b.dataset.doc).catch(error=>message(error.message,true));});
$('#upload').addEventListener('change',e=>upload(e.target.files[0]));
$('#refresh-graph').addEventListener('click',()=>loadGraph().catch(error=>message(error.message,true)));
$('#search-form').addEventListener('submit',search);
document.addEventListener('click',async e=>{const button=e.target.closest('[data-open-document]');if(button){selectedDocument=button.dataset.openDocument;selectedPage=Number(button.dataset.page)||1;await showView('documents');}});
loadStatus().catch(error=>message(error.message,true));
