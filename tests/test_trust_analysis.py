from __future__ import annotations

from app.services.phash_store import PHashAnalysisStore
from app.services.trust_analysis_service import build_trust_analysis


def _metadata(ai_tool_detected: bool = False, evidence: list[str] | None = None, camera_make_model_found: bool = False) -> dict:
    return {
        "ai_tool_detected": ai_tool_detected,
        "evidence": evidence or [],
        "camera_make_model_found": camera_make_model_found,
    }


def test_trust_analysis_flags_duplicate_reuse(tmp_path):
    store = PHashAnalysisStore(str(tmp_path / "cache.sqlite3"))
    base_response = {
        "product": "Imalytix",
        "request_id": "req_1",
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
            "ai_probability": 10,
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
        "trust_analysis": None,
        "evidence_summary": [],
        "suspicious_regions": [],
        "limitations": [],
        "recommended_action": "test",
    }
    store.save(phash="aaaaaaaaaaaaaaaa", mode="standard", response=base_response)

    trust = build_trust_analysis(
        phash="aaaaaaaaaaaaaaaa",
        mode="standard",
        source_url=None,
        filename="copy.jpg",
        metadata_result=_metadata(),
        detector_results=[],
        vision_results=[],
        source_result=None,
        phash_store=store,
    )

    assert trust.theft_risk_score > 0
    assert trust.trust_score < 100
    assert any("pHash" in item for item in trust.evidence)


def test_trust_analysis_flags_similar_phash_reuse(tmp_path):
    store = PHashAnalysisStore(str(tmp_path / "cache.sqlite3"))
    base_response = {
        "product": "Imalytix",
        "request_id": "req_1",
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
            "ai_probability": 10,
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
        "trust_analysis": None,
        "evidence_summary": [],
        "suspicious_regions": [],
        "limitations": [],
        "recommended_action": "test",
    }
    store.save(phash="aaaaaaaaaaaaaaaa", mode="standard", response=base_response)

    trust = build_trust_analysis(
        phash="aaaaaaaaaaaaaaab",
        mode="standard",
        source_url=None,
        filename="edit.jpg",
        metadata_result=_metadata(),
        detector_results=[],
        vision_results=[],
        source_result=None,
        phash_store=store,
    )

    assert trust.theft_risk_score > 0
    assert any("유사 pHash" in item for item in trust.evidence)


def test_trust_analysis_detects_forgery_signals():
    trust = build_trust_analysis(
        phash="bbbbbbbbbbbbbbbb",
        mode="standard",
        source_url="https://example.com/generated-image.jpg",
        filename="generated.png",
        metadata_result=_metadata(ai_tool_detected=True, evidence=["EXIF Software 태그에서 Midjourney 흔적이 확인되었습니다."]),
        detector_results=[{"score": 0.9}],
        vision_results=[
            {
                "score": 0.88,
                "confidence": "high",
                "evidence": [{"severity": "high", "description": "손가락 구조가 부자연스럽습니다."}],
                "suspicious_regions": [],
                "limitations": [],
            }
        ],
        source_result={"known_ai_cdn": True, "trusted_source": False, "evidence": ["AI CDN"]},
        phash_store=None,
    )

    assert trust.forgery_risk_score > trust.theft_risk_score
    assert trust.label in {"주의 필요", "위변조 가능성 높음", "추가 검증 권장", "불확실"}
    assert trust.signals
