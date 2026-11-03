# Topic Modelling of the Memoirs of Countess Schwerin (1684–1732)

This repository accompanies the article below. It contains the data, scripts and results of a sentence-level topic model (BERTopic) of the normalized reading text of the digital edition of the memoirs of Luise Charlotte von Schwerin. 

**Article:**
Selina Galka: Thematische Erschließung in digitalen Editionen. Manuelle Beschlagwortung und Topic Modelling am Beispiel der Memoiren der Gräfin Schwerin. In: Zeitschrift für digitale Geisteswissenschaften (in preparation).

**Edition:**
Selina Galka / Ines Peper / Michael Pölzl / Chiara Petrolini / Georg Vogeler / Joëlle Weis (Hg.): Digitale Edition der Memoiren der Gräfin Schwerin (1684–1732). Unter Mitarbeit von Sabine Amon. Wien / Graz 2026. [https://gams.uni-graz.at/context:mgs](https://gams.uni-graz.at/context:mgs)

## Pipeline

```
01_preprocessing   TEI edition → sentence-segmented TEI → plain text / resolved TEI
        │
02_bertopic        plain text → sentences → BERTopic model → topics per sentence
        │
03_topic_labels    editorial labels, assessment, related topics and subject headings
        │
04_topics_to_tei   topics → <s> + stand-off <span> in TEI, topic taxonomy in TEI

05_model_comparison      comparison runs: other embedding models, other min_cluster_size values
06_edition_survey        survey of thematic indexing in 26 digital editions
```

Steps 01–04 build on each other; 05 and 06 are supplementary.

## Repository structure

```
01_preprocessing/
├── input/lesefassung_2025_corrected.xml         TEI source text of the edition
├── scripts/
│   ├── 1_insert_milestones.xsl                 sentence boundaries → <milestone unit="sentence"/>
│   ├── 2_insert_milestone_in_app.xsl           sentence boundaries after <app>
│   ├── 3_tei_to_text.xsl                       TEI → plain text (/// = paragraph, ### = sentence)
│   ├── 3b_resolve_to_tei.xsl                   TEI with apparatus resolved to one reading
│   ├── Prepare_data_for_topic_modelling.ipynb  plain text → sentence list, validation
│   └── validation/count_milestones_per_paragraph.xsl
└── output/
    ├── lesefassung_milestones2.xml             full TEI with sentence annotation
    ├── lesefassung_nlp_resolved.xml            resolved TEI = exact text basis of the model
    └── sentences_for_bert_schwerin_2026_final.txt

02_bertopic/
├── Topic_modelling_with_BERT_sentences_2026_09_27.ipynb
├── requirements.txt
├── input/lesefassung.txt                       output of 3_tei_to_text.xsl
├── stopwords/stopwords_edited.txt              edited French stopword list
├── models/final_2026-09-27.mm                  fitted model (not in the Git repository, see below)
├── output/
│   ├── processed_sentences_lesefassung.txt
│   ├── topic_info_with_weights_output_schwerin_final_2026-09-27.json
│   ├── document_info_output_schwerin_final_2026-09-27.json
│   └── bertopic_results_with_paragraphs_schwerin_final_2026-09-27.json
└── barchart_visualization_schwerin_final_2026-09-27.html

03_topic_labels/
└── topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json   curated topics

04_topics_to_tei/
├── wrap_sentences.py
├── build_topics_taxonomy.py
└── output/
    ├── tei_with_topics_2026-09-27_standoff.xml
    └── topics.xml

05_model_comparison/
├── Topic_modelling_mpnet.ipynb
├── Topic_modelling_camembert.ipynb
└── output/
    ├── embedding_models/                       topic info and topic per sentence, mpnet and CamemBERT
    └── min_cluster_size/                       topic info and topic per sentence, min_cluster_size 5, 15, 20

06_edition_survey/
└── table_of_editions.md                        Table 1 of the article, full version (German)

```

## 01 Preprocessing

The source is the TEI/XML reading text as published in the beta version of the digital edition in March 2026. Where a passage survives in two witnesses, the text has a critical apparatus (`<app>` with `<rdg wit="#W">` and `<rdg wit="#A">`). W (Vienna, Haus-, Hof- und Staatsarchiv) is the base witness of the reading text. A is the manuscript in Aix-en-Provence (Bibliothèque Méjanes) on which the printed edition by Daumas/Ulbrich (2013) is based; it is used only where W does not contain the passage.

1. **`1_insert_milestones.xsl`** marks every sentence boundary (`.`, `!`, `?` followed by whitespace) with `<milestone unit="sentence"/>`. Single capital letters followed by a full stop (abbreviated names such as `H.`) are protected from splitting. Text inside `<note>` and `<certainty>` is not segmented. Inside the apparatus, only the W reading is segmented where both readings exist.
2. **`2_insert_milestone_in_app.xsl`** adds a sentence boundary directly after an `<app>` when its text ends a sentence and the following text starts with a capital letter.
3. **`3_tei_to_text.xsl`** produces the plain text used as model input. It excludes the `teiHeader`, `<note>` and `<certainty>`. Each `<app>` is resolved to one reading: W where both exist, otherwise the only (or first) reading. Paragraphs are delimited by `///` and sentences by `###`. The output is `02_bertopic/input/lesefassung.txt`.
4. **`3b_resolve_to_tei.xsl`** applies the same decisions as step 3 but keeps the TEI markup. `lesefassung_nlp_resolved.xml` therefore contains exactly the text the model saw.
5. **`Prepare_data_for_topic_modelling.ipynb`** splits the plain text into sentences, records the paragraph number of each sentence, and compares the number of sentences per paragraph with the number of milestones in the TEI.

The four stylesheets require an XSLT 2.0 processor (e.g. Saxon-HE or oXygen). Apply `1_insert_milestones.xsl` to `lesefassung_2025_corrected.xml`, `2_insert_milestone_in_app.xsl` to the result, and `3_tei_to_text.xsl` and `3b_resolve_to_tei.xsl` to the result of the second step (`lesefassung_milestones2.xml`).

## 02 BERTopic

The notebook was run in Google Colab (Python 3.13, T4 GPU). Package versions are pinned in `requirements.txt`.

| Component | Setting |
|---|---|
| BERTopic | 0.17.4, `language="french"` |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| UMAP | `n_neighbors=15`, `n_components=5`, `min_dist=0.0`, `metric="cosine"` |
| HDBSCAN | `min_cluster_size=10`, `metric="euclidean"`, `cluster_selection_method="eom"` |
| Random seed | 42 (Python, NumPy, PyTorch, UMAP) |
| Topic representation | `CountVectorizer` with `stopwords/stopwords_edited.txt` |

**Output files**

- `processed_sentences_lesefassung.txt`: all sentences with their paragraph numbers. The file is identical to `01_preprocessing/output/sentences_for_bert_schwerin_2026_final.txt`.
- `topic_info_with_weights_…json`: one entry per topic, with `Topic`, `Count`, `Name`, `Representation` (top ten words), `Representative_Docs` and `Terms_with_Weights` (c-TF-IDF weights).
- `document_info_…json`: one entry per sentence, with `Document` (the sentence), `Topic`, `Name`, `CustomName`, `Representation`, `Representative_Docs`, `Top_n_words`, `Probability` and `Representative_document`.
- `bertopic_results_with_paragraphs_…json`: the same as `document_info_…json`, plus `Paragraph`. The paragraph number *n* corresponds to `xml:id="P.n"` in the TEI.

## 03 Topic labels

`topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json` is the BERTopic topic info (`02_bertopic/output/topic_info_with_weights_…json`) with the editors' curation added. Every topic was given a German label by Selina Galka on the basis of its ten most relevant terms and up to 50 of its most probable sentences. The labels were then reviewed together with Ines Peper and Michael Pölzl. The three of them also assessed whether a topic is meaningful, i.e. whether its sentences share a clearly nameable theme (`Display`: `yes`), or of limited use because it is unclear, its terms are very general, or it is tied to single persons or episodes and hardly understandable without further explanation (`no`); the edition highlights the meaningful topics. They also linked topics that are similar or related in content to each other and to related subject headings of the edition ([`o:mgs.subjects`](https://gams.uni-graz.at/o:mgs.subjects/ONTOLOGY) on GAMS).

## 04 Topics in TEI

```
python wrap_sentences.py         # output/tei_with_topics_2026-09-27_standoff.xml
python build_topics_taxonomy.py  # output/topics.xml
```

- **`tei_with_topics_2026-09-27_standoff.xml`**: `lesefassung_nlp_resolved.xml` with every sentence in `<s xml:id="sN">` and the topic of each sentence as a stand-off `<span>`.
- **`topics.xml`**: the curated topics as a TEI taxonomy (`o:mgs.topics`): label, top terms with weights, sentence count, editorial assessment (`<desc type="assessment">` with `@subtype` `meaningful` or `limited`), related topics and subject headings. `@resp` distinguishes the labels (`#labelling`), the joint editorial decisions (`#editors`) and the model output (`#bertopic_2026-09-27`).

The data model is described in section 4.4 of the article.

## 05 Model comparison

This folder contains the data of the comparison runs with other embedding models (`paraphrase-multilingual-mpnet-base-v2`, `Lajavaness/sentence-camembert-large`; `output/embedding_models/`) and other values of `min_cluster_size` (5, 15, 20; `output/min_cluster_size/`). Everything else is the same as in the final model. Each run has its topic info and topic per sentence in the format of `02_bertopic`. The embedding runs were produced with the two notebooks in this folder, the `min_cluster_size` runs with the notebook in `02_bertopic`. Models and embeddings are not published, and the runs are not curated.

`Topic_modelling_paragraphs.ipynb` runs the final model on the 678 paragraphs instead of the sentences (otherwise identical; output in `output/paragraphs/`). The paragraphs are mostly longer than the 128 word pieces the embedding model reads, so the notebook reports how many are truncated and offers two strategies: truncation (default, as in a plain BERTopic run) or the mean of the sentence embeddings of each paragraph.

## 06 Edition survey

Full version of Table 1 of the article: how 26 digital editions model thematic indexing (subject headings, topics, themes) – unit of assignment, vocabulary, TEI modelling and links to example files. Editions 1–19 were selected from the Catalogue of Digital Editions (export of 2026-09-29, filtered by edition, scholarly, digital, TEI/XML and indices; 130 editions, 110 of them reachable); editions 20–26 were added from web searches and knowledge of the field. The article contains a shortened version of the table.

State of the survey: 2026-09-30 (editions 1–19) and 2026-10-03 (editions 20–26); websites and data may have changed since.

## Model file

`02_bertopic/models/final_2026-09-27.mm` (540 MB) exceeds GitHub's file size limit and is not part of the Git repository. TODO: add the link to where the model is archived.

## Licence

- **Code** (XSLT stylesheets, Python scripts, Jupyter notebooks): [MIT](LICENSE)
- **Data** (all other files): [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0), like the edition text from which they are derived (see its TEI header)

## Funding

Austrian Science Fund (FWF), grant DOI [10.55776/P34943](https://doi.org/10.55776/P34943).
