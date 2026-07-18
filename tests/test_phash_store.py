from __future__ import annotations

from app.services.phash_store import PHashAnalysisStore, hamming_distance_hex


def test_hamming_distance_hex_matches_identical_hashes():
    assert hamming_distance_hex("f0e1d2c3b4a59687", "f0e1d2c3b4a59687") == 0


def test_phash_store_saves_and_finds_exact_match(tmp_path):
    store = PHashAnalysisStore(str(tmp_path / "phash.sqlite3"))
    response = {
        "product": "Imalytix",
        "request_id": "req_test",
        "mode": "standard",
        "input": {
            "type": "file_upload",
            "mime_type": "image/jpeg",
            "width": 10,
            "height": 10,
            "phash": "f0e1d2c3b4a59687",
        },
        "final_result": {
            "is_ai_generated": True,
            "ai_probability": 87,
            "label": "AI 생성 가능성 높음",
            "confidence": "high",
        },
        "metadata_analysis": {
            "exif_found": False,
            "png_metadata_found": False,
            "c2pa_found": False,
            "ai_tool_detected": False,
            "detected_tools": [],
            "metadata_score": 0,
            "camera_make_model_found": False,
            "evidence": [],
            "limitations": [],
            "raw": {},
        },
        "detector_results": [],
        "vision_results": [],
        "evidence_summary": [],
        "suspicious_regions": [],
        "limitations": [],
        "recommended_action": "test",
    }

    store.save(phash="f0e1d2c3b4a59687", mode="standard", response=response)
    match = store.find_best_match(phash="f0e1d2c3b4a59687", mode="standard", max_distance=0)

    assert match is not None
    assert match.distance == 0
    assert match.payload["request_id"] == "req_test"


def test_phash_store_finds_similar_match_with_threshold(tmp_path):
    store = PHashAnalysisStore(str(tmp_path / "phash.sqlite3"))
    response = {
        "product": "Imalytix",
        "request_id": "req_test",
        "mode": "standard",
        "input": {
            "type": "file_upload",
            "mime_type": "image/jpeg",
            "width": 10,
            "height": 10,
            "phash": "aaaaaaaaaaaaaaaa",
        },
        "final_result": {
            "is_ai_generated": False,
            "ai_probability": 12,
            "label": "실제 이미지 가능성 높음",
            "confidence": "medium",
        },
        "metadata_analysis": {
            "exif_found": False,
            "png_metadata_found": False,
            "c2pa_found": False,
            "ai_tool_detected": False,
            "detected_tools": [],
            "metadata_score": 0,
            "camera_make_model_found": False,
            "evidence": [],
            "limitations": [],
            "raw": {},
        },
        "detector_results": [],
        "vision_results": [],
        "evidence_summary": [],
        "suspicious_regions": [],
        "limitations": [],
        "recommended_action": "test",
    }

    store.save(phash="aaaaaaaaaaaaaaaa", mode="standard", response=response)
    match = store.find_best_match(phash="aaaaaaaaaaaaaaab", mode="standard", max_distance=4)

    assert match is not None
    assert match.distance == 1
    assert match.similarity > 0.9
