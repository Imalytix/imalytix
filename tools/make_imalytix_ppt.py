from __future__ import annotations

import base64
import zipfile
from pathlib import Path
from textwrap import dedent


ROOT = Path(r"C:\Users\cubix\Desktop\성윤-창업")
FRONTEND = ROOT / "imalytix-frontend"
OUT_DIR = ROOT / "deliverables"
OUT_DIR.mkdir(exist_ok=True)

PHOTO = FRONTEND / "public" / "sakura-photo.png"
SLIDE1_SVG = OUT_DIR / "imalytix_slide_1.svg"
SLIDE2_SVG = OUT_DIR / "imalytix_slide_2.svg"
PPTX_PATH = OUT_DIR / "Imalytix_UI_Prototype.pptx"

SLIDE_W = 1600
SLIDE_H = 900


def read_photo_data_uri() -> str:
    data = PHOTO.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_slide1_svg() -> str:
    return dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{SLIDE_W}" height="{SLIDE_H}" viewBox="0 0 {SLIDE_W} {SLIDE_H}">
          <defs>
            <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#f8fafc"/>
              <stop offset="100%" stop-color="#eef2f7"/>
            </linearGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="18" stdDeviation="20" flood-color="#0f172a" flood-opacity="0.08"/>
            </filter>
          </defs>
          <rect width="1600" height="900" fill="url(#bg)"/>
          <rect x="0" y="0" width="1600" height="72" fill="#ffffff" opacity="0.95"/>
          <circle cx="36" cy="36" r="7" fill="#ff5f57"/>
          <circle cx="58" cy="36" r="7" fill="#febc2e"/>
          <circle cx="80" cy="36" r="7" fill="#28c840"/>
          <rect x="100" y="18" width="1120" height="36" rx="10" fill="#f1f5f9" stroke="#e2e8f0"/>
          <text x="126" y="42" font-family="Inter, Arial, sans-serif" font-size="16" fill="#64748b">http://localhost:5173/</text>
          <text x="1460" y="30" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#0f172a">Imalytix</text>
          <text x="1460" y="49" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="12" fill="#64748b">프로토타입</text>

          <text x="56" y="118" font-family="Inter, Arial, sans-serif" font-size="36" font-weight="700" fill="#0f172a">Imalytix Image Analysis</text>
          <text x="56" y="148" font-family="Inter, Arial, sans-serif" font-size="18" fill="#64748b">이미지 업로드 + 미리보기 + 엔진별 분석 결과를 한 화면에 표시</text>

          <rect x="1255" y="92" width="180" height="56" rx="16" fill="#0f172a" filter="url(#shadow)"/>
          <text x="1345" y="126" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#ffffff">파일 선택</text>

          <rect x="54" y="190" width="1492" height="150" rx="24" fill="#ffffff" filter="url(#shadow)"/>
          <rect x="76" y="214" width="360" height="102" rx="22" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="106" y="252" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="700" fill="#0f172a">이미지 업로드</text>
          <text x="106" y="278" font-family="Inter, Arial, sans-serif" font-size="13" fill="#64748b">JPG / PNG / WEBP 지원</text>
          <rect x="470" y="214" width="1060" height="102" rx="22" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="520" y="250" font-family="Inter, Arial, sans-serif" font-size="14" fill="#94a3b8">미리보기</text>
          <image href="{read_photo_data_uri()}" x="1010" y="224" width="500" height="82" preserveAspectRatio="xMidYMid slice" clip-path="inset(0 round 18px)"/>
          <text x="520" y="278" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="700" fill="#0f172a">벚꽃 사진 미리보기</text>

          <rect x="54" y="366" width="420" height="356" rx="28" fill="#ffffff" filter="url(#shadow)"/>
          <text x="86" y="410" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">점수</text>
          <circle cx="264" cy="536" r="126" fill="#f8fafc" stroke="#dbe4f0" stroke-width="22"/>
          <circle cx="264" cy="536" r="126" fill="none" stroke="#38bdf8" stroke-width="10"/>
          <text x="264" y="548" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="60" font-weight="700" fill="#0f172a">87%</text>
          <text x="264" y="592" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">AI 생성물 가능성</text>
          <rect x="72" y="654" width="384" height="42" rx="12" fill="#eef2ff" stroke="#cbd5e1"/>
          <text x="264" y="681" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="700" fill="#0f172a">AI 생성 가능성 높음</text>

          <rect x="500" y="366" width="1046" height="356" rx="28" fill="#ffffff" filter="url(#shadow)"/>
          <text x="532" y="410" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">엔진별 분석 결과</text>

          <rect x="528" y="432" width="980" height="86" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <circle cx="570" cy="475" r="22" fill="#fff" stroke="#cbd5e1"/>
          <text x="570" y="482" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">O</text>
          <text x="620" y="464" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">OpenAI Vision</text>
          <text x="620" y="490" font-family="Inter, Arial, sans-serif" font-size="13" fill="#64748b">손가락 구조 이상 / 배경 경계 오류 / 텍스처 반복</text>
          <text x="1380" y="470" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="700" fill="#0f172a">88%</text>

          <rect x="528" y="526" width="980" height="86" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <circle cx="570" cy="569" r="22" fill="#fff" stroke="#cbd5e1"/>
          <text x="570" y="576" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">M</text>
          <text x="620" y="558" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">Metadata</text>
          <text x="620" y="584" font-family="Inter, Arial, sans-serif" font-size="13" fill="#64748b">EXIF / PNG / C2PA / AI 도구 흔적</text>
          <text x="1380" y="564" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="700" fill="#0f172a">35</text>

          <rect x="528" y="620" width="980" height="86" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <circle cx="570" cy="663" r="22" fill="#fff" stroke="#cbd5e1"/>
          <text x="570" y="670" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">D</text>
          <text x="620" y="652" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">Dedicated Detectors</text>
          <text x="620" y="678" font-family="Inter, Arial, sans-serif" font-size="13" fill="#64748b">Hive / Sightengine / Reality Defender (예정)</text>
          <text x="1380" y="658" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="700" fill="#0f172a">92%</text>

          <rect x="54" y="748" width="1492" height="98" rx="24" fill="#ffffff" filter="url(#shadow)"/>
          <rect x="74" y="772" width="440" height="50" rx="16" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="94" y="803" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">메타데이터 분석</text>
          <rect x="528" y="772" width="440" height="50" rx="16" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="548" y="803" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">전용 탐지기 결과</text>
          <rect x="982" y="772" width="542" height="50" rx="16" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="1002" y="803" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">최종 통합 요약은 보조 정보로만 표시</text>
        </svg>
        """
    )


def build_slide2_svg() -> str:
    photo = read_photo_data_uri()
    return dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{SLIDE_W}" height="{SLIDE_H}" viewBox="0 0 {SLIDE_W} {SLIDE_H}">
          <defs>
            <linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#f8fafc"/>
              <stop offset="100%" stop-color="#eef2f7"/>
            </linearGradient>
            <filter id="shadow2" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="18" stdDeviation="20" flood-color="#0f172a" flood-opacity="0.08"/>
            </filter>
          </defs>
          <rect width="1600" height="900" fill="url(#bg2)"/>
          <rect x="0" y="0" width="1600" height="72" fill="#ffffff" opacity="0.95"/>
          <circle cx="36" cy="36" r="7" fill="#ff5f57"/>
          <circle cx="58" cy="36" r="7" fill="#febc2e"/>
          <circle cx="80" cy="36" r="7" fill="#28c840"/>
          <rect x="100" y="18" width="1120" height="36" rx="10" fill="#f1f5f9" stroke="#e2e8f0"/>
          <text x="126" y="42" font-family="Inter, Arial, sans-serif" font-size="16" fill="#64748b">http://localhost:5173/detail</text>
          <text x="1460" y="30" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#0f172a">Imalytix</text>
          <text x="1460" y="49" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="12" fill="#64748b">상세 분석</text>

          <text x="56" y="118" font-family="Inter, Arial, sans-serif" font-size="36" font-weight="700" fill="#0f172a">상세 분석 화면</text>
          <text x="56" y="148" font-family="Inter, Arial, sans-serif" font-size="18" fill="#64748b">Evidence Summary를 상단에 배치하고, 중심 이미지와 의심 영역을 함께 확인</text>
          <rect x="1270" y="92" width="120" height="44" rx="14" fill="#0f172a"/>
          <text x="1330" y="120" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="700" fill="#ffffff">AI 87%</text>
          <rect x="1400" y="92" width="150" height="44" rx="14" fill="#ffffff" stroke="#dbe4f0"/>
          <text x="1475" y="120" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="15" fill="#0f172a">← 요약으로</text>

          <rect x="54" y="190" width="1492" height="98" rx="24" fill="#ffffff" filter="url(#shadow2)"/>
          <text x="84" y="228" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">Evidence Summary</text>
          <rect x="84" y="240" width="360" height="28" rx="10" fill="#f8fafc" stroke="#e2e8f0"/>
          <rect x="458" y="240" width="440" height="28" rx="10" fill="#f8fafc" stroke="#e2e8f0"/>
          <rect x="912" y="240" width="570" height="28" rx="10" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="102" y="259" font-family="Inter, Arial, sans-serif" font-size="12" fill="#0f172a">EXIF Software 태그에서 Midjourney 흔적이 확인되었습니다.</text>
          <text x="474" y="259" font-family="Inter, Arial, sans-serif" font-size="12" fill="#0f172a">손가락 개수와 관절 연결이 자연스럽지 않습니다.</text>
          <text x="928" y="259" font-family="Inter, Arial, sans-serif" font-size="12" fill="#0f172a">배경 경계와 직선 구조가 자연스럽지 않습니다.</text>

          <rect x="54" y="308" width="360" height="506" rx="28" fill="#ffffff" filter="url(#shadow2)"/>
          <text x="84" y="348" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">AI 의심 부위</text>
          <rect x="84" y="372" width="300" height="96" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <rect x="84" y="480" width="300" height="96" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <rect x="84" y="588" width="300" height="96" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="110" y="410" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">1. 손가락 구조 이상</text>
          <text x="110" y="436" font-family="Inter, Arial, sans-serif" font-size="12" fill="#64748b">손가락 수와 연결이 부자연스러움</text>
          <text x="110" y="518" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">2. 피부 텍스처 반복</text>
          <text x="110" y="544" font-family="Inter, Arial, sans-serif" font-size="12" fill="#64748b">반복 패턴이 보이는 표면 질감</text>
          <text x="110" y="626" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">3. 배경 왜곡</text>
          <text x="110" y="652" font-family="Inter, Arial, sans-serif" font-size="12" fill="#64748b">직선과 원근이 약간 어긋남</text>

          <rect x="440" y="308" width="780" height="506" rx="28" fill="#ffffff" filter="url(#shadow2)"/>
          <text x="470" y="348" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">이미지 분석</text>
          <rect x="470" y="372" width="720" height="410" rx="24" fill="#f8fafc" stroke="#e2e8f0"/>
          <image href="{photo}" x="470" y="372" width="720" height="410" preserveAspectRatio="xMidYMid slice" clip-path="inset(0 round 24px)"/>
          <rect x="820" y="400" width="200" height="120" rx="6" fill="rgba(255,255,255,0.1)" stroke="#ef4444" stroke-width="4"/>
          <rect x="650" y="466" width="210" height="130" rx="6" fill="rgba(255,255,255,0.08)" stroke="#f59e0b" stroke-width="4"/>
          <rect x="480" y="438" width="160" height="160" rx="6" fill="rgba(255,255,255,0.08)" stroke="#22c55e" stroke-width="4"/>
          <text x="835" y="426" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#ef4444">1</text>
          <text x="665" y="492" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#f59e0b">2</text>
          <text x="495" y="464" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#22c55e">3</text>

          <rect x="1240" y="308" width="306" height="506" rx="28" fill="#ffffff" filter="url(#shadow2)"/>
          <text x="1270" y="348" font-family="Inter, Arial, sans-serif" font-size="14" fill="#64748b">선택 항목 설명</text>
          <rect x="1270" y="372" width="246" height="82" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="1290" y="404" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700" fill="#0f172a">손가락 구조 이상</text>
          <text x="1290" y="430" font-family="Inter, Arial, sans-serif" font-size="12" fill="#64748b">이미지 내부의 비정상 구조를 설명</text>
          <rect x="1270" y="470" width="246" height="120" rx="20" fill="#f8fafc" stroke="#e2e8f0"/>
          <text x="1290" y="503" font-family="Inter, Arial, sans-serif" font-size="13" fill="#64748b">관련 근거</text>
          <text x="1290" y="530" font-family="Inter, Arial, sans-serif" font-size="13" fill="#0f172a">• 손가락 개수와 관절 연결이 자연스럽지 않습니다.</text>
          <text x="1290" y="558" font-family="Inter, Arial, sans-serif" font-size="13" fill="#0f172a">• 배경 경계와 직선 구조가 자연스럽지 않습니다.</text>
        </svg>
        """
    )


def svg_to_file(path: Path, svg_text: str) -> None:
    path.write_text(svg_text, encoding="utf-8")


def content_types_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
          <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
          <Default Extension="xml" ContentType="application/xml"/>
          <Default Extension="svg" ContentType="image/svg+xml"/>
          <Default Extension="png" ContentType="image/png"/>
          <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
          <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
          <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
          <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
          <Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
          <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
          <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
          <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
        </Types>
        """
    )


def rels_root_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
          <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
          <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
        </Relationships>
        """
    )


def core_props_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
          xmlns:dc="http://purl.org/dc/elements/1.1/"
          xmlns:dcterms="http://purl.org/dc/terms/"
          xmlns:dcmitype="http://purl.org/dc/dcmitype/"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <dc:title>Imalytix UI Prototype</dc:title>
          <dc:creator>Codex</dc:creator>
          <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
          <dcterms:created xsi:type="dcterms:W3CDTF">2026-05-14T00:00:00Z</dcterms:created>
          <dcterms:modified xsi:type="dcterms:W3CDTF">2026-05-14T00:00:00Z</dcterms:modified>
        </cp:coreProperties>
        """
    )


def app_props_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
          xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
          <Application>Microsoft Office PowerPoint</Application>
          <PresentationFormat>Widescreen</PresentationFormat>
          <Slides>2</Slides>
          <Notes>0</Notes>
          <HiddenSlides>0</HiddenSlides>
          <MMClips>0</MMClips>
          <Company>OpenAI</Company>
          <LinksUpToDate>false</LinksUpToDate>
          <SharedDoc>false</SharedDoc>
          <HyperlinksChanged>false</HyperlinksChanged>
          <AppVersion>16.0000</AppVersion>
        </Properties>
        """
    )


def presentation_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <p:sldMasterIdLst>
            <p:sldMasterId id="2147483648" r:id="rId1"/>
          </p:sldMasterIdLst>
          <p:sldIdLst>
            <p:sldId id="256" r:id="rId2"/>
            <p:sldId id="257" r:id="rId3"/>
          </p:sldIdLst>
          <p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>
          <p:notesSz cx="6858000" cy="9144000"/>
        </p:presentation>
        """
    )


def presentation_rels_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
          <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
          <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/>
        </Relationships>
        """
    )


def slide_master_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <p:cSld name="Master">
            <p:spTree>
              <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
              </p:nvGrpSpPr>
              <p:grpSpPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="0" cy="0"/>
                  <a:chOff x="0" y="0"/>
                  <a:chExt cx="0" cy="0"/>
                </a:xfrm>
              </p:grpSpPr>
            </p:spTree>
          </p:cSld>
          <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
          <p:sldLayoutIdLst>
            <p:sldLayoutId id="2147483649" r:id="rId1"/>
          </p:sldLayoutIdLst>
          <p:txStyles>
            <p:titleStyle/>
            <p:bodyStyle/>
            <p:otherStyle/>
          </p:txStyles>
        </p:sldMaster>
        """
    )


def slide_master_rels_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
          <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
        </Relationships>
        """
    )


def slide_layout_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
          type="blank" preserve="1">
          <p:cSld name="Blank">
            <p:spTree>
              <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
              </p:nvGrpSpPr>
              <p:grpSpPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="0" cy="0"/>
                  <a:chOff x="0" y="0"/>
                  <a:chExt cx="0" cy="0"/>
                </a:xfrm>
              </p:grpSpPr>
            </p:spTree>
          </p:cSld>
          <p:clrMapOvr>
            <a:masterClrMapping/>
          </p:clrMapOvr>
        </p:sldLayout>
        """
    )


def theme_xml() -> str:
    return dedent(
        """\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
          <a:themeElements>
            <a:clrScheme name="Office">
              <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
              <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
              <a:dk2><a:srgbClr val="1F1F1F"/></a:dk2>
              <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
              <a:accent1><a:srgbClr val="5B9BD5"/></a:accent1>
              <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
              <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>
              <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
              <a:accent5><a:srgbClr val="4472C4"/></a:accent5>
              <a:accent6><a:srgbClr val="70AD47"/></a:accent6>
              <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
              <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
            </a:clrScheme>
            <a:fontScheme name="Office">
              <a:majorFont>
                <a:latin typeface="Aptos"/>
                <a:ea typeface="Aptos"/>
                <a:cs typeface="Aptos"/>
              </a:majorFont>
              <a:minorFont>
                <a:latin typeface="Aptos"/>
                <a:ea typeface="Aptos"/>
                <a:cs typeface="Aptos"/>
              </a:minorFont>
            </a:fontScheme>
            <a:fmtScheme name="Office">
              <a:fillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"/></a:gs></a:gsLst><a:lin ang="16200000" scaled="1"/></a:gradFill>
                <a:gradFill rotWithShape="1"><a:gsLst><a:gs pos="0"><a:schemeClr val="phClr"/></a:gs></a:gsLst><a:lin ang="16200000" scaled="1"/></a:gradFill>
              </a:fillStyleLst>
              <a:lnStyleLst>
                <a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
                <a:ln w="25400"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
                <a:ln w="38100"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
              </a:lnStyleLst>
              <a:effectStyleLst>
                <a:effectStyle><a:effectLst/></a:effectStyle>
                <a:effectStyle><a:effectLst/></a:effectStyle>
                <a:effectStyle><a:effectLst/></a:effectStyle>
              </a:effectStyleLst>
              <a:bgFillStyleLst>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
                <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
              </a:bgFillStyleLst>
            </a:fmtScheme>
          </a:themeElements>
        </a:theme>
        """
    )


def slide_xml(image_target: str) -> str:
    return dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <p:cSld>
            <p:bg>
              <p:bgPr>
                <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
                <a:effectLst/>
              </p:bgPr>
            </p:bg>
            <p:spTree>
              <p:nvGrpSpPr>
                <p:cNvPr id="1" name=""/>
                <p:cNvGrpSpPr/>
                <p:nvPr/>
              </p:nvGrpSpPr>
              <p:grpSpPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="0" cy="0"/>
                  <a:chOff x="0" y="0"/>
                  <a:chExt cx="0" y="0"/>
                </a:xfrm>
              </p:grpSpPr>
              <p:pic>
                <p:nvPicPr>
                  <p:cNvPr id="2" name="Slide Image"/>
                  <p:cNvPicPr>
                    <a:picLocks noChangeAspect="1"/>
                  </p:cNvPicPr>
                  <p:nvPr/>
                </p:nvPicPr>
                <p:blipFill>
                  <a:blip r:embed="rId1"/>
                  <a:stretch><a:fillRect/></a:stretch>
                </p:blipFill>
                <p:spPr>
                  <a:xfrm>
                    <a:off x="0" y="0"/>
                    <a:ext cx="12192000" cy="6858000"/>
                  </a:xfrm>
                  <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                </p:spPr>
              </p:pic>
            </p:spTree>
          </p:cSld>
          <p:clrMapOvr>
            <a:masterClrMapping/>
          </p:clrMapOvr>
        </p:sld>
        """
    )


def slide_rels_xml(image_name: str) -> str:
    return dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{image_name}"/>
        </Relationships>
        """
    )


def build_pptx() -> None:
    svg_to_file(SLIDE1_SVG, build_slide1_svg())
    svg_to_file(SLIDE2_SVG, build_slide2_svg())

    files: dict[str, bytes] = {
        "[Content_Types].xml": content_types_xml().encode("utf-8"),
        "_rels/.rels": rels_root_xml().encode("utf-8"),
        "docProps/core.xml": core_props_xml().encode("utf-8"),
        "docProps/app.xml": app_props_xml().encode("utf-8"),
        "ppt/presentation.xml": presentation_xml().encode("utf-8"),
        "ppt/_rels/presentation.xml.rels": presentation_rels_xml().encode("utf-8"),
        "ppt/slideMasters/slideMaster1.xml": slide_master_xml().encode("utf-8"),
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": slide_master_rels_xml().encode("utf-8"),
        "ppt/slideLayouts/slideLayout1.xml": slide_layout_xml().encode("utf-8"),
        "ppt/theme/theme1.xml": theme_xml().encode("utf-8"),
        "ppt/slides/slide1.xml": slide_xml("slide1.svg").encode("utf-8"),
        "ppt/slides/_rels/slide1.xml.rels": slide_rels_xml("slide1.svg").encode("utf-8"),
        "ppt/slides/slide2.xml": slide_xml("slide2.svg").encode("utf-8"),
        "ppt/slides/_rels/slide2.xml.rels": slide_rels_xml("slide2.svg").encode("utf-8"),
        "ppt/media/slide1.svg": SLIDE1_SVG.read_bytes(),
        "ppt/media/slide2.svg": SLIDE2_SVG.read_bytes(),
    }

    with zipfile.ZipFile(PPTX_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
      for name, data in files.items():
        zf.writestr(name, data)


if __name__ == "__main__":
    build_pptx()
    print(PPTX_PATH)
