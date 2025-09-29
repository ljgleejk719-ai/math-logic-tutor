import streamlit as st
from google import genai
from google.genai import types
import os
from datetime import datetime
# Google Sheets 연동을 위한 Streamlit Connection 추가
st.cache_data.clear() # 캐시 데이터 클리어
conn = st.connection("gsheets", type=st.connections.SnowflakeConnection)


# -----------------------------------------------------
# 1. API 설정 및 모델 초기화
# -----------------------------------------------------
api_key = "AIzaSyAU1iwa-OFdgFyiookp8Rcwez6rlNXajm4"

if not api_key:
    st.error("⚠️ API Key가 설정되지 않았습니다.")
    st.stop()

client = genai.Client(api_key=api_key)
model_name = 'gemini-2.5-flash' 
# ... (SYSTEM_INSTRUCTION 생략 - 이전 프롬프트 유지) ... 
SYSTEM_INSTRUCTION = """
당신은 고등학교 1학년 수학 '명제' 단원의 전문 튜터입니다.
당신의 목표는 학생의 논리적 사고력을 향상시키고, 스스로 오류를 발견하도록 돕는 것입니다.

[입력 명제 검토 원칙]
1. **필수어 확인**: 입력된 명제가 **'모든'** 또는 **'어떤'** 중 하나를 포함하고 있지 않다면, 답변 대신 "**명제에는 '모든' 또는 '어떤'이라는 용어를 반드시 포함해야 합니다. 다시 입력해주세요.**"라고 출력합니다.
2. **수학적 명제 한정**: 명제에 포함된 집합(자연수, 실수, 집합, 도형 등)이나 조건이 수학과 관련이 없는 경우, 답변 대신 "**수학과 관련된 명제를 입력해주세요.**"라고 출력합니다.
3. **두 가지 검토 원칙 중 하나라도 해당되면 즉시 답변을 중단하고 해당 메시지만 출력합니다.**

[학생의 입력 형식]
1. 명제: [학생이 입력한 명제] (예: 모든 자연수 x에 대해 x^2 > x 이다.)
2. 학생의 판단: [참 / 거짓]
3. 학생이 생각하는 이유/근거/반례: [학생이 직접 작성한 이유]

[당신의 피드백 원칙]
1. **정확성 확인**: 명제의 실제 참/거짓 여부를 판단합니다.
2. **사고 유도 질문 (가장 중요)**:
    * 만약 학생의 **참/거짓 판단이 틀렸거나** **제시한 이유/근거/반례가 논리적으로 잘못된 경우**, 올바른 정답이나 반례를 바로 알려주지 마세요.
    * 대신, 학생이 스스로 오류를 발견하고 생각할 수 있도록 **구체적이고 핵심을 짚는 질문**을 하나 또는 두 개 출력합니다. (예: "만약 x에 1을 대입한다면 그 조건은 참인가요?", "'어떤'의 의미는 모든 경우가 아닌 '단 하나'의 경우만 있으면 된다는 것을 기억해 보세요.")
3. **판단 일치 시 보강**:
    * **참/거짓과 이유가 모두 논리적으로 완벽할 경우**: "논리적으로 완벽해요!👏"라고 칭찬하고, 학생의 이유를 보강하는 추가 설명이나 더 일반적인 증명 원리를 제공합니다.
4. **마지막 질문**: 학생이 다음 명제를 입력하도록 유도하는 질문을 덧붙입니다.
"""


# -----------------------------------------------------
# 3. Streamlit 웹 인터페이스 구현 - 제목 수정 완료
# -----------------------------------------------------

st.set_page_config(page_title="'모든'이나 '어떤'이 포함된 명제 논리 튜터 챗봇", layout="centered")
st.title("👨‍🏫 '모든'이나 '어떤'이 포함된 명제 논리 튜터 챗봇")
st.markdown("명제를 입력하고, 본인의 판단과 이유를 적어 **즉각적인 논리 피드백**을 받아보세요. (단, 명제는 **'모든'** 또는 **'어떤'**을 반드시 포함해야 합니다.)")

# 폼 생성 (즉각적인 응답을 위해 st.form 사용)
with st.form(key='tutor_form'):
    user_proposition = st.text_input("1. 명제를 입력해 주세요. (예: 모든 자연수 x에 대해 x² > x 이다.)", key="prop_input")
    user_judgment = st.radio(
        "2. 학생의 판단은 무엇인가요?",
        ('참', '거짓'),
        index=None,
        key="judg_radio"
    )
    user_reason = st.text_area("3. 그렇게 판단한 이유/근거/반례를 써주세요. (구체적일수록 좋아요!)", key="reason_input")
    
    # 제출 버튼
    submit_button = st.form_submit_button(label='피드백 요청하기')

# 제출 버튼이 눌렸을 때 로직
if submit_button:
    if not user_proposition or not user_judgment or not user_reason:
        st.error("모든 항목(명제, 판단, 이유)을 입력해 주세요.")
        st.stop()
        
    user_message = f"""
    [학생의 입력]
    1. 명제: {user_proposition}
    2. 학생의 판단: {user_judgment}
    3. 학생이 생각하는 이유/근거/반례: {user_reason}
    
    위 입력에 대해 엄격한 피드백 원칙을 따라 논리적인 튜터링 피드백을 제공해 주세요.
    """
    
    with st.spinner('✨ AI 튜터가 논리를 분석하고 피드백을 생성 중입니다...'):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION
                )
            )
            
            ai_feedback = response.text # AI 피드백 저장
            
            # --- 데이터 저장 로직 (추가된 핵심 부분) ---
            # 1. 시트 이름은 'Sheet1' (Google Sheets 기본값)을 사용합니다.
            # 2. 행 추가 (append) 명령을 사용하여 Google Sheets에 데이터 기록
            conn.append('Sheet1', data=[
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # 시간
                    user_proposition, 
                    user_judgment, 
                    user_reason, 
                    ai_feedback
                ]
            ])
            # ---------------------------------------------

            st.success("🎉 피드백이 도착했습니다!")
            st.markdown(ai_feedback)
            
        except Exception as e:
            st.error(f"API 호출 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. (오류: {e})")
