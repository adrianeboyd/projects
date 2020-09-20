import spacy
from spacy.tokens import DocBin
from spacy.training import Corpus
import re
import tempfile
import typer
from conll18_ud_eval import load_conllu, evaluate


def main(model: str, gold_path: str, output_path: str):
    nlp = spacy.load(model)
    texts = []
    with open(gold_path) as fileh:
        text = ""
        prev_line = ""
        for line in fileh:
            line = line.strip()
            if text and (line.startswith("# newdoc") or line.startswith("# newpar")):
                texts.append(re.sub("\s+", " ", text.strip()))
                text = ""
            if line.startswith("# text = "):
                text += line.replace("# text = ", "")
            if line == "":
                cols = prev_line.split("\t")
                if len(cols) >= 10:
                    if not "SpaceAfter=No" in cols[9]:
                        text += " "
            prev_line = line
        if text:
            texts.append(text)

    docs = nlp.pipe(texts)
    output_lines = []
    for doc in docs:
        for sent in doc.sents:
            output_lines.append("# text = " + sent.text + "\n")
            for i, token in enumerate(sent):
                cols = ["_"] * 10
                cols[0] = i + 1
                cols[1] = token.text
                if token.lemma_:
                    cols[2] = token.lemma_
                if token.pos_:
                    cols[3] = token.pos_
                if token.tag_:
                    cols[4] = token.tag_
                if token.morph_:
                    cols[5] = token.morph_
                cols[6] = 0 if token.head.i == token.i else token.head.i + 1 - sent[0].i
                cols[7] = "root" if token.dep_ == "ROOT" else token.dep_
                if not token.whitespace_:
                    cols[9] = "SpaceAfter=No"
                output_lines.append("\t".join(str(c) for c in cols) + "\n")
            output_lines.append("\n")
    with tempfile.TemporaryFile("w+") as fileh:
        fileh.writelines(output_lines)
        fileh.flush()
        fileh.seek(0)
        pred_corpus = load_conllu(fileh)
    with open(gold_path) as fileh:
        gold_corpus = load_conllu(fileh)
    scores = evaluate(gold_corpus, pred_corpus)
    with open(output_path, "w") as fileh:
        fileh.write(format_evaluation(scores))


def format_evaluation(evaluation):
    lines = []
    lines.append("Metric     | Precision |    Recall |  F1 Score | AligndAcc")
    lines.append("-----------+-----------+-----------+-----------+-----------")
    for metric in["Tokens", "Sentences", "Words", "UPOS", "XPOS", "UFeats", "AllTags", "Lemmas", "UAS", "LAS", "CLAS", "MLAS", "BLEX"]:
        lines.append("{:11}|{:10.2f} |{:10.2f} |{:10.2f} |{}".format(
            metric,
            100 * evaluation[metric].precision,
            100 * evaluation[metric].recall,
            100 * evaluation[metric].f1,
            "{:10.2f}".format(100 * evaluation[metric].aligned_accuracy) if evaluation[metric].aligned_accuracy is not None else ""
        ))
    return "\n".join(lines)


if __name__ == "__main__":
    typer.run(main)
