import streamlit as st
from datetime import datetime, time, timedelta
import uuid

# 제목
st.title("주말 일과표")

# 날짜 선택 및 요일 표시
selected_date = st.date_input("날짜를 선택하세요", datetime.now())
date_key = selected_date.isoformat()
weekday_labels = ["월", "화", "수", "목", "금", "토", "일"]
st.markdown(f"#### {selected_date.month}월 {selected_date.day}일 {weekday_labels[selected_date.weekday()]}요일")

# 세션키: 날짜별 오전/오후 리스트 유지 (각 항목에 고유 id 포함)
morning_key = f"morning_tasks_{date_key}"
afternoon_key = f"afternoon_tasks_{date_key}"

def make_item(title="", place="", time_str=""):
    return {"id": str(uuid.uuid4()), "title": title, "place": place, "time": time_str}

# 초기 항목: title은 빈 문자열로 두어 placeholder(회색 안내)가 보이게 함
if morning_key not in st.session_state:
    st.session_state[morning_key] = [make_item("", "", "")]
if afternoon_key not in st.session_state:
    st.session_state[afternoon_key] = [make_item("", "", "")]

# 시간 옵션 생성 (15분 간격)
def make_time_options(section):
    opts = []
    if section == "m":  # 오전: 06:00 ~ 11:45
        start = time(6,0)
        end_hour = 11
    else:  # 오후: 12:00 ~ 21:45
        start = time(12,0)
        end_hour = 21
    cur = datetime.combine(datetime.today(), start)
    while cur.time().hour <= end_hour:
        opts.append(cur.time().strftime("%H:%M"))
        cur += timedelta(minutes=15)
    return opts

def parse_time_str(tstr):
    try:
        h, m = tstr.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 10**9  # very large -> put at end

def sort_tasks_by_time(state_key):
    lst = list(st.session_state[state_key])
    # stable sort by parse_time_str (empty/invalid times go to end)
    lst.sort(key=lambda item: parse_time_str(item.get("time", "") or ""))
    st.session_state[state_key] = lst

def render_tasks(section_label, state_key, prefix):
    cols = st.columns([8,1])
    with cols[0]:
        # 요청에 따라 섹션 제목을 '오전일과' / '오후일과' 형태로 표시
        st.markdown(f"### {section_label}")  # section_label 전달시 "오전일과" 또는 "오후일과" 로 호출하세요
    with cols[1]:
        if st.button("추가", key=f"add_{prefix}_{date_key}"):
            st.session_state[state_key].append(make_item("", "", ""))

    time_opts = make_time_options(prefix)

    # 헤더 행: 각 칸 위에 레이블 표시 (일과명 / 장소명 / 시간)
    # CSS로 레이블과 입력박스의 간격을 줄여 라벨이 입력박스와 가깝게 보이도록 함
    st.markdown(
        """
        <style>
        .ws-small-label { margin: 0 0 4px 0; font-weight:600; font-size:14px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    header_cols = st.columns([3,3,3,1])
    with header_cols[0]:
        st.markdown('<div class="ws-small-label">일과명</div>', unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown('<div class="ws-small-label">장소명</div>', unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown('<div class="ws-small-label">시간</div>', unsafe_allow_html=True)
    with header_cols[3]:
        st.markdown('')

    # 렌더링: 각 항목의 위젯 key에 id 사용 -> 정렬 시 입력값 유지
    for item in list(st.session_state[state_key]):
        item_id = item["id"]
        container = st.container()
        with container:
            c_title, c_place, c_time, c_actions = st.columns([3,3,3,1])

            # 일과명: 선택항목 제거, 텍스트 입력만 제공. placeholder로 회색 안내 표시
            with c_title:
                title_val = st.text_input(
                    "",  # 라벨은 위 헤더에서 처리
                    value=item.get("title", ""),
                    placeholder="어떤 계획이 있나요?",
                    key=f"title_{prefix}_{item_id}_{date_key}"
                )
                for it in st.session_state[state_key]:
                    if it["id"] == item_id:
                        it["title"] = title_val
                        break

            # 장소 칸: 단순 텍스트 입력 (placeholder: '어디에서 하나요?')
            with c_place:
                place_val = st.text_input(
                    "",
                    value=item.get("place", ""),
                    placeholder="어디에서 하나요?",
                    key=f"place_{prefix}_{item_id}_{date_key}"
                )
                for it in st.session_state[state_key]:
                    if it["id"] == item_id:
                        it["place"] = place_val
                        break

            # 시간 칸
            with c_time:
                default_time = item.get("time") or (time_opts[0] if time_opts else "")
                idx = time_opts.index(default_time) if default_time in time_opts else 0
                selected_time = st.selectbox(
                    "",
                    time_opts,
                    index=idx,
                    key=f"time_{prefix}_{item_id}_{date_key}"
                )
                for it in st.session_state[state_key]:
                    if it["id"] == item_id:
                        it["time"] = selected_time
                        break

            # 삭제 버튼
            with c_actions:
                del_key = f"del_{prefix}_{item_id}_{date_key}"
                if st.button("삭제", key=del_key):
                    st.session_state[state_key] = [it for it in st.session_state[state_key] if it["id"] != item_id]

    # 입력/삭제 후에는 시간 기준으로 자동 정렬
    sort_tasks_by_time(state_key)

# 렌더링: 섹션 라벨을 요청대로 설정
render_tasks("오전일과", morning_key, "m")
st.markdown('<hr style="border-top: 2px dashed #bbb;">', unsafe_allow_html=True)
render_tasks("오후일과", afternoon_key, "a")

# 코멘트 저장
st.markdown("### 오늘 하루는 어땠나요?")
comment = st.text_area("", key=f"comment_{date_key}")
st.session_state["timetable"] = st.session_state.get("timetable", {})
st.session_state["timetable"][f"{date_key}_comment"] = comment