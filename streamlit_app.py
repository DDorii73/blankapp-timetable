import streamlit as st
from datetime import datetime, timedelta
from streamlit_drawable_canvas import st_canvas
import calendar
import numpy as np
from PIL import Image
import base64
# 서명 영역 크기 상수 (잠금 전/후 동일하게 유지)
SIGN_W = 200
SIGN_H = 120

# 캔버스 요소에 대해 강제 스타일 적용 — 페이지 내 canvas 요소 크기/테두리 동일화
st.markdown(
    f"""
    <style>
    /* 앱 내의 모든 canvas에 대해 고정 크기/테두리 적용 (st_canvas가 생성한 canvas도 포함) */
    canvas {{
        width: {SIGN_W}px !important;
        height: {SIGN_H}px !important;
        border: 1px solid #ddd !important;
        box-sizing: border-box !important;
        display: block;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# 과목 리스트 (특수학급 명칭 변경)
subjects = [
    "국어", "영어", "수학", "사회", "과학", "음악", "미술", "체육",
    "진로", "정보", "역사",
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
    # 삭제 시 st.experimental_rerun() 사용하지 않도록 변경.
    # 버튼 클릭 시 세션 상태를 갱신하고 루프를 즉시 빠져나가도록 하여 안전하게 삭제 처리합니다.
    deleted = False
    for i, period in enumerate(periods):
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            periods[i]["name"] = st.text_input(f"{i+1}교시 이름", period["name"], key=f"edit_name_{i}")
        with col2:
            periods[i]["time"] = st.text_input(f"{i+1}교시 시간", period["time"], key=f"edit_time_{i}")
        with col3:
            if st.button("삭제", key=f"delete_period_{i}") and len(periods) > 1:
                periods.pop(i)
                # 세션 상태에 반영
                st.session_state["periods"] = periods
                deleted = True
                # 루프 중간 변경으로 인한 불일치 방지를 위해 루프를 빠져나감
                break
    # 삭제가 발생했으면 이후 코드는 갱신된 st.session_state["periods"] 기반으로 다시 실행되며,
    # 별도의 experimental_rerun 호출은 필요하지 않습니다.
    if st.button("교시 추가"):
        periods.append({"name": f"{len(periods)+1}교시", "time": "시간 입력"})
    st.session_state["periods"] = periods

# 준비물 기본값 함수 정의
def get_default_supplies(subject):
    # '특수' 과목은 필기도구로 매핑
    if "특수" in subject:
        return ["필기도구"]
    if subject == "체육":
        return ["체육복", "운동화"]
    return ["교과서", "필기도구"]

# 한글 요일
weekday_labels = ["월", "화", "수", "목", "금", "토", "일"]

# 날짜 선택(달력)
st.title("오늘의 시간표")
selected_date = st.date_input("날짜를 선택하세요", datetime.now())
year, month, day = selected_date.year, selected_date.month, selected_date.day
weekday = selected_date.weekday()  # 0=월, 6=일

# 선택한 날짜 정보만 표시
st.markdown(f"#### {month}월 {day}일 {weekday_labels[weekday]}요일")

# 진행도 표시 (항상 상단 고정) — total이 0일 때 보호 추가
def fixed_progress(progress, total):
    if total <= 0:
        return
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
        # 안정적인 키 사용
        lunch_eat_key = f"lunch_eat_{selected_date}_{idx}"
        lunch_brush_key = f"lunch_brush_{selected_date}_{idx}"
        lunch_done_key = f"lunch_done_{selected_date}_{idx}"

        # 식사, 양치 체크박스 생성 (세션이 자동으로 관리)
        with col1:
            st.checkbox("🍱 식사", key=lunch_eat_key)
        with col2:
            st.checkbox("🪥 양치", key=lunch_brush_key)

        # 현재 상태 읽기
        eat_val = st.session_state.get(lunch_eat_key, False)
        brush_val = st.session_state.get(lunch_brush_key, False)

        # 둘 다 체크되어 있을 때만 자동으로 점심 완료가 활성화되도록 함
        lunch_done_val = bool(eat_val and brush_val)

        # 세션값을 위젯 생성 전에 설정(자동 반영, 사용자가 직접 조작 불가)
        st.session_state[lunch_done_key] = lunch_done_val

        # 완료 표시: 활성화이면 초록색 체크 텍스트, 아니면 회색 대시 (가운데 정렬)
        with col3:
            if lunch_done_val:
                st.markdown(
                    "<div style='display:flex;align-items:center;justify-content:center;height:28px;color:#2e7d32;font-weight:700;'>✅ 점심시간 완료</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='display:flex;align-items:center;justify-content:center;height:28px;color:#bbb;font-weight:700;'>— 점심시간 완료</div>",
                    unsafe_allow_html=True,
                )

        # 완료 여부로 진행도 계산
        if st.session_state.get(lunch_done_key, False):
            progress += 1

        # 점선 구분선
        st.markdown('<hr style="border-top: 2px dashed #bbb;">', unsafe_allow_html=True)
        continue

    subject_key = f"subject_{idx}_{selected_date}"
    done_key = f"done_{idx}_{selected_date}"
    supplies_key = f"supplies_{idx}_{selected_date}"
    ready_key = f"ready_{idx}_{selected_date}"
    move_done_key = f"move_done_{idx}_{selected_date}"

    with col1:
        subject = st.selectbox("과목 선택", subjects, key=subject_key)
    with col2:
        # 과목에 따라 자동으로 장소를 채움 (요구사항 반영)
        def get_default_place_for_subject(subj):
            # 국어, 영어, 수학, 사회, 진로, 역사 -> 2-5
            if subj in ["국어", "영어", "수학", "사회", "진로", "역사"]:
                return "2-5"
            # '특수'가 들어가면 모두 특수학급
            if "특수" in subj:
                return "특수학급"
            # 기타 매핑
            if subj == "정보":
                return "컴퓨터실"
            if subj == "체육":
                return "운동장, 체육관"
            if subj == "미술":
                return "미술실"
            if subj == "음악":
                return "음악실"
            if subj == "과학":
                return "과학실"
            return ""

        auto_place = get_default_place_for_subject(subject)
        place_key = f"place_{idx}_{selected_date}"
        prev_subj_key = f"subject_prev_{idx}_{selected_date}"

        # 이전 과목을 기록해 두어 과목 변경 시 장소를 자동 갱신하도록 함
        if prev_subj_key not in st.session_state:
            st.session_state[prev_subj_key] = subject

        # 과목이 변경되면 자동 장소로 덮어쓰기
        if st.session_state.get(prev_subj_key) != subject:
            st.session_state[place_key] = auto_place
            st.session_state[prev_subj_key] = subject

        # widget 생성 전에 기본값 보장
        if place_key not in st.session_state:
            st.session_state[place_key] = auto_place

        # 라벨 '장소' 보이도록 수정, 사용자가 직접 수정 가능
        place = st.text_input("장소", key=place_key)

        # 장소 밑에 '이동 완료' 체크박스 추가
        # 체크 상태는 세션에 보관되어 재렌더링 시 유지됩니다.
        if move_done_key not in st.session_state:
            st.session_state[move_done_key] = False
        # st.checkbox이 key를 사용하면 st.session_state에 자동으로 값이 들어갑니다.
        # 따라서 위젯 생성 후 st.session_state[...]를 직접 다시 쓰면 StreamlitAPIException이 발생합니다.
        move_done = st.checkbox("이동 완료", value=st.session_state.get(move_done_key, False), key=move_done_key)

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
        # move_done(이동 완료)와 ready(준비물 완료)가 모두 체크되어야만 수업준비완료가 활성화되도록 함
        move_done_val = st.session_state.get(move_done_key, False)
        ready_val = st.session_state.get(ready_key, False)

        # 위젯 생성 전에 done 상태를 원본 상태(move_done AND ready)로 설정하여 자동 동기화
        if done_key not in st.session_state:
            st.session_state[done_key] = False
        st.session_state[done_key] = bool(move_done_val and ready_val)

        # 체크박스와 라벨의 줄 높이를 맞춰 중앙 정렬되게 표시
        chk_col, lbl_col = st.columns([1, 4])
        with chk_col:
            # 위에서 세션에 셋팅한 값으로 렌더링 (사용자가 임의로 변경하면 다음 rerun에서 다시 동기화됩니다)
            done = st.checkbox("", key=done_key)
        with lbl_col:
            # 라벨을 flex로 감싸고 align-items:center로 체크박스와 수직 중앙정렬
            if st.session_state.get(done_key, False):
                label_html = "<div style='display:flex;align-items:center;height:28px;color:#2e7d32;font-weight:700;'>수업준비완료</div>"
            else:
                label_html = "<div style='display:flex;align-items:center;height:28px;color:#444;'>수업 준비 완료</div>"
            st.markdown(label_html, unsafe_allow_html=True)
        if st.session_state.get(done_key, False):
            progress += 1
    with col5:
        st.markdown("교사 확인")

        # 키/초기화
        date_key = selected_date.isoformat() if hasattr(selected_date, "isoformat") else str(selected_date)
        sign_img_key = f"sign_img_{idx}_{date_key}"
        sign_locked_key = f"sign_locked_{idx}_{date_key}"
        canvas_key = f"sign_canvas_{idx}_{date_key}"
        lock_icon_key = f"lock_icon_{idx}_{date_key}"
        unlock_icon_key = f"unlock_icon_{idx}_{date_key}"

        if sign_locked_key not in st.session_state:
            st.session_state[sign_locked_key] = False
        if sign_img_key not in st.session_state:
            st.session_state[sign_img_key] = None

        saved_img = st.session_state.get(sign_img_key)

        # 잠금 상태: 이미지 박스(편집 불가) — 하나의 칸만 표시
        if st.session_state.get(sign_locked_key, False):
            if saved_img is not None:
                try:
                    from io import BytesIO
                    buf = BytesIO()
                    saved_img.convert("RGBA").save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    st.markdown(
                        f"""
                        <div style="width:200px;height:120px;border:1px solid #ddd;background:#fff;display:flex;align-items:center;justify-content:center;box-sizing:border-box;overflow:hidden;">
                            <img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:contain;display:block;"/>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.image(saved_img, width=200)
            else:
                st.markdown("<div style='width:200px;height:120px;border:1px dashed #ccc;display:flex;align-items:center;justify-content:center;color:#999;'>저장된 서명이 없습니다.</div>", unsafe_allow_html=True)

            if st.button("🔓 잠금 해제", key=unlock_icon_key):
                st.session_state[sign_locked_key] = False
        else:
            # 편집 가능 상태: 캔버스 하나만 노출 (200x120)
            canvas_result = st_canvas(
                key=canvas_key,
                height=120,
                width=200,
                background_color="#ffffff",
                background_image=None,
                drawing_mode="freedraw",
                stroke_width=2,
                stroke_color="#222",
                update_streamlit=True,
            )

            # 캔버스 결과를 안전하게 PIL로 변환해 저장
            if canvas_result is not None and getattr(canvas_result, "image_data", None) is not None:
                try:
                    arr = np.array(canvas_result.image_data)
                    if arr.dtype.kind == "f":
                        if arr.max() <= 1.01:
                            arr = (arr * 255).astype(np.uint8)
                        else:
                            arr = arr.astype(np.uint8)
                    else:
                        arr = arr.astype(np.uint8)
                    if arr.ndim == 3 and arr.shape[2] == 3:
                        alpha = np.full((arr.shape[0], arr.shape[1], 1), 255, dtype=np.uint8)
                        arr = np.concatenate([arr, alpha], axis=2)
                    pil_img = Image.fromarray(arr).convert("RGBA")
                    st.session_state[sign_img_key] = pil_img
                except Exception:
                    st.error("서명 이미지 변환에 실패했습니다.")

            # 잠금 버튼: 서명이 존재할 때만 잠금 가능
            if st.button("🔒 잠금", key=lock_icon_key):
                if st.session_state.get(sign_img_key) is not None:
                    st.session_state[sign_locked_key] = True
                else:
                    st.warning("먼저 서명을 그려주세요.")

        st.session_state["timetable"][f"{selected_date}_{period['name']}"] = {
            "subject": subject,
            "place": place,
            "supplies": supplies_list,
            "ready": ready,
            "done": done,
            "move_done": st.session_state.get(move_done_key, False),
            # sign info kept in separate sign_img_key / sign_locked_key
        }
    # 점선 구분선
    st.markdown('<hr style="border-top: 2px dashed #bbb;">', unsafe_allow_html=True)

# 진행도(상단 고정)
fixed_progress(progress, progress_steps)

# 오늘 하루 코멘트
st.markdown("### 오늘 하루는 어땠나요?")
comment = st.text_area("", key=f"comment_{selected_date}")
st.session_state["timetable"][f"{selected_date}_comment"] = comment

# (시간표 루프가 끝난 직후, fixed_progress 호출 전에 아래 코드를 추가)
st.markdown("### 오늘 하루 요약")
st.caption("오늘 학교 생활을 요약합니다(장소 이동/준비물/선생님 확인)")

date_key_iso = selected_date.isoformat() if hasattr(selected_date, "isoformat") else str(selected_date)

# 헤더 (칸 너비를 같게)
h1, h2, h3, h4 = st.columns([1,1,1,1])
with h1:
    st.markdown("**교시[교과]**")
with h2:
    st.markdown("**이동**")
with h3:
    st.markdown("**준비물**")
with h4:
    st.markdown("**선생님확인**")

# 각 교시 요약 행 생성 (점심시간 제외)
for idx, period in enumerate(periods):
    if period["name"] == "점심시간":
        continue

    # 원본 키들 (메인 루프와 동일한 키 형식 사용)
    subj_key = f"subject_{idx}_{selected_date}"
    move_done_key = f"move_done_{idx}_{selected_date}"
    ready_key = f"ready_{idx}_{selected_date}"
    sign_img_key = f"sign_img_{idx}_{date_key_iso}"
    sign_locked_key = f"sign_locked_{idx}_{date_key_iso}"

    # 원본 상태 읽기 (요약은 오로지 원본 상태만 반영)
    subj_val = st.session_state.get(subj_key, "")
    move_val = bool(st.session_state.get(move_done_key, False))
    ready_val = bool(st.session_state.get(ready_key, False))
    # 선생님 확인은 "이미지 존재 AND 잠금 버튼이 눌린 경우"에만 활성화되도록 변경
    sign_val = bool(st.session_state.get(sign_locked_key, False) and st.session_state.get(sign_img_key) is not None)

    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        # "1교시[국어]" 형식으로 표시
        st.markdown(f"{period['name']} [{subj_val}]")
    # 체크 표시들은 모두 가운데 정렬로 표시
    with c2:
        if move_val:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:24px;color:#2e7d32;font-weight:700;'>✔</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:24px;color:#bbb;font-weight:700;'>—</div>", unsafe_allow_html=True)
    with c3:
        if ready_val:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:24px;color:#2e7d32;font-weight:700;'>✔</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:24px;color:#bbb;font-weight:700;'>—</div>", unsafe_allow_html=True)
    with c4:
        # 선생님 확인도 가운데 정렬된 초록 체크로 표시 (읽기 전용: 조작 불가)
        if sign_val:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:24px;color:#2e7d32;font-weight:700;'>✔</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:24px;color:#bbb;font-weight:700;'>—</div>", unsafe_allow_html=True)