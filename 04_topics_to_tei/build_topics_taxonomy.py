# -*- coding: utf-8 -*-
"""
Build the topic taxonomy as a standalone TEI document (output/topics.xml).

Every topic becomes one <category xml:id="T…"> inside
<classDecl><taxonomy>. The stand-off file of this step
(tei_with_topics_2026-09-27_standoff.xml) refers to the topics with URIs
such as https://gams.uni-graz.at/o:mgs.topics#T1; on GAMS, these URIs lead
to the category with xml:id="T1" in this file.

Each category contains
    <gloss>                      the label given by the editors
    <desc type="representation"> the ten most characteristic terms of the
                                 topic with their c-TF-IDF weights in @n
    <desc type="scope">          the number of sentences of the topic
    <desc type="assessment">     the editorial assessment: meaningful or limited
    <desc type="related">        related topics (only where there are any)
    <desc type="subject">        related subject headings of the edition
                                 (only where there are any)
@resp says who made each statement: the model run (#bertopic_2026-09-27),
the person who labelled the topics (#labelling) or the editors (#editors).

Input
    ../03_topic_labels/topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json
Output
    output/topics.xml

Run:  python build_topics_taxonomy.py
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
# Editorial assessment of a topic ("Assessment" in the labelled topic info):
# "meaningful" if its sentences share a clearly nameable theme, "limited" if
# it is unclear, its terms are very general, or it is tied to single persons
# or episodes and hardly understandable without further explanation. The
# edition highlights the meaningful topics in its interface.
ASSESSMENT_TEXT = {
    "meaningful": "Die Sätze dieses Topics teilen ein klar benennbares Thema.",
    "limited": "Dieses Topic ist unklar, seine charakteristischen Begriffe sind sehr allgemein, "
          "oder es ist an einzelne Personen oder Episoden gebunden und ohne weitere Erläuterung "
          "kaum verständlich.",
}


def esc(text):
    """Escape characters such as & and < so that the text is valid XML."""
    return html.escape(str(text), quote=True)


def build_category(topic, labels, subject_labels):
    """Return the <category> element of one topic as XML text, plus two
    flags: whether the topic has no editorial label yet, and whether it is
    assessed as meaningful."""
    topic_id = topic["Topic"]

    # The ten most characteristic terms of the topic (empty entries removed)
    terms = []
    for term in topic.get("Representation", []):
        if str(term).strip():
            terms.append(term)

    # c-TF-IDF weight of each term (if a term occurs twice, the first weight counts)
    weights = {}
    for term, weight in topic.get("Terms_with_Weights", []):
        if term not in weights:
            weights[term] = weight

    label = (topic.get("Label") or "").strip()
    count = topic.get("Count")
    assessment = topic["Assessment"]  # "meaningful" or "limited"

    # A topic without an editorial label gets its first three terms as a
    # provisional label, attributed to the model run instead of a person.
    provisional = not label
    if provisional:
        gloss_resp = f"#{RUN_ID}"
        label = " / ".join(terms[:3]) if terms else f"Topic {topic_id}"
    else:
        gloss_resp = "#labelling"

    lines = [f'      <category xml:id="T{topic_id}">',
             f'         <gloss resp="{gloss_resp}">{esc(label)}</gloss>']

    # Terms with their weights, e.g. <term n="0.2578">fièvre</term>
    if terms:
        term_elements = []
        for term in terms[:10]:
            if term in weights:
                term_elements.append(f'<term n="{weights[term]:.4f}">{esc(term)}</term>')
            else:
                term_elements.append(f"<term>{esc(term)}</term>")
        lines.append(f'         <desc type="representation" resp="#{RUN_ID}">{" ".join(term_elements)}</desc>')

    # Number of sentences
    lines.append(f'         <desc type="scope" resp="#{RUN_ID}"><num value="{count}">{count}</num> Sätze</desc>')

    # Editorial assessment
    lines.append(f'         <desc type="assessment" subtype="{assessment}" resp="#editors">'
                 f'{esc(ASSESSMENT_TEXT[assessment])}</desc>')

    # Related topics, each as a link to its category
    similar = topic.get("Similar_topics") or []
    if similar:
        refs = []
        for other_id in similar:
            refs.append(f'<ref target="#T{other_id}">{esc(labels[other_id])}</ref>')
        lines.append(f'         <desc type="related" resp="#editors">Ähnliche oder verwandte Topics: {", ".join(refs)}</desc>')

    # Related subject headings, each as a link to the subject heading on GAMS
    subjects = topic.get("Subjects") or []
    if subjects:
        refs = []
        for subject_id in subjects:
            refs.append(f'<ref target="{SUBJECT_URI}{subject_id}">{esc(subject_labels[subject_id])}</ref>')
        heading = "Verwandtes Schlagwort" if len(subjects) == 1 else "Verwandte Schlagwörter"
        lines.append(f'         <desc type="subject" resp="#editors">{heading}: {", ".join(refs)}</desc>')

    if provisional:
        lines.append(f'         <desc type="review" resp="#{RUN_ID}">noch nicht redaktionell benannt</desc>')

    lines.append('      </category>')
    return "\n".join(lines), provisional, assessment == "meaningful"


def main():
    # ---- 1. Load the curated topics ------------------------------------------

    with open(TOPIC_INFO, encoding="utf-8") as f:
        topic_info = json.load(f)

    # All topics except the outliers (-1), in numerical order
    real_topics = [topic for topic in topic_info if topic["Topic"] != -1]
    real_topics.sort(key=lambda topic: topic["Topic"])

    subject_labels = SUBJECT_LABELS

    # Label of every topic, used as link text for related topics
    labels = {}
    for topic in real_topics:
        labels[topic["Topic"]] = (topic.get("Label") or "").strip() or f"Topic {topic['Topic']}"

    # ---- 2. Build one <category> per topic -----------------------------------

    n_labelled = n_provisional = n_display = 0
    categories = []
    for topic in real_topics:
        xml, provisional, meaningful = build_category(topic, labels, subject_labels)
        categories.append(xml)
        if provisional:
            n_provisional += 1
        else:
            n_labelled += 1
        if meaningful:
            n_display += 1

    # The outliers get their own category without a label
    categories.append('      <category xml:id="T-1">\n'
                      '         <catDesc>Ausreißer (kein Topic zugewiesen)</catDesc>\n'
                      '      </category>')

    # ---- 3. Put the categories into a complete TEI document and write it ----

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
