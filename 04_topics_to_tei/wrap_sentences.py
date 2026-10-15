# -*- coding: utf-8 -*-
"""
Wrap every sentence of lesefassung_nlp_resolved.xml in a bare, addressable
<s xml:id="sN">...</s> - no topic info on the element itself - and record
the BERTopic assignments separately, as stand-off spans

"""
import json
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
PUB_DIR = HERE.parent

XML_PATH = PUB_DIR / "01_preprocessing" / "output" / "lesefassung_nlp_resolved.xml"
DOC_INFO_PATH = PUB_DIR / "02_bertopic" / "output" / "bertopic_results_with_paragraphs_schwerin_final_2026-09-27.json"
OUT_PATH = HERE / "output" / "tei_with_topics_2026-09-27_standoff.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

RUN_ID = "bertopic_2026-09-27"
RUN_DATE = "2026-09-27"
RUN_DESC = ("BERTopic 0.17.4; Embeddings: paraphrase-multilingual-MiniLM-L12-v2; "
            "UMAP n_neighbors=15, n_components=5, min_dist=0.0, metric=cosine; "
            "HDBSCAN min_cluster_size=10, metric=euclidean, cluster_selection_method=eom; "
            "random_state=42; Analyseeinheit: Satz. "
            "Textgrundlage: lesefassung_nlp_resolved.xml (teiHeader, <note>, "
            "<certainty> ausgeschlossen; Apparat auf eine Lesart reduziert, "
            "#W bevorzugt sonst #A).")


def q(local):
    return f"{{{TEI_NS}}}{local}"


def add_header_declarations(root):
    """Add <appInfo><application> to <encodingDesc>, idempotently (skip if
    already present).

    Topic references use full absolute GAMS URIs, like @ana/@ref elsewhere
    in the edition (persons, places, timeline, subjects) - no <prefixDef>."""
    encoding_desc = root.find(f".//{q('encodingDesc')}")
    assert encoding_desc is not None, "no <encodingDesc> found"

    if encoding_desc.find(f"{q('appInfo')}/{q('application')}[@{{{XML_NS}}}id='{RUN_ID}']") is None:
        app_info = encoding_desc.find(q("appInfo"))
        if app_info is None:
            app_info = etree.SubElement(encoding_desc, q("appInfo"))
        application = etree.SubElement(app_info, q("application"))
        application.set(f"{{{XML_NS}}}id", RUN_ID)
        application.set("ident", "BERTopic")
        application.set("version", "0.17.4")
        application.set("when", RUN_DATE)
        label = etree.SubElement(application, q("label"))
        label.text = "BERTopic, Satzebene"
        desc = etree.SubElement(application, q("desc"))
        desc.text = RUN_DESC


def wrap_paragraph(p, n_sentences):
    """Replace <milestone unit="sentence"/>-delimited runs in <p> with
    bare <s> elements (ids assigned by the caller). Returns the list of
    new <s> elements in order, or None if the milestone count doesn't
    match n_sentences (paragraph left untouched in that case)."""
    ms_tag = q("milestone")
    children = list(p)
    n_ms = sum(1 for c in children if c.tag == ms_tag and c.get("unit") == "sentence")
    if n_ms != n_sentences:
        return None

    new_children = []
    current_s = None

    for child in children:
        if child.tag == ms_tag and child.get("unit") == "sentence":
            s_el = etree.Element(q("s"))
            s_el.text = child.tail
            current_s = s_el
            new_children.append(s_el)
        else:
            current_s.append(child)  # moves child (and its tail) from p to current_s

    p[:] = new_children
    return new_children


def main():
    parser = etree.XMLParser(remove_blank_text=False, huge_tree=True, recover=True)
    tree = etree.parse(str(XML_PATH), parser)
    root = tree.getroot()
    text_el = root.find(q("text"))
    tei_header = root.find(q("teiHeader"))
    assert text_el is not None and tei_header is not None

    add_header_declarations(root)

    doc_info = json.load(open(DOC_INFO_PATH, encoding="utf-8"))
    by_para = {}
    for r in doc_info:
        by_para.setdefault(r["Paragraph"], []).append(r)

    spans = []  # (s_xml_id, topic, prob)
    id_counter = [1]
    n_paras_ok = n_paras_skipped = 0
    n_sent_skipped = 0

    for p in text_el.iter(q("p")):
        pid = p.get(f"{{{XML_NS}}}id")
        if not pid or not pid.startswith("P."):
            continue
        n = int(pid.split(".")[1])
        entries = by_para.get(n, [])
        new_s = wrap_paragraph(p, len(entries))
        if new_s is None:
            n_paras_skipped += 1
            n_sent_skipped += len(entries)
            print(f"  SKIPPED {pid}: milestone/JSON sentence count mismatch, left as milestones")
            continue
        n_paras_ok += 1
        for s_el, entry in zip(new_s, entries):
            sid = f"s{id_counter[0]}"
            id_counter[0] += 1
            s_el.set(f"{{{XML_NS}}}id", sid)
            spans.append((sid, entry["Topic"], entry.get("Probability") or 0.0))

    # ---- build <standOff><spanGrp> and insert right after </teiHeader> ----
    stand_off = etree.Element(q("standOff"))
    span_grp = etree.SubElement(stand_off, q("spanGrp"))
    span_grp.set("type", "topicAssignment")
    span_grp.set("resp", f"#{RUN_ID}")
    for sid, topic, prob in spans:
        span = etree.SubElement(span_grp, q("span"))
        span.set("target", f"#{sid}")
        span.set("ana", f"https://gams.uni-graz.at/o:mgs.topics#T{topic}")
        if topic != -1:
            span.set("cert", f"{prob:.2f}")
    tei_header.addnext(stand_off)

    OUT_PATH.parent.mkdir(exist_ok=True)
    tree.write(str(OUT_PATH), encoding="UTF-8", xml_declaration=True)

    print(f"\nBERTopic sentences: {len(doc_info)}")
    print(f"paragraphs wrapped: {n_paras_ok}, skipped: {n_paras_skipped} ({n_sent_skipped} sentences not written)")
    print(f"<s> elements: {len(spans)}")
    print(f"<span> assertions: {len(spans)} (incl. {sum(1 for _,t,_ in spans if t == -1)} outliers)")
    print(f"written: {OUT_PATH}")


if __name__ == "__main__":
    main()
