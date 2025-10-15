import streamlit as st
from datetime import datetime, timedelta
import calendar

# 과목 리스트
subjects = [
    "국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육",
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

# 날짜 선택 및 달력 (주말 제외)
st.title("🎈 오늘의 시간표")
today = st.date_input("날짜를 선택하세요", datetime.now())
calendar_expander = st.expander("📅 한달 시간표 보기")
with calendar_expander:
    st.write("날짜를 클릭하면 해당 날짜의 시간표를 볼 수 있습니다.")
    month = today.month
    year = today.year
    cal = calendar.monthcalendar(year, month)
    # 주말(토,일)은 제외
    selectable_days = []
    for week in cal:
        for i, day in enumerate(week):
            if day != 0 and i < 5:  # 0~4: 월~금
                selectable_days.append(day)
    selected_day = st.selectbox("날짜 선택(주말 제외)", selectable_days)
    # 실제 기록은 세션 상태나 DB에 저장 필요

# 세션 상태 초기화
if "timetable" not in st.session_state:
    st.session_state["timetable"] = {}

# 진행도 계산 (모든 교시+점심시간)
progress_steps = len([p for p in periods if p["name"] != "점심시간"]) + 1  # 6교시+점심
progress = 0

# 시간표 입력
for idx, period in enumerate(periods):
    # 점심시간 처리
    if period["name"] == "점심시간":
        st.markdown(f"### {period['name']} ({period['time']})")
        col1, col2, col3 = st.columns(3)
        with col1:
            lunch_eat = st.checkbox("🍱 식사", key=f"lunch_eat_{today}")
        with col2:
            lunch_brush = st.checkbox("🪥 양치", key=f"lunch_brush_{today}")
        with col3:
            lunch_done = st.button("✅ 점심시간 완료", key=f"lunch_done_{today}")
        lunch_ready = lunch_eat and lunch_brush and lunch_done
        box_color = "#eaffea" if lunch_ready else "#fff"
        st.markdown(
            f'<div style="border:2px solid #4CAF50; background:{box_color}; padding:10px;">'
            f'점심시간 {"완료!" if lunch_ready else "진행중"}</div>',
            unsafe_allow_html=True
        )
        if lunch_ready:
            progress += 1
        continue

    # 교시별 입력
    subject_key = f"subject_{idx}_{today}"
    ready_key = f"ready_{idx}_{today}"
    done_key = f"done_{idx}_{today}"
    supplies_key = f"supplies_{idx}_{today}"

    # 과목 선택
    st.markdown(f"### {period['name']} ({period['time']})")
    col1, col2, col3, col4 = st.columns([2,2,2,2])
    with col1:
        subject = st.selectbox("과목 선택", subjects, key=subject_key)
    with col2:
        place = st.text_input("장소 입력", key=f"place_{idx}_{today}")

    # 준비물 동적 변경
    if "supplies_state" not in st.session_state:
        st.session_state["supplies_state"] = {}
    prev_subject = st.session_state["supplies_state"].get(subject_key, "")
    default_supplies = get_default_supplies(subject)
    # 과목이 바뀌면 준비물도 기본값으로 변경
    if prev_subject != subject:
        st.session_state[supplies_key] = ", ".join(default_supplies)
        st.session_state["supplies_state"][subject_key] = subject
    with col3:
        supplies = st.text_input(
            "준비물(콤마로 구분)", st.session_state.get(supplies_key, ", ".join(default_supplies)), key=supplies_key
        )
        supplies_list = [s.strip() for s in supplies.split(",") if s.strip()]
        ready = st.checkbox("👜 준비물 챙김", key=ready_key)
    with col4:
        done = st.checkbox("✅ 수업 준비완료", key=done_key)
    # 박스 색상 결정
    box_color = "#eaffea" if done else "#fff"
    border_color = "#4CAF50" if done else "#ccc"
    st.markdown(
        f'<div style="border:2px solid {border_color}; background:{box_color}; padding:10px; margin-bottom:10px;">'
        f'{period["name"]} - {subject} @ {place} (준비물: {", ".join(supplies_list)})<br>'
        f'{"✅ 준비 완료!" if done else "⏳ 준비중"}</div>',
        unsafe_allow_html=True
    )
    if done:
        progress += 1

    # 시간표 저장
    st.session_state["timetable"][f"{today}_{period['name']}"] = {
        "subject": subject,
        "place": place,
        "supplies": supplies_list,
        "ready": ready,
        "done": done
    }

# 전체 진행도 표시
st.progress(progress / progress_steps, text=f"진행도: {progress}/{progress_steps}")

# 오늘 하루 코멘트
st.markdown("### 오늘 하루 일과 코멘트")
comment = st.text_area("코멘트를 남겨보세요! (이모티콘 입력 가능 😊)", key=f"comment_{today}")

# 기록 저장 (실제 앱에서는 DB나 파일 저장 필요)
st.session_state["timetable"][f"{today}_comment"] = comment

# 달력에서 선택한 날짜의 시간표 보기 (주말 제외)
with calendar_expander:
    st.markdown(f"#### {year}-{month:02d}-{selected_day:02d} 시간표")
    for idx, period in enumerate(periods):
        key = f"{datetime(year, month, selected_day).date()}_{period['name']}"
        record = st.session_state["timetable"].get(key)
        if record:
            st.write(f"{period['name']} - {record['subject']} @ {record['place']} (준비물: {', '.join(record['supplies'])})")
        else:
            st.write(f"{period['name']} - 기록 없음")
