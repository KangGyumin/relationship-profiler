import os
import json
import time
import re
import urllib.request
import urllib.error

# 로컬 config.py 또는 클라우드 환경변수에서 API 키 자동 탐색
try:
    from config import API_KEY, ENGINE_MODELS
except ImportError:
    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    ENGINE_MODELS = [
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-latest",
        "gemini-flash-latest",
        "gemini-1.5-flash"
    ]

if not API_KEY:
    API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """
당신은 대화 맥락과 심리, 대화 스킬을 냉철하고 과학적으로 분석하는 '객관적 관계 역학 프로파일러'입니다.
상대방의 마음을 읽어주는 것에 그치지 않고, 사용자가 저지르는 '치명적인 대화 실수'와 '매력 저하 행동'을 날카롭게 짚어 교정해줍니다.

[절대 규칙 - 출력 제약]
1. 내부 추론 과정(Chain of Thought)이나 영문 메모는 단 한 글자도 출력하지 마십시오.
2. 무조건 한국어 반말 톤으로, 아래 [출력 형식]의 5개 섹션만 명확하게 작성하십시오.

[분석 1원칙: 관계 유형의 열린 판별 (선입견 배제)]
모든 대화를 무조건 '썸/호감'으로 단정 짓지 말고, 대화의 호칭('자기', '여보', 애칭, 하트), 공유된 역사, 뉘앙스를 바탕으로 둘의 실제 관계를 객관적 확률(%)로 먼저 판정할 것:
- 확고한 연인/부부: 애칭 사용, 깊은 일상 공유 등. 연인 사이의 권태/서운함 예방, 애정 표현의 균형, 귀여운 티키타카를 진단.
- 허물없는 찐친/친구: 편안한 장난, 욕설/비속어, 돈 정산 등. '우정 100%'로 규정하고 의리와 유쾌함을 진단.
- 썸/호감/소개팅 탐색 단계: 아래의 [★ 나의 대화 행동 진단] 5대 치명적 감점 요인을 현미경처럼 들이대며 냉혹하게 분석.

[핵심 분석 영역]
1. [반증 가능성(Falsifiability)]: 사용자의 착각이나 김칫국을 깨부술 수 있는 결정적 반증 조건을 제시할 것.
2. [다중 가설 및 베이지안 확률 분포 (MECE 원칙)]: 
   상대방의 심리와 태도를 2분법(A, B)으로 단순화하지 말 것. 
   대화의 복잡도와 맥락에 따라 가장 유력한 주가설부터 가능성이 존재하는 보조/예외 가설(가설 A, B, C, 필요시 D까지)을 다각도로 도출할 것.
   각 가설마다 팩트에 기반한 타당성 근거를 제시하고, 모든 가설의 예상 확률(%) 총합은 반드시 정확히 100%가 되도록 산정할 것.
3. [★ 나의 대화 행동 진단 (메타인지 audit)]:
   사용자의 메시지에서 다음 실패 패턴이 나타나는지 현미경처럼 분석해 직설적으로 꼬집을 것:
   - 템포 불균형 & 안달남: 상대방의 답장 텀을 고려하지 않은 조급한 칼답, 상대방의 대화 종료/마무리 뉘앙스를 눈치채지 못하고 억지로 질척거리며 대화를 이어가려는 태도.
   - 쿨함과 여유의 부재 (Abundance Mindset 결여): "이 사람 아니어도 상관없다"는 당당함 없이, 관계에 목을 매며 주도권을 상대에게 헌납하는 결핍감.
   - 정보 과잉 방출 (TMI) & 미스터리 상실: 불안한 마음에 자신의 장점과 일상을 한 번에 다 읊어버려(100가지를 불안해서 다 말하기), 상대방의 호기심과 대화 소재를 스스로 소진시키는 행동.
   - 취조식 질문 & 주제 널뛰기: 한 주제로 꼬리에 꼬리를 물며 깊이감과 재미를 끌어내지 못하고, 대화가 끊길까 봐 조바심에 억지로 새 주제를 던지는 면접관식 질문 폭격.
   - 줏대 없는 억지 공감 & 단조로운 텐션: 자기 잣대 없이 무조건 상대에게 맞춰주기만 하느라 이성적 매력 상실, 본인만 재밌는 얘기하기, 은근한 허세, 티키타카 없이 노잼 텐션 유지 여부.
4. [행동 지침 & 추천 멘트]: 대화 템포를 맞추고 여유를 되찾기 위한 즉각적인 스탠스와, 한 주제를 자연스럽게 꼬리물기할 수 있는 실제 전송용 대체 멘트 제시.

[출력 형식]
1. [관계 유형 및 현 상황 진단]: (예: 확고한 연인 관계 99%, 허물없는 찐친 우정 100%, 썸/호감 탐색 70% 등 명확한 확률과 팩트 1~2문장)
2. [가설 및 반증 가능성 검증]: (핵심 가설의 성립 조건과 기각 여부)
3. [가설별 심리 프로파일링]: 
   - 가설 A (예상 확률 XX%): (주요 가설 해석 및 구체적 근거)
   - 가설 B (예상 확률 XX%): (경쟁 가설 해석 및 구체적 근거)
   - 가설 C (예상 확률 XX%): (대안/변수 가설 해석 및 구체적 근거)
   - 가설 D (예상 확률 XX%): (필요 시 작성, 낮은 확률의 예외적 심리/상황)
   *(단, 도출된 모든 가설의 확률 합계는 정확히 100%가 되도록 명시)*
4. [나의 대화 행동 진단]: (템포/칼답 안달남, 대화 종료 신호 무시, TMI 남발, 취조식 질문, 줏대 상실 등 직설 분석)
5. [행동 지침 & 추천 멘트]: (쿨한 거리두기 태도 및 꼬리에 꼬리를 무는 자연스러운 추천 멘트)
"""

def highlight_percentages_and_hypotheses(text):
    text = re.sub(
        r'-\s*(가설\s*[A-Z0-9가-힣]+)\s*(\([^\)]*?\d+%\))',
        r'- <span style="background-color:#0284C7; color:#FFFFFF; padding:2px 8px; border-radius:4px; font-weight:700; font-size:13px; margin-right:4px;">\1</span> <span style="background-color:#10B981; color:#FFFFFF; padding:2px 7px; border-radius:4px; font-weight:700; font-size:13px;">\2</span>',
        text
    )
    return text

def format_to_html(raw_text):
    sections = [
        ("1. [관계 유형 및 현 상황 진단]", "#38BDF8"),
        ("2. [가설 및 반증 가능성 검증]", "#F87171"),
        ("3. [가설별 심리 프로파일링]", "#34D399"),
        ("4. [나의 대화 행동 진단]", "#FB923C"),
        ("5. [행동 지침 & 추천 멘트]", "#C084FC")
    ]
    
    lines = raw_text.split('\n')
    parsed_cards = []
    curr_title = ""
    curr_border = "#38BDF8"
    curr_lines = []

    for line in lines:
        matched = False
        for sec_key, border_col in sections:
            clean_sec = sec_key.split("]")[0] + "]"
            if clean_sec in line:
                if curr_title:
                    content_str = "<br>".join([l.strip() for l in curr_lines if l.strip()]).strip()
                    parsed_cards.append((curr_title, curr_border, content_str))
                
                if "]:" in line:
                    t_part, _, c_part = line.partition("]:")
                    curr_title = t_part.strip() + "]"
                    curr_lines = [c_part.strip()] if c_part.strip() else []
                else:
                    curr_title = line.strip()
                    curr_lines = []
                    
                curr_border = border_col
                matched = True
                break
                
        if not matched and curr_title:
            if line.strip():
                curr_lines.append(line.strip())

    if curr_title:
        content_str = "<br>".join([l.strip() for l in curr_lines if l.strip()]).strip()
        parsed_cards.append((curr_title, curr_border, content_str))

    card_htmls = []
    for title, border, content in parsed_cards:
        styled_content = highlight_percentages_and_hypotheses(content)
        card_htmls.append(
            f'<div style="background-color: #1E293B !important; border: 1px solid #334155 !important; border-left: 6px solid {border} !important; border-radius: 10px !important; padding: 16px 20px !important; margin-bottom: 14px !important; text-align: left !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5) !important;">'
            f'<div style="color: {border} !important; font-size: 16px !important; font-weight: 800 !important; margin-bottom: 10px !important; font-family: \'Pretendard\', sans-serif !important; letter-spacing: -0.3px !important;">{title}</div>'
            f'<div style="color: #F8FAFC !important; font-size: 15px !important; font-weight: 450 !important; line-height: 1.75 !important; font-family: \'Pretendard\', sans-serif !important; margin: 0 !important; padding: 0 !important;">{styled_content}</div>'
            f'</div>'
        )

    final_html = "".join(card_htmls)
    if not final_html:
        final_html = f"<div style='color:#F8FAFC !important; font-size:15px; line-height:1.7; padding:10px;'>{raw_text.replace(chr(10), '<br>')}</div>"
        
    return f"""
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    <div style="font-family: 'Pretendard', sans-serif !important; width: 100% !important;">
        {final_html}
    </div>
    """

class RelationshipAnalyzer:
    @staticmethod
    def analyze(chat_text):
        key = API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return False, "<div style='color:#EF4444; font-size:15px;'>❌ GEMINI_API_KEY가 설정되지 않았습니다.</div>", ""

        prompt = f"{SYSTEM_PROMPT}\n\n[분석할 카카오톡 대화 데이터]:\n{chat_text}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2500},
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        data_bytes = json.dumps(payload).encode('utf-8')

        for model_name in ENGINE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    parts = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    text_pieces = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
                    if not text_pieces:
                        text_pieces = [p.get("text", "") for p in parts if "text" in p]
                    
                    raw_result = "".join(text_pieces).strip()
                    return True, format_to_html(raw_result), raw_result
            except Exception:
                continue

        return False, "<div style='color:#EF4444; font-size:15px;'>❌ AI 분석 엔진 응답 지연입니다. 잠시 후 다시 시도해주세요.</div>", ""

    @staticmethod
    def consult_followup(raw_report, user_question, history_list):
        key = API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return "API 키가 등록되지 않았습니다."

        history_context = ""
        for item in history_list:
            if isinstance(item, dict):
                sender = "사용자" if item.get("role") == "user" else "프로파일러"
                history_context += f"{sender}: {item.get('content', '')}\n"
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                history_context += f"사용자: {item[0]}\n프로파일러: {item[1]}\n"

        consult_prompt = f"""
당신은 방금 전 카톡 대화 진단 리포트를 작성한 '객관적 관계 역학 프로파일러'입니다.
사용자가 작성된 진단 결과를 바탕으로 추가 질문이나 상담을 요청했습니다.

[기존 분석 리포트 내용]:
{raw_report}

[이전 상담 대화 기록]:
{history_context}

[사용자의 추가 질문]:
{user_question}

[답변 원칙]:
1. 말투: 친근하면서도 뼈를 때리는 냉철한 한국어 반말 톤 유지.
2. 기존 리포트의 가설 및 진단 내용(상대방 심리, 관계 상태)과 100% 일관성을 유지할 것.
3. 뜬구름 잡는 소리 대신, "지금 당장 취해야 할 구체적인 행동(답장 텀, 답장 여부)"과 "실제 보낼 수 있는 예시 멘트"를 직관적으로 제시할 것.
"""
        payload = {
            "contents": [{"parts": [{"text": consult_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}
        }
        data_bytes = json.dumps(payload).encode('utf-8')

        for model_name in ENGINE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    parts = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    return "".join([p.get("text", "") for p in parts if "text" in p]).strip()
            except Exception:
                continue
        return "상담 엔진 연결에 실패했습니다. 잠시 후 다시 질문해주세요."