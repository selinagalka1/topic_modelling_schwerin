# -*- coding: utf-8 -*-
"""
Sentences that the final model (MiniLM) may have left out wrongly.

The final model leaves 40 % of the sentences without a topic (outliers,
topic -1). This script lists the outlier sentences of MiniLM that BOTH other
embedding models (mpnet and CamemBERT) assign to a topic with a thematic
profile. These are candidates for sentences that MiniLM should perhaps have
assigned ("false negatives").

A topic counts as thematic if it is neither the outlier cluster (-1) nor the
catch-all topic without a thematic profile (T0 in MiniLM and mpnet;
CamemBERT has no such topic; see the comparison of embedding models in the article).

From all candidates, 50 are drawn at random for manual review. The random
seed is fixed (42), so running the script again draws exactly the same
sentences.

Input
    ../02_bertopic/output/document_info_output_schwerin_final_2026-09-27.json      (MiniLM)
    output/embedding_models/document_info_mpnet.json
    output/embedding_models/document_info_camembert.json
    ../02_bertopic/output/bertopic_results_with_paragraphs_schwerin_final_2026-09-27.json
Output
    output/false_negatives/false_negative_candidates_all.csv
    output/false_negatives/false_negative_candidates_sample50.csv   (empty columns for the review)

The reviewed version of the sample is
output/false_negatives/false_negative_candidates_sample50_coded.csv.
Running the script does not change it.

Run:  python false_negative_candidates.py
"""
import csv
import json
import random
from pathlib import Path


# ---- Settings -------------------------------------------------------------

HERE = Path(__file__).resolve().parent
PUB_DIR = HERE.parent

# One entry per sentence (same sentences, same order) for each of the three models
SENTENCES = {
    "minilm": PUB_DIR / "02_bertopic" / "output" / "document_info_output_schwerin_final_2026-09-27.json",
    "mpnet": HERE / "output" / "embedding_models" / "document_info_mpnet.json",
    "camembert": HERE / "output" / "embedding_models" / "document_info_camembert.json",
}
# The same sentences in the same order, plus the paragraph number (P.n)
PARAGRAPHS = PUB_DIR / "02_bertopic" / "output" / "bertopic_results_with_paragraphs_schwerin_final_2026-09-27.json"

# Topic numbers WITHOUT a thematic profile in each model:
# -1 = outliers, 0 = catch-all topic (only in MiniLM and mpnet)
NOT_THEMATIC = {"minilm": {-1, 0}, "mpnet": {-1, 0}, "camembert": {-1}}

OUT_DIR = HERE / "output" / "false_negatives"
SAMPLE_SIZE = 50
SEED = 42


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_table(path, rows):
    # utf-8-sig and ";" so that Excel opens the file correctly
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main():
    # ---- 1. Load the data ---------------------------------------------------

    sentences = {}
    for model, path in SENTENCES.items():
        sentences[model] = load_json(path)
    paragraphs = load_json(PARAGRAPHS)

    # Safety check: all files must list the same sentences in the same order,
    # otherwise the sentences of the three models could not be compared.
    texts = [entry["Document"] for entry in sentences["minilm"]]
    for model in ("mpnet", "camembert"):
        assert [entry["Document"] for entry in sentences[model]] == texts, f"sentence order differs in {model}"
    assert [entry["Document"] for entry in paragraphs] == texts, "sentence order differs in the paragraph file"

    # ---- 2. Find the candidates --------------------------------------------

    candidates = []
    for position, minilm_entry in enumerate(sentences["minilm"]):
        # Only sentences that MiniLM leaves without a topic
        if int(minilm_entry["Topic"]) != -1:
            continue

        mpnet_entry = sentences["mpnet"][position]
        camembert_entry = sentences["camembert"][position]

        # Both other models must assign a thematic topic
        if int(mpnet_entry["Topic"]) in NOT_THEMATIC["mpnet"]:
            continue
        if int(camembert_entry["Topic"]) in NOT_THEMATIC["camembert"]:
            continue

        # Neighbouring sentences help to judge the sentence in context
        if position > 0:
            sentence_before = texts[position - 1]
        else:
            sentence_before = ""
        if position + 1 < len(texts):
            sentence_after = texts[position + 1]
        else:
            sentence_after = ""

        candidates.append({
            # Sentence ids start at 1: s1 is the first sentence.
            # They are the same as <s xml:id="s1"> in the TEI file of step 04.
            "s_id": f"s{position + 1}",
            "Absatz": paragraphs[position]["Paragraph"],
            "Satz_davor": sentence_before,
            "Satz": texts[position],
            "Satz_danach": sentence_after,
            # Topic number and top words in the two other models
            "mpnet_Topic": mpnet_entry["Topic"],
            "mpnet_Begriffe": mpnet_entry["Top_n_words"],
            "camembert_Topic": camembert_entry["Topic"],
            "camembert_Begriffe": camembert_entry["Top_n_words"],
            # Empty columns, filled in during the manual review
            "Thema_erkennbar (ja/nein/unklar)": "",
            "passendes_MiniLM_Topic": "",
            "Kommentar": "",
        })

    # ---- 3. Draw the sample ------------------------------------------------

    random.seed(SEED)
    sample = random.sample(candidates, SAMPLE_SIZE)
    # Put the drawn sentences back in text order (s1, s2, ...)
    sample.sort(key=lambda row: int(row["s_id"][1:]))

    # ---- 4. Write the tables -----------------------------------------------

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_table(OUT_DIR / "false_negative_candidates_all.csv", candidates)
    write_table(OUT_DIR / f"false_negative_candidates_sample{SAMPLE_SIZE}.csv", sample)

    print(f"{len(candidates)} candidates, sample of {len(sample)} written to {OUT_DIR}")


if __name__ == "__main__":
    main()
