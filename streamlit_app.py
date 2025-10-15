import streamlit as st
from datetime import datetime
from streamlit_drawable_canvas import st_canvas

# 과목 리스트 (진로, 정보 추가)
subjects = [
    "국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육",
    "진로", "정보",
    "특수학급(진로)", "특수학급(수학)", "특수학급(체육)", "특수학급(국어)", "특수학급(정보)"
]

# 시간표 정보
periods = [
    {"name": "1교시", "time": "09:00 ~ 09:45"},
    {"name": "2교시", "time": "09:55 ~ 10:40"},
    {"name": "3교시", "time": "10:50 ~ 11:35"},
    {"name": "4교시", "time": "11:45 ~ 12:30"},
    {"name": "점심시간", "time": "12:30 ~ 13:30"},
    {"name": "5교시", "time": "13:30 ~ 14:15"},
    {"name": "6교시", "time": "14:25 ~ 15:10"},
]

# 준비물 기본값
def get_default_supplies(subject):
    if "특수학급" in subject:
        return []
    if subject == "체육":
        return ["체육복", "운동화"]
    return ["교과서", "필기도구"]

# 진행도 표시 (항상 상단 고정)
def fixed_progress(progress, total):
    st.markdown(
        f"""
        <div style="position:fixed;top:10px;right:10px;z-index:9999;background:rgba(255,255,255,0.9);padding:8px 16px;border-radius:20px;border:1px solid #eee;box-shadow:0 2px 8px #0001;">
            🏃‍♂️ <b>진행도</b> {progress}/{total}
            <div style="width:120px;height:8px;background:#eee;border-radius:4px;overflow:hidden;margin-top:4px;">
                <div style="width:{int(progress/total*100)}%;height:100%;background:#4CAF50;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# 날짜 선택
st.title("🎈 오늘의 시간표")
today = st.date_input("날짜를 선택하세요", datetime.now())

# 세션 상태 초기화
if "timetable" not in st.session_state:
    st.session_state["timetable"] = {}

progress_steps = len([p for p in periods if p["name"] != "점심시간"]) + 1  # 6교시+점심
progress = 0

# 시간표 입력
for idx, period in enumerate(periods):
    st.markdown(f"### {period['name']} ({period['time']})")
    col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])

    # 점심시간 처리
    if period["name"] == "점심시간":
        with col1:
            lunch_eat = st.checkbox("🍱 식사", key=f"lunch_eat_{today}")
        with col2:
            lunch_brush = st.checkbox("🪥 양치", key=f"lunch_brush_{today}")
        with col3:
            lunch_done = st.checkbox("✅ 점심시간 완료", key=f"lunch_done_{today}")
        if lunch_eat and lunch_brush and lunch_done:
            progress += 1
        # 싸인란
        with col5:
            st.markdown("교사 싸인")
            st_canvas(
                key=f"sign_lunch_{today}",
                height=60,
                width=150,
                background_color="#fff",
                drawing_mode="freedraw",
                stroke_width=2,
                stroke_color="#222",
                update_streamlit=True,
            )
        continue

    subject_key = f"subject_{idx}_{today}"
    done_key = f"done_{idx}_{today}"
    supplies_key = f"supplies_{idx}_{today}"

    with col1:
        subject = st.selectbox("과목 선택", subjects, key=subject_key)
    with col2:
        place = st.text_input("장소 입력", key=f"place_{idx}_{today}")

    # 준비물 동적 변경
    if "supplies_state" not in st.session_state:
        st.session_state["supplies_state"] = {}
    prev_subject = st.session_state["supplies_state"].get(subject_key, "")
    default_supplies = get_default_supplies(subject)
    if prev_subject != subject:
        st.session_state[supplies_key] = ", ".join(default_supplies)
        st.session_state["supplies_state"][subject_key] = subject
    with col3:
        supplies = st.text_input(
            "준비물(콤마로 구분)", st.session_state.get(supplies_key, ", ".join(default_supplies)), key=supplies_key
        )
    with col4:
        done = st.checkbox("✅ 수업 준비완료", key=done_key)
        if done:
            progress += 1
    with col5:
        st.markdown("교사 싸인")
        st_canvas(
            key=f"sign_{idx}_{today}",
            height=60,
            width=150,
            background_color="#fff",
            drawing_mode="freedraw",
            stroke_width=2,
            stroke_color="#222",
            update_streamlit=True,
        )

    supplies_list = [s.strip() for s in supplies.split(",") if s.strip()]
    st.session_state["timetable"][f"{today}_{period['name']}"] = {
        "subject": subject,
        "place": place,
        "supplies": supplies_list,
        "done": done
    }

# 진행도(상단 고정)
fixed_progress(progress, progress_steps)

# 오늘 하루 코멘트
st.markdown("### 오늘 하루 일과 코멘트")
comment = st.text_area("코멘트를 남겨보세요! (이모티콘 입력 가능 😊)", key=f"comment_{today}")
st.session_state["timetable"][f"{today}_comment"] = comment
