# -*- coding: utf-8 -*-
"""
Publish the topic taxonomy additionally as a SKOS concept scheme, in the
same format as the subject headings of the edition (o:mgs.subjects), so
that topics and subject headings can be used together as Linked Data.

"""
import json
from pathlib import Path
from xml.sax.saxutils import escape as esc

HERE = Path(__file__).resolve().parent
PUB_DIR = HERE.parent
TOPIC_INFO = PUB_DIR / "03_topic_labels" / "topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json"
OUT_PATH = HERE / "output" / "topics_skos.xml"

BASE = "https://gams.uni-graz.at/o:mgs.topics"
SUBJECTS = "https://gams.uni-graz.at/o:mgs.subjects"
OUTLIER_LABEL = "Ausreißer (kein Topic zugewiesen)"

HEADER = f'''<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:dct="http://purl.org/dc/terms/"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:skos="http://www.w3.org/2004/02/skos/core#">
   <skos:ConceptScheme rdf:about="{BASE}">
      <dc:title xml:lang="de">Topics (BERTopic)</dc:title>
      <dc:relation>Digitale Edition der Memoiren der Gräfin Schwerin (1684-1732)</dc:relation>
      <dc:relation>https://gams.uni-graz.at/context:mgs</dc:relation>
      <dc:publisher>Institut für Digitale Geisteswissenschaften, Karl-Franzens-Universität Graz</dc:publisher>
      <dc:publisher rdf:resource="http://d-nb.info/gnd/1137284463"/>
      <dc:publisher>Institut für die Erforschung der Habsburgermonarchie und des Balkanraumes, Österreichische Akademie der Wissenschaften</dc:publisher>
      <dc:publisher rdf:resource="https://d-nb.info/gnd/1202798799"/>
      <dc:identifier>o:mgs.topics</dc:identifier>
      <dc:date>2026</dc:date>
      <dc:format>rdf+xml</dc:format>
      <dc:rights>Creative Commons BY-NC 4.0</dc:rights>
      <dc:rights rdf:resource="https://creativecommons.org/licenses/by-nc/4.0"/>
      <dc:description xml:lang="de">Topics des Topic Modelling (BERTopic, Lauf vom 27.09.2026, paraphrase-multilingual-MiniLM-L12-v2, min_cluster_size 10) auf Satzebene der Lesefassung, redaktionell benannt und kuratiert. Bezeichnungen, Verknüpfungen und Hervorhebung stammen von den Herausgeber*innen, Terme, Gewichte und Satzzahlen aus dem Modell. Die Zuweisung der Sätze steht als Stand-off im TEI (tei_with_topics_2026-09-27_standoff.xml); dieselben Topics als TEI-Taxonomie: topics.xml.</dc:description>
      <dc:language>de</dc:language>
      <dc:source>Topic-Taxonomie aus der digitalen Edition der Memoiren der Gräfin Schwerin, digital entstanden.</dc:source>
      <dc:coverage>Graz</dc:coverage>
   </skos:ConceptScheme>
'''


def as_list(v):
    if isinstance(v, list):
        return v
    if not v:
        return []
    return json.loads(v.replace("'", '"')) if isinstance(v, str) else [v]


def main():
    topics = {int(t["Topic"]): t for t in json.load(open(TOPIC_INFO, encoding="utf-8"))}
    out = [HEADER]
    displayed = []
    for tid in sorted(topics, key=lambda x: (x < 0, x)):
        t = topics[tid]
        uri = f"{BASE}#T{tid}"
        lines = [f'   <skos:Concept rdf:about="{uri}">',
                 f'      <skos:inScheme rdf:resource="{BASE}"/>']
        if tid == -1:
            lines.append(f'      <skos:prefLabel xml:lang="de">{esc(OUTLIER_LABEL)}</skos:prefLabel>')
            lines.append('   </skos:Concept>')
            out.extend(lines)
            continue
        terms = [w for w in as_list(t.get("Representation")) if str(w).strip()][:10]
        weights = {}
        for w, v in as_list(t.get("Terms_with_Weights")):
            weights.setdefault(w, v)
        label = (t.get("Label") or "").strip() or " / ".join(terms[:3]) or f"Topic {tid}"
        lines.append(f'      <skos:prefLabel xml:lang="de">{esc(label)}</skos:prefLabel>')
        if terms:
            tw = ", ".join(f"{w} ({weights[w]:.4f})" if w in weights else w for w in terms)
            lines.append(f'      <skos:note xml:lang="de">Repräsentative Terme (c-TF-IDF): {esc(tw)}</skos:note>')
        lines.append(f'      <skos:note xml:lang="de">{t["Count"]} Sätze</skos:note>')
        for sid in as_list(t.get("Similar_topics")):
            lines.append(f'      <skos:related rdf:resource="{BASE}#T{int(sid)}"/>')
        for subj in as_list(t.get("Subjects")):
            lines.append(f'      <skos:relatedMatch rdf:resource="{SUBJECTS}#{subj}"/>')
        lines.append('   </skos:Concept>')
        out.extend(lines)
        if t.get("Display") == "yes":
            displayed.append(uri)
    out.append(f'   <skos:Collection rdf:about="{BASE}#highlighted">')
    out.append('      <skos:prefLabel xml:lang="de">In der Edition hervorgehobene Topics</skos:prefLabel>')
    out.extend(f'      <skos:member rdf:resource="{u}"/>' for u in displayed)
    out.append('   </skos:Collection>')
    out.append('</rdf:RDF>\n')
    OUT_PATH.write_text("\n".join(out), encoding="utf-8")
    print(f"{len(topics)} concepts, {len(displayed)} highlighted -> {OUT_PATH}")


if __name__ == "__main__":
    main()
