import pytest
from pathlib import Path
from docweave.schema import normalize, entity_key, entities, masked, Chunk, make_triple
from docweave.extractors import RuleExtractor, get_extractor
from docweave.adapters import validate_llm_triples, OllamaExtractor

def chunk(text): return Chunk("c1","d1",1,text,"native")

def test_normalization(): assert normalize(" A\n B\tC ")=="A B C"
def test_unicode_entity_key(): assert entity_key("\uff21tlas40  Service")=="atlas40 service"
def test_entities(): assert entities("Atlas40 Service is managed by Cedar40 Team.")==["Atlas40 Service","Cedar40 Team"]
def test_duration(): assert entities("Granite40 Archive retains records for 70 days.")==["Granite40 Archive","70 days"]
def test_masking_hides_identity(): assert masked("Atlas40 Service uses Shield40 Protocol.")==masked("Atlas01 Service uses Shield01 Protocol.")
def test_rule_direction():
    t=RuleExtractor().extract(chunk("Cedar40 Team manages Atlas40 Service."))[0]
    assert (t.subject,t.predicate,t.object)==("Atlas40 Service","MANAGED_BY","Cedar40 Team")
@pytest.mark.parametrize("text",["Atlas40 Service does not use Shield40 Protocol.","Atlas40 Service may use Shield40 Protocol.","Atlas40 Service never uses Shield40 Protocol."])
def test_rule_rejects_nonaffirmative(text): assert RuleExtractor().extract(chunk(text))==[]
def test_ambiguous_endpoint_rejected(): assert make_triple(chunk("Atlas40 Service and Atlas41 Service use Shield40 Protocol."),"USES",1.,"test") is None
def test_unknown_relation_rejected(): assert make_triple(chunk("Atlas40 Service uses Shield40 Protocol."),"INVENTED",1.,"test") is None
def test_unknown_extractor():
    with pytest.raises(ValueError): get_extractor("unknown",Path("."))
def test_llm_grounded_quote():
    c=chunk("Atlas40 Service uses Shield40 Protocol.")
    payload={"triples":[{"subject":"Atlas40 Service","predicate":"USES","object":"Shield40 Protocol","quote":c.text}]}
    result=validate_llm_triples(c,payload)
    assert len(result)==1 and result[0].method=="ollama_unreviewed"
def test_llm_invented_quote_rejected():
    c=chunk("Atlas40 Service uses Shield40 Protocol.")
    payload={"triples":[{"subject":"Atlas40 Service","predicate":"USES","object":"Other Protocol","quote":"Atlas40 Service uses Other Protocol."}]}
    assert validate_llm_triples(c,payload)==[]
def test_llm_schema_failure():
    with pytest.raises(ValueError): validate_llm_triples(chunk("text"),{"wrong":[]})
def test_llm_duplicates_removed():
    c=chunk("Atlas40 Service uses Shield40 Protocol."); row={"subject":"Atlas40 Service","predicate":"USES","object":"Shield40 Protocol","quote":c.text}
    assert len(validate_llm_triples(c,{"triples":[row,row]}))==1
@pytest.mark.parametrize("endpoint",["https://example.com","http://192.168.1.5:11434","file:///etc/passwd"])
def test_llm_remote_endpoint_rejected(endpoint):
    with pytest.raises(ValueError): OllamaExtractor(endpoint)
def test_llm_bad_field_type_rejected():
    assert validate_llm_triples(chunk("Atlas40 Service uses Shield40 Protocol."),{"triples":[{"subject":5}]})==[]
