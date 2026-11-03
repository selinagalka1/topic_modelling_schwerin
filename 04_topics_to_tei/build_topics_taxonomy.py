# -*- coding: utf-8 -*-
"""
Build a TEI-native topic taxonomy (<classDecl><taxonomy><category>...),
published as its own standalone TEI document, so that the URIs used in
the stand-off spans of tei_with_topics_2026-09-27_standoff.xml
(https://gams.uni-graz.at/o:mgs.topics#T1) resolve to the fragment of
THIS file with xml:id="T1".

"""
import html
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PUB_DIR = HERE.parent

TOPIC_INFO = PUB_DIR / "03_topic_labels" / "topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json"
# Labels of the subject headings of the edition (o:mgs.subjects on GAMS,
# https://gams.uni-graz.at/o:mgs.subjects/ONTOLOGY), used as link text.
SUBJECT_LABELS = {
    "S1": "Essen",
    "S2": "Reisen",
    "S3": "Natur",
    "S4": "Mode",
    "S5": "Feste",
    "S6": "Gebete",
    "S7": "theologische Sachverhalte",
    "S8": "Krankheit und Medizin",
    "S9": "Schwangerschaft und Geburt",
    "S10": "Geld und Vermögen",
}
OUT_PATH = HERE / "output" / "topics.xml"
SUBJECT_URI = "https://gams.uni-graz.at/o:mgs.subjects#"

RUN_ID = "bertopic_2026-09-27"
RUN_DATE = "2026-09-27"
# Editorial assessment of a topic ("Display" in the labelled topic info):
# "meaningful" if its sentences share a clearly nameable theme, "limited" if
# it is unclear, its terms are very general, or it is tied to single persons
# or episodes and hardly understandable without further explanation. The
# edition highlights the meaningful topics in its interface.
ASSESSMENT_SUBTYPE = {"yes": "meaningful", "no": "limited"}
ASSESSMENT_TEXT = {
    "yes": "Die Sätze dieses Topics teilen ein klar benennbares Thema.",
    "no": "Dieses Topic ist unklar, seine charakteristischen Begriffe sind sehr allgemein, "
          "oder es ist an einzelne Personen oder Episoden gebunden und ohne weitere Erläuterung "
          "kaum verständlich.",
}


def esc(s):
    return html.escape(str(s), quote=True)


def build_category(t, labels, subject_labels):
    tid = t["Topic"]
    terms = [w for w in t.get("Representation", []) if str(w).strip()]
    weights = {}
    for w, v in t.get("Terms_with_Weights", []):
        weights.setdefault(w, v)
    label = (t.get("Label") or "").strip()
    count = t.get("Count")
    display = t["Display"]

    provisional = not label
    gloss_resp = f"#{RUN_ID}" if provisional else "#labelling"
    if provisional:
        label = " / ".join(terms[:3]) if terms else f"Topic {tid}"

    lines = [f'      <category xml:id="T{tid}">',
             f'         <gloss resp="{gloss_resp}">{esc(label)}</gloss>']
    if terms:
        term_str = " ".join(
            f'<term n="{weights[w]:.4f}">{esc(w)}</term>' if w in weights else f"<term>{esc(w)}</term>"
            for w in terms[:10])
        lines.append(f'         <desc type="representation" resp="#{RUN_ID}">{term_str}</desc>')
    lines.append(f'         <desc type="scope" resp="#{RUN_ID}"><num value="{count}">{count}</num> Sätze</desc>')
    lines.append(f'         <desc type="assessment" subtype="{ASSESSMENT_SUBTYPE[display]}" resp="#editors">'
                 f'{esc(ASSESSMENT_TEXT[display])}</desc>')
    similar = t.get("Similar_topics") or []
    if similar:
        refs = ", ".join(f'<ref target="#T{sid}">{esc(labels[sid])}</ref>' for sid in similar)
        lines.append(f'         <desc type="similar" resp="#editors">Ähnliche oder verwandte Topics: {refs}</desc>')
    subjects = t.get("Subjects") or []
    if subjects:
        refs = ", ".join(f'<ref target="{SUBJECT_URI}{sid}">{esc(subject_labels[sid])}</ref>' for sid in subjects)
        heading = "Verwandtes Schlagwort" if len(subjects) == 1 else "Verwandte Schlagwörter"
        lines.append(f'         <desc type="subject" resp="#editors">{heading}: {refs}</desc>')
    if provisional:
        lines.append(f'         <desc type="review" resp="#{RUN_ID}">noch nicht redaktionell benannt</desc>')
    lines.append('      </category>')
    return "\n".join(lines), provisional, display == "yes"


def main():
    topic_info = json.load(open(TOPIC_INFO, encoding="utf-8"))
    real_topics = sorted([t for t in topic_info if t["Topic"] != -1], key=lambda t: t["Topic"])

    subject_labels = SUBJECT_LABELS
    labels = {t["Topic"]: (t.get("Label") or "").strip() or f"Topic {t['Topic']}" for t in real_topics}

    n_labelled = n_provisional = n_display = 0
    categories = []
    for t in real_topics:
        xml, provisional, display = build_category(t, labels, subject_labels)
        categories.append(xml)
        n_provisional += provisional
        n_labelled += not provisional
        n_display += display

    categories.append('      <category xml:id="T-1">\n'
                      '         <catDesc>Ausreißer (kein Topic zugewiesen)</catDesc>\n'
                      '      </category>')

    out = f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
   <teiHeader>
      <fileDesc>
         <titleStmt>
            <title>Topic-Taxonomie (BERTopic) der digitalen Edition der Memoiren der Gr&#228;fin Schwerin (1684-1732)</title>
            <respStmt xml:id="labelling">
               <resp>Benennung der Topics</resp>
               <persName>
                  <forename>Selina</forename>
                  <surname>Galka</surname>
               </persName>
            </respStmt>
            <respStmt xml:id="editors">
               <resp>Redaktionelle Prüfung und Kuratierung der Topics</resp>
               <persName>
                  <forename>Selina</forename>
                  <surname>Galka</surname>
               </persName>
               <persName>
                  <forename>Ines</forename>
                  <surname>Peper</surname>
               </persName>
               <persName>
                  <forename>Michael</forename>
                  <surname>P&#246;lzl</surname>
               </persName>
            </respStmt>
         </titleStmt>
         <publicationStmt>
            <publisher>
               <orgName corresp="https://www.oeaw.ac.at/ihb/home" ref="https://d-nb.info/gnd/1202798799">Institut f&#252;r die Erforschung der Habsburgermonarchie und des Balkanraumes</orgName>
               <country>Austria</country>
            </publisher>
            <authority>
               <orgName ref="http://d-nb.info/gnd/1137284463" corresp="https://informationsmodellierung.uni-graz.at">Institut f&#252;r Digitale Geisteswissenschaften</orgName>
               <country>Austria</country>
            </authority>
            <distributor>
               <orgName ref="https://gams.uni-graz.at">GAMS - Geisteswissenschaftliches Asset Management System</orgName>
            </distributor>
            <availability>
               <licence target="https://creativecommons.org/licenses/by-nc/4.0">Creative Commons BY-NC 4.0</licence>
            </availability>
            <date when="2026">2026</date>
            <pubPlace>Graz</pubPlace>
            <idno type="PID">o:mgs.topics</idno>
         </publicationStmt>
         <sourceDesc>
            <p>Automatisch generierte Topics (BERTopic) der Lesefassung der digitalen Edition;
               {len(real_topics)} Topics, davon {n_labelled} redaktionell benannt und {n_provisional} vorl&#228;ufig (Repr&#228;sentationsw&#246;rter
               als Label). {n_display} Topics sind redaktionell als aussagekr&#228;ftig eingesch&#228;tzt und werden
               in der Edition hervorgehoben (siehe &lt;desc type="assessment"&gt;, @subtype
               "meaningful" bzw. "limited").</p>
         </sourceDesc>
      </fileDesc>
      <encodingDesc>
         <appInfo>
            <application xml:id="{RUN_ID}" ident="BERTopic" version="0.17.4" when="{RUN_DATE}">
               <label>BERTopic, Satzebene</label>
               <desc>Embeddings: paraphrase-multilingual-MiniLM-L12-v2; UMAP n_neighbors=15,
                  n_components=5, min_dist=0.0, metric=cosine; HDBSCAN min_cluster_size=10,
                  metric=euclidean, cluster_selection_method=eom; random_state=42;
                  Analyseeinheit: Satz. Textgrundlage: lesefassung_nlp_resolved.xml (teiHeader,
                  &lt;note&gt;, &lt;certainty&gt; ausgeschlossen; Apparat auf eine Lesart reduziert,
                  #W bevorzugt sonst #A). Topic-Repr&#228;sentation: c-TF-IDF, zehn Terme je Topic,
                  nach dem Training neu berechnet mit der franz&#246;sischen Stoppwortliste des NLTK,
                  erg&#228;nzt um 39 Eintr&#228;ge (Funktionsw&#246;rter, Personennamen, Anreden und Titel);
                  die Zuweisung der S&#228;tze bleibt davon unber&#252;hrt. Zuordnungswerte:
                  Zugeh&#246;rigkeitsst&#228;rke nach HDBSCAN (calculate_probabilities=False).</desc>
            </application>
         </appInfo>
         <classDecl>
            <taxonomy xml:id="mgs-topics">
               <desc>Topics des Topic Modelling der Lesefassung (BERTopic, Lauf vom 27.09.2026; Modell
                  und Parameter: <ref target="#{RUN_ID}">application {RUN_ID}</ref>):
                  {len(real_topics)} Topics f&#252;r 10.039 S&#228;tze, davon 4.034 ohne Topic (Kategorie T-1).
                  Terme, Gewichte und Satzzahlen stammen aus dem Modell, Bezeichnungen,
                  Einsch&#228;tzung der Aussagekraft und Verkn&#252;pfungen von den Herausgeber*innen.</desc>
{chr(10).join(categories)}
            </taxonomy>
         </classDecl>
      </encodingDesc>
   </teiHeader>
   <text>
      <body>
         <p>Diese Datei enth&#228;lt ausschlie&#223;lich die Taxonomie-Deklaration im teiHeader
            (&lt;classDecl&gt;); keinen fortlaufenden Text.</p>
      </body>
   </text>
</TEI>
"""
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(out, encoding="utf-8")
    print(f"categories written: {len(real_topics) + 1} ({len(real_topics)} topics + T-1)")
    print(f"labelled: {n_labelled}, provisional: {n_provisional}, meaningful: {n_display}")
    print(f"output: {OUT_PATH} ({len(out):,} chars)")


if __name__ == "__main__":
    main()
