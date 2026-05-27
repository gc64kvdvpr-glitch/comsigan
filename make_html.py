import asyncio
import datetime
import re
import requests
from typing import List
from pycomcigan.timetable import TimeTable, TimeTableData, Lecture

# ==========================================
# 🔧 Comcigan API Monkey Patches for Stability
# ==========================================

def patched_get_comcigan_codes() -> tuple:
    url = 'http://comci.net:4082/st'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.encoding = 'euc-kr'
    content = response.text
    
    comcigan_code_match = re.search(r'\./[0-9]+\?[0-9]+l', content)
    comcigan_code = comcigan_code_match.group(0)[1:] if comcigan_code_match else ""
    
    code0_match = re.search(r"sc_data\('([0-9]+)_", content)
    code0 = code0_match.group(1) if code0_match else ""
    
    code1_match = re.search(r'성명=(?:Q성명\()?자료\.자료([0-9]+)', content)
    code1 = code1_match.group(1) if code1_match else ""
    if not code1:
        code1_backup = re.search(r'성명=자료\.자료([0-9]+)', content)
        code1 = code1_backup.group(1) if code1_backup else ""
        
    code2_match = re.search(r'자료\.자료([0-9]+)\[sb\]', content)
    code2 = code2_match.group(1) if code2_match else ""
    
    code3_match = re.search(r'=H시간표\.자료([0-9]+)', content)
    code3 = code3_match.group(1) if code3_match else ""
    
    code4_match = re.search(r'일일자료=Q자료\(자료\.자료([0-9]+)', content)
    code4 = code4_match.group(1) if code4_match else ""
    
    code5_match = re.search(r'원자료=Q자료\(자료\.자료([0-9]+)', content)
    code5 = code5_match.group(1) if code5_match else ""
    
    return comcigan_code, code0, code1, code2, code3, code4, code5

def clean_period_val(val) -> int:
    if isinstance(val, str):
        cleaned = re.sub(r'\D', '', val)
        return int(cleaned) if cleaned else 0
    elif isinstance(val, (int, float)):
        return int(val)
    return 0

def patched_create_period_data(period: int, day: int, class_data: List,
                               original_class: List, teacher_list: List[str],
                               subject_list: List[str]) -> TimeTableData:
    original_period_raw = 0
    if (day < len(original_class) and
            len(original_class[day]) > 0 and
            period <= original_class[day][0] and
            period < len(original_class[day])):
        original_period_raw = original_class[day][period]

    current_period_raw = 0
    if (day < len(class_data) and
            len(class_data[day]) > 0 and
            period <= class_data[day][0] and
            period < len(class_data[day])):
        current_period_raw = class_data[day][period]

    original_period = clean_period_val(original_period_raw)
    current_period = clean_period_val(current_period_raw)

    original_lecture = None
    if current_period != original_period and original_period != 0:
        original_lecture = Lecture(
            period=period,
            subject=subject_list[original_period // 1000] if original_period // 1000 < len(subject_list) else "",
            teacher=teacher_list[original_period % 100] if original_period % 100 < len(teacher_list) else ""
        )

    subject_name = ""
    teacher_name = ""

    if current_period != 0:
        subject_idx = current_period // 1000
        teacher_idx = current_period % 100

        if subject_idx < len(subject_list):
            subject_name = subject_list[subject_idx]
        if teacher_idx < len(teacher_list):
            teacher_name = teacher_list[teacher_idx]

    return TimeTableData(
        period=period,
        subject=subject_name,
        teacher=teacher_name,
        replaced=current_period_raw != original_period_raw,
        original=original_lecture
    )

TimeTable._get_comcigan_codes = staticmethod(patched_get_comcigan_codes)
TimeTable._create_period_data = staticmethod(patched_create_period_data)


# ==========================================
# ⏰ 교시별 시작 시간 설정
# ==========================================
START_TIMES = {
    1: "09:00",
    2: "10:00",
    3: "11:00",
    4: "12:00",
    5: "13:50",
    6: "14:50",
    7: "15:50",
    8: "16:50" # 혹시 몰라 8교시도 넣어둠
}

# ==========================================
# 🎨 반별 색상 설정
# ==========================================
SPECIFIC_COLORS = {
    "3-5": "#FFEBEE", 
    "1-2": "#E3F2FD", 
}

AUTO_COLORS = [
    "#F3E5F5", "#E8F5E9", "#FFFDE7", "#FBE9E7", "#E0F7FA", 
    "#FFF3E0", "#F1F8E9", "#ECEFF1", "#F9FBE7", "#EFEBE9"
]

def get_class_color(class_name):
    if class_name in SPECIFIC_COLORS:
        return SPECIFIC_COLORS[class_name]
    hash_val = sum(ord(c) for c in class_name) 
    return AUTO_COLORS[hash_val % len(AUTO_COLORS)]

# ==========================================
# 노션 위젯용 템플릿 (시간 표시 추가됨)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>시간표</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #ffffff; margin: 0; padding: 0; overflow-x: hidden;
        }}
        .container {{ width: 100%; padding: 0; }}

        /* 탭 스타일 */
        .tabs {{ display: flex; border-bottom: 1px solid #e0e0e0; background: #f9f9f9; }}
        .tab {{ 
            flex: 1; padding: 8px 0; text-align: center; font-size: 13px; color: #666; 
            cursor: pointer; transition: 0.2s; border-bottom: 2px solid transparent; 
        }}
        .tab:hover {{ background: #f0f0f0; }}
        .tab.active {{ color: #4a90e2; font-weight: bold; border-bottom: 2px solid #4a90e2; background: white; }}
        
        .content {{ display: none; }}
        .content.active {{ display: block; }}
        
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        
        th {{ 
            background-color: #f1f3f5; color: #495057; font-size: 12px; padding: 6px 2px;
            border-bottom: 1px solid #dee2e6; border-right: 1px solid #eee;
        }}
        
        td {{ 
            border-bottom: 1px solid #eee; border-right: 1px solid #eee;
            padding: 4px 2px; text-align: center; vertical-align: middle; height: 42px;
        }}

        /* 교시 열 스타일 수정 */
        .period {{ 
            background-color: #f8f9fa; 
            color: #495057; 
            font-size: 12px; 
            font-weight: bold; 
            width: 35px; 
            line-height: 1.1; /* 줄 간격 좁게 */
        }}
        
        /* 시작 시간 스타일 (추가됨) */
        .time-info {{
            display: block;
            font-size: 9px;
            color: #adb5bd;
            font-weight: normal;
            margin-top: 2px;
        }}

        .subject {{ font-size: 13px; font-weight: 600; color: #333; display: block; line-height: 1.2; }}
        .class-info {{ font-size: 10px; color: #666; display: block; margin-top: 2px; opacity: 0.8; }}
        
        th:last-child, td:last-child {{ border-right: none; }}
    </style>
    <script>
        function openTab(event, tabId) {{
            var i, x, tablinks;
            x = document.getElementsByClassName("content");
            for (i = 0; i < x.length; i++) {{ x[i].classList.remove("active"); }}
            tablinks = document.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {{ tablinks[i].classList.remove("active"); }}
            document.getElementById(tabId).classList.add("active");
            event.currentTarget.classList.add("active");
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="tabs">{tab_buttons}</div>
        {tab_contents}
    </div>
</body>
</html>
"""

async def get_week_data(school_name, target_teacher, week_num):
    try:
        tt = TimeTable(school_name, week_num=week_num)
        my_schedule = [["" for _ in range(9)] for _ in range(6)]
        has_data = False

        for grade in range(1, 4):
            for class_num in range(1, 16):
                try:
                    class_data = tt.timetable[grade][class_num]
                except: continue

                for day_idx in range(1, 6):
                    for lesson in class_data[day_idx]:
                        if target_teacher in lesson.teacher:
                            my_schedule[day_idx][lesson.period] = {
                                "subject": lesson.subject,
                                "class": f"{grade}-{class_num}"
                            }
                            has_data = True

        if not has_data: return None

        rows = ""
        for period in range(1, 8):
            # [변경점] 교시 숫자 밑에 시작 시간 추가
            time_str = START_TIMES.get(period, "")
            rows += f"<tr><td class='period'>{period}<span class='time-info'>{time_str}</span></td>"
            
            for day in range(1, 6):
                data = my_schedule[day][period]
                if data:
                    bg_color = get_class_color(data['class'])
                    rows += f"<td style='background-color: {bg_color};'><span class='subject'>{data['subject']}</span><span class='class-info'>{data['class']}</span></td>"
                else:
                    rows += "<td></td>"
            rows += "</tr>"
        return rows

    except Exception:
        return None

async def create_final_widget():
    school = "송양고등학교"
    teacher = "정찬" 
    
    print(f"[INFO] 노션 위젯용(시간표시) 데이터 수집 중...")

    tab_buttons_html = ""
    tab_contents_html = ""
    
    max_weeks = 2 
    
    for w in range(max_weeks):
        print(f"[RUNNING] {w}주차 확인...", end="\r")
        table_rows = await get_week_data(school, teacher, w)
        
        if table_rows is None:
            table_rows = "<tr><td colspan='6' style='padding:20px; font-size:12px; color:#999;'>정보 없음</td></tr>"
            
        tab_label = "이번 주" if w == 0 else "다음 주"
        is_active = "active" if w == 0 else ""
        
        tab_buttons_html += f"""<div class="tab {is_active}" onclick="openTab(event, 'week{w}')">{tab_label}</div>"""
        
        tab_contents_html += f"""
        <div id="week{w}" class="content {is_active}">
            <table>
                <thead>
                    <tr><th width="10%">교시</th><th width="18%">월</th><th width="18%">화</th><th width="18%">수</th><th width="18%">목</th><th width="18%">금</th></tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
        """

    final_html = HTML_TEMPLATE.format(
        tab_buttons=tab_buttons_html,
        tab_contents=tab_contents_html
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("\n[SUCCESS] 시간 정보가 포함된 index.html 파일 생성 완료!")

if __name__ == "__main__":
    asyncio.run(create_final_widget())
