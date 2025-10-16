import streamlit as st
from datetime import datetime, timedelta
from streamlit_drawable_canvas import st_canvas
import calendar

# 과목 리스트 (특수학급 명칭 변경)
subjects = [
    "국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육",
    "진로", "정보",
    "특수(진로)", "특수(수학)", "특수(체육)", "특수(국어)", "특수(정보)"
]

# 기본 시간표 정보
default_periods = [
    {"name": "1교시", "time": "09:00 ~ 09:45"},
    {"name": "2교시", "time": "09:55 ~ 10:40"},
    {"name": "3교시", "time": "10:50 ~ 11:35"},
    {"name": "4교시", "time": "11:45 ~ 12:30"},
    {"name": "점심시간", "time": "12:30 ~ 13:30"},
    {"name": "5교시", "time": "13:30 ~ 14:15"},
    {"name": "6교시", "time": "14:25 ~ 15:10"},
]

# 세션 상태에 시간표 정보 저장
if "periods" not in st.session_state:
    st.session_state["periods"] = default_periods.copy()

# 시간표 수정 탭 (추가/삭제)
with st.expander("⏰ 시간표 수정/교시 추가/삭제"):
    periods = st.session_state["periods"]
    for i, period in enumerate(periods):
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            periods[i]["name"] = st.text_input(f"{i+1}교시 이름", period["name"], key=f"edit_name_{i}")
        with col2:
            periods[i]["time"] = st.text_input(f"{i+1}교시 시간", period["time"], key=f"edit_time_{i}")
        with col3:
            if st.button("삭제", key=f"delete_period_{i}") and len(periods) > 1:
                periods.pop(i)
                st.experimental_rerun()
    if st.button("교시 추가"):
        periods.append({"name": f"{len(periods)+1}교시", "time": "시간 입력"})
    st.session_state["periods"] = periods

# 준비물 기본값 함수 정의
def get_default_supplies(subject):
    if "특수" in subject:
        return []
    if subject == "체육":
        return ["체육복", "운동화"]
    return ["교과서", "필기도구"]

# 한글 요일
weekday_labels = ["월", "화", "수", "목", "금", "토", "일"]

# 날짜 선택(달력)
selected_date = st.date_input("날짜를 선택하세요", datetime.now())
year, month, day = selected_date.year, selected_date.month, selected_date.day
weekday = selected_date.weekday()  # 0=월, 6=일

# 선택한 날짜 정보만 표시
st.markdown(f"#### {month}월 {day}일 {weekday_labels[weekday]}요일")

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

# 세션 상태 초기화
if "timetable" not in st.session_state:
    st.session_state["timetable"] = {}

periods = st.session_state["periods"]
progress_steps = len([p for p in periods if p["name"] != "점심시간"])
progress = 0

# 시간표 입력
for idx, period in enumerate(periods):
    st.markdown(f"### {period['name']} ({period['time']})")
    col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])

    # 점심시간 처리 (교사싸인 없음)
    if period["name"] == "점심시간":
        with col1:
            lunch_eat = st.checkbox("🍱 식사", key=f"lunch_eat_{selected_date}_{idx}")
        with col2:
            lunch_brush = st.checkbox("🪥 양치", key=f"lunch_brush_{selected_date}_{idx}")
        with col3:
            lunch_done = st.checkbox("✅ 점심시간 완료", key=f"lunch_done_{selected_date}_{idx}")
        if lunch_eat and lunch_brush and lunch_done:
            progress += 1
        # 점선 구분선
        st.markdown('<hr style="border-top: 2px dashed #bbb;">', unsafe_allow_html=True)
        continue

    subject_key = f"subject_{idx}_{selected_date}"
    done_key = f"done_{idx}_{selected_date}"
    supplies_key = f"supplies_{idx}_{selected_date}"
    ready_key = f"ready_{idx}_{selected_date}"

    with col1:
        subject = st.selectbox("과목 선택", subjects, key=subject_key)
    with col2:
        place = st.text_input("장소 입력", key=f"place_{idx}_{selected_date}")

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
            "준비물", st.session_state.get(supplies_key, ", ".join(default_supplies)), key=supplies_key
        )
        supplies_list = [s.strip() for s in supplies.split(",") if s.strip()]
        ready = st.checkbox("준비물 완료", key=ready_key)
    with col4:
        done = st.checkbox("수업 준비 완료", key=done_key)
        if done:
            progress += 1
    with col5:
        st.markdown("교사 확인")
        st_canvas(
            key=f"sign_{idx}_{selected_date}",
            height=60,
            width=150,
            background_color="#fff",
            drawing_mode="freedraw",
            stroke_width=2,
            stroke_color="#222",
            update_streamlit=True,
        )

    st.session_state["timetable"][f"{selected_date}_{period['name']}"] = {
        "subject": subject,
        "place": place,
        "supplies": supplies_list,
        "ready": ready,
        "done": done
    }
    # 점선 구분선
    st.markdown('<hr style="border-top: 2px dashed #bbb;">', unsafe_allow_html=True)

# 진행도(상단 고정)
fixed_progress(progress, progress_steps)

# 오늘 하루 코멘트
st.markdown("### 오늘 하루는 어땠나요?")
comment = st.text_area("", key=f"comment_{selected_date}")
st.session_state["timetable"][f"{selected_date}_comment"] = comment
