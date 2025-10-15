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
        return ["운동화", "체육복"]
    return ["교과서", "필기도구"]

# 날짜 선택 및 달력
st.title("🎈 오늘의 시간표")
today = st.date_input("날짜를 선택하세요", datetime.now())
calendar_expander = st.expander("📅 한달 시간표 보기")
with calendar_expander:
    st.write("날짜를 클릭하면 해당 날짜의 시간표를 볼 수 있습니다.")
    # 간단한 달력 표시
    month = today.month
    year = today.year
    cal = calendar.monthcalendar(year, month)
    selected_day = st.selectbox("날짜 선택", [day for week in cal for day in week if day != 0])
    # 실제 기록은 세션 상태나 DB에 저장 필요

# 세션 상태 초기화
if "timetable" not in st.session_state:
    st.session_state["timetable"] = {}

# 진행도 계산
progress_steps = 2  # 점심, 6교시
progress = 0

# 시간표 입력
for idx, period in enumerate(periods):
    if period["name"] == "점심시간":
        lunch_done = st.checkbox("🍱 점심시간 완료", key=f"lunch_{today}")
        if lunch_done:
            progress += 1
        st.info(f"{period['name']} ({period['time']})")
        continue

    st.markdown(f"### {period['name']} ({period['time']})")
    col1, col2, col3, col4 = st.columns([2,2,2,2])

    with col1:
        subject = st.selectbox(
            "과목 선택", subjects, key=f"subject_{idx}_{today}"
        )
    with col2:
        place = st.text_input("장소 입력", key=f"place_{idx}_{today}")
    with col3:
        default_supplies = get_default_supplies(subject)
        supplies = st.text_input(
            "준비물(콤마로 구분)", ", ".join(default_supplies), key=f"supplies_{idx}_{today}"
        )
        supplies_list = [s.strip() for s in supplies.split(",") if s.strip()]
        ready = st.toggle("👜 준비물 챙김", key=f"ready_{idx}_{today}")
        if ready:
            st.success("준비 완료!", icon="✅")
        else:
            st.warning("준비물을 챙기세요!", icon="⚠️")
    with col4:
        done = st.button("✅ 수업 준비완료", key=f"done_{idx}_{today}")
        if done or st.session_state.get(f"done_{idx}_{today}_state", False):
            st.session_state[f"done_{idx}_{today}_state"] = True
            st.markdown(
                f'<div style="border:2px solid #4CAF50; background:#eaffea; padding:10px;">{period["name"]} 준비 완료!</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="border:2px solid #ccc; background:#fff; padding:10px;">{period["name"]} 준비중</div>',
                unsafe_allow_html=True
            )
    # 6교시 완료 체크
    if idx == 6 and (done or st.session_state.get(f"done_{idx}_{today}_state", False)):
        progress += 1

    # 시간표 저장
    st.session_state["timetable"][f"{today}_{period['name']}"] = {
        "subject": subject,
        "place": place,
        "supplies": supplies_list,
        "ready": ready,
        "done": done or st.session_state.get(f"done_{idx}_{today}_state", False)
    }

# 전체 진행도 표시
st.progress(progress / progress_steps, text=f"진행도: {progress}/{progress_steps}")

# 오늘 하루 코멘트
st.markdown("### 오늘 하루 일과 코멘트")
comment = st.text_area("코멘트를 남겨보세요! (이모티콘 입력 가능 😊)", key=f"comment_{today}")

# 기록 저장 (실제 앱에서는 DB나 파일 저장 필요)
st.session_state["timetable"][f"{today}_comment"] = comment

# 달력에서 선택한 날짜의 시간표 보기
with calendar_expander:
    st.markdown(f"#### {year}-{month:02d}-{selected_day:02d} 시간표")
    for idx, period in enumerate(periods):
        key = f"{datetime(year, month, selected_day).date()}_{period['name']}"
        record = st.session_state["timetable"].get(key)
        if record:
            st.write(f"{period['name']} - {record['subject']} @ {record['place']} (준비물: {', '.join(record['supplies'])})")
        else:
            st.write(f"{period['name']} - 기록 없음")
