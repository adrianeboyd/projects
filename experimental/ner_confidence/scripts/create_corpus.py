import re
import typer
import spacy
from spacy.language import Language
from spacy.tokens import DocBin
from itertools import islice
from pathlib import Path
from datasets import load_dataset


@Language.component("remove_trf_data")
def remove_trf_data(doc):
    doc._.trf_data = None
    return doc


def main(
    lang: str,
    oscar_dataset: str,
    max_texts: int,
    model: str,
    output_dir: Path,
):
    dataset = load_dataset("oscar", oscar_dataset, split="train", streaming=True)
    spacy.prefer_gpu()
    nlp = spacy.load(
        model, disable=["tagger", "parser", "attribute_ruler", "lemmatizer"]
    )
    nlp.add_pipe("remove_trf_data")
    train_corpus = DocBin()
    dev_corpus = DocBin()
    texts = (
        re.sub(r"\s+", " ", line["text"].strip() + "\n")
        for line in islice(iter(dataset), max_texts)
    )
    for i, doc in enumerate(nlp.pipe(texts)):
        doc.spans["sc"] = doc.ents
        if i % 10 == 0:
            dev_corpus.add(doc)
        else:
            train_corpus.add(doc)

    train_corpus.to_disk(output_dir / "train.spacy")
    dev_corpus.to_disk(output_dir / "dev.spacy")


if __name__ == "__main__":
    typer.run(main)
