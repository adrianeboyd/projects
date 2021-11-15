from typing import Optional, Iterable, cast
from thinc.api import get_current_ops, Ops
from thinc.types import Ragged, Ints1d

from spacy.pipeline.spancat import Suggester
from spacy.tokens import Doc
from spacy.util import registry


@registry.misc("noun_chunk_suggester.v1")
def build_noun_chunk_suggester() -> Suggester:
    def noun_chunk_suggester(
        docs: Iterable[Doc], *, ops: Optional[Ops] = None
    ) -> Ragged:
        if ops is None:
            ops = get_current_ops()
        spans = []
        lengths = []
        for doc in docs:
            if doc.has_annotation("DEP"):
                edges = [-2, -1, 0, 1, 2]
                chunks = []
                for chunk in doc.noun_chunks:
                    for left in edges:
                        for right in edges:
                            if (
                                chunk.start + left >= 0
                                and chunk.end + right < len(doc)
                                and chunk.start + left < chunk.end + right
                            ):
                                chunks.append([chunk.start + left, chunk.end + right])
                chunks = ops.asarray(chunks, dtype="i")
                if chunks.shape[0] > 0:
                    spans.append(chunks)
                    lengths.append(chunks.shape[0])
                else:
                    lengths.append(0)
            else:
                lengths.append(0)
        lengths_array = cast(Ints1d, ops.asarray(lengths, dtype="i"))
        if len(spans) > 0:
            output = Ragged(ops.xp.vstack(spans), lengths_array)
        else:
            output = Ragged(ops.xp.zeros((0, 0), dtype="i"), lengths_array)

        assert output.dataXd.ndim == 2
        return output

    return noun_chunk_suggester
