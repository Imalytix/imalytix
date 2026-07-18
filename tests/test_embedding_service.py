from __future__ import annotations

from PIL import Image

from app.services.embedding_service import build_embedding, cosine_similarity
from app.services.vector_store import EmbeddingVectorStore


def test_embedding_strategies_return_vectors():
    image = Image.new("RGB", (32, 32), color=(255, 0, 0))

    dino = build_embedding(image, strategy="dino")
    clip = build_embedding(image, strategy="clip")

    assert dino
    assert clip
    assert len(dino) != 0
    assert len(clip) != 0


def test_cosine_similarity_is_bounded():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_vector_store_saves_and_searches(tmp_path):
    store = EmbeddingVectorStore(str(tmp_path / "embedding.sqlite3"))
    store.save(
        phash="aaaaaaaaaaaaaaaa",
        strategy="dino",
        embedding=[1.0, 0.0, 0.0],
        source_url="https://example.com/a.jpg",
        filename="a.jpg",
        category="publisher",
        label="trusted",
        mode="standard",
    )
    store.save(
        phash="bbbbbbbbbbbbbbbb",
        strategy="dino",
        embedding=[0.99, 0.01, 0.0],
        source_url="https://example.com/b.jpg",
        filename="b.jpg",
        category="publisher",
        label="trusted",
        mode="standard",
    )

    hits = store.search(
        phash="cccccccccccccccc",
        strategy="dino",
        embedding=[1.0, 0.0, 0.0],
        top_k=1,
    )

    assert hits
    assert hits[0].phash in {"aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb"}
    assert hits[0].similarity > 0.95
