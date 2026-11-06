# -*- coding: utf-8 -*-
"""
Coherence check: draw a random sample of sentences for manual review.

For each of the 52 topics that the editors consider meaningful
("Assessment": "meaningful" in the curated topic file), the script picks 10 sentences
at random and writes them into a table. Each sentence is then checked by
hand: does it fit the label of its topic?

The sentences are drawn from all sentences of a topic, not only from those
with the highest assignment score, because the labels were given on the
basis of the top-scoring sentences.

The random seed is fixed (42), so running the script again draws exactly
the same sentences.

Input
    topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json
    ../02_bertopic/output/document_info_output_schwerin_final_2026-09-27.json
    ../02_bertopic/output/bertopic_results_with_paragraphs_schwerin_final_2026-09-27.json
Output
    coherence_check/coherence_sample.csv   (empty columns for the review)

The reviewed version of the table is coherence_check/coherence_sample_coded.csv.
Running the script does not change it.

Run:  python coherence_sample.py
"""
import csv
import json
import random
from pathlib import Path


# ---- Settings -------------------------------------------------------------

HERE = Path(__file__).resolve().parent
PUB_DIR = HERE.parent

# Curated topics: label and editorial assessment per topic
TOPIC_INFO = HERE / "topic_info_with_weights_output_schwerin_final_2026-09-27_labelled.json"
# One entry per sentence: the sentence, its topic and its assignment score
DOC_INFO = PUB_DIR / "02_bertopic" / "output" / "document_info_output_schwerin_final_2026-09-27.json"
# The same sentences in the same order, plus the paragraph number (P.n)
PARAGRAPHS = PUB_DIR / "02_bertopic" / "output" / "bertopic_results_with_paragraphs_schwerin_final_2026-09-27.json"

OUT_FILE = HERE / "coherence_check" / "coherence_sample.csv"

SENTENCES_PER_TOPIC = 10
SEED = 42


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    # ---- 1. Load the data ---------------------------------------------------

    all_topics = load_json(TOPIC_INFO)
    sentences = load_json(DOC_INFO)
    paragraphs = load_json(PARAGRAPHS)

    # Only the topics the editors consider meaningful
    meaningful_topics = []
    for topic in all_topics:
        if topic["Assessment"] == "meaningful":
            meaningful_topics.append(topic)

    # Safety check: both sentence files must list the sentences in the same
    # order, otherwise the paragraph numbers would belong to the wrong sentence.
    texts_1 = [entry["Document"] for entry in sentences]
    texts_2 = [entry["Document"] for entry in paragraphs]
    assert texts_1 == texts_2, "the two sentence files are not in the same order"

    # ---- 2. Draw 10 sentences per topic --------------------------------------

    random.seed(SEED)
    rows = []

    # Go through the topics in numerical order (T1, T2, ...), so that the
    # random draw is always the same.
    meaningful_topics.sort(key=lambda topic: int(topic["Topic"]))

    for topic in meaningful_topics:
        # Positions (0, 1, 2, ...) of all sentences that belong to this topic
        positions = []
        for position, entry in enumerate(sentences):
            if entry["Topic"] == topic["Topic"]:
                positions.append(position)

        # Safety check: the number of sentences must match the topic file
        assert len(positions) == int(topic["Count"]), f"sentence count differs for T{topic['Topic']}"

        # Draw at random, then put the drawn sentences back in text order
        n = min(SENTENCES_PER_TOPIC, len(positions))
        drawn = sorted(random.sample(positions, n))

        for position in drawn:
            entry = sentences[position]

            # Neighbouring sentences help to judge the sentence in context
            if position > 0:
                sentence_before = sentences[position - 1]["Document"]
            else:
                sentence_before = ""
            if position + 1 < len(sentences):
                sentence_after = sentences[position + 1]["Document"]
            else:
                sentence_after = ""

            rows.append({
                "Topic": f"T{topic['Topic']}",
                "Label": topic["Label"],
                # Sentence ids start at 1: s1 is the first sentence.
                # They are the same as <s xml:id="s1"> in the TEI file of step 04.
                "s_id": f"s{position + 1}",
                "Absatz": paragraphs[position]["Paragraph"],
                "Zuordnungswert": round(float(entry["Probability"]), 2),
                "Satz_davor": sentence_before,
                "Satz": entry["Document"],
                "Satz_danach": sentence_after,
                # Empty columns, filled in during the manual review
                "passt (ja/teilweise/nein)": "",
                "Kommentar": "",
            })

    # ---- 3. Write the table ------------------------------------------------

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig and ";" so that Excel opens the file correctly
    with open(OUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} sentences from {len(meaningful_topics)} topics written to {OUT_FILE}")


if __name__ == "__main__":
    main()
