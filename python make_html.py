import asyncio
from pycomcigan import TimeTable
import datetime

# ==========================================
# 🎨 반별 색상 설정 (여기서 색을 바꿀 수 있어요!)
# ==========================================
# 특정 반에 원하는 색을 직접 지정하고 싶다면 여기에 적으세요.
# 색상 코드표: https://htmlcolorcodes.com/
SPECIFIC_COLORS = {
    "3-5": "#FFEBEE", # 예: 3학년 5반은 연한 빨강
    "1-2": "#E3F2FD", # 예: 1학년 2반은 연한 파랑
}

# 지정하지 않은 반들은 아래 색상들 중에서 자동으로 골라집니다. (파스텔톤)
AUTO_COLORS = [
    "#F3E5F5", "#E8F5E9", "#FFFDE7", "#FBE9E7", "#E0F7FA", 
    "#FFF3E0", "#F1F8E9", "#ECEFF1", "#F9FBE7", "#EFEBE9"
]

def get_class_color(class_name):
    """반 이름(예: '3-5')에 맞는 배경색을 가져옵니다."""
    # 1. 직접 지정한 색이 있으면 그걸 사용
    if class_name in SPECIFIC_COLORS:
        return SPECIFIC_COLORS[class_name]
    
    # 2. 없으면 반 이름을 숫자로 바꿔서 자동 색상 배정 (항상 같은 반은 같은 색)
    # 예: '3-5'라는 글자를 숫자로 변환해서 리스트 인덱스로 사용
    hash_val = sum(ord(c) for c in class_name) 
    return AUTO_COLORS[hash_val % len(AUTO_COLORS)]

# ==========================================
# 노션 위젯용 템플릿
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
            padding: 4px 2px; text-align: center; vertical-align: middle; height: 38px;
        }}

        .period {{ background-color: #f8f9fa; color: #868e96; font-size: 11px; font-weight: bold; width: 30px; }}
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
            rows += f"<tr><td class='period'>{period}</td>"
            for day in range(1, 6):
                data = my_schedule[day][period]
                if data:
                    # [변경점] 반 이름으로 색상 가져오기
                    bg_color = get_class_color(data['class'])
                    rows += f"<td style='background-color: {bg_color};'><span class='subject'>{data['subject']}</span><span class='class-info'>{data['class']}</span></td>"
                else:
                    rows += "<td></td>"
            rows += "</tr>"
        return rows

    except Exception:
        return None

async def create_colorful_widget():
    school = "송양고등학교"
    teacher = "정찬" 
    
    print(f"🚀 노션 위젯용(컬러) 데이터 수집 중...")

    tab_buttons_html = ""
    tab_contents_html = ""
    
    max_weeks = 2 
    
    for w in range(max_weeks):
        print(f"📡 {w}주차 확인...", end="\r")
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
                    <tr><th width="8%">교시</th><th width="18%">월</th><th width="18%">화</th><th width="18%">수</th><th width="18%">목</th><th width="18%">금</th></tr>
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
    
    print("\n✅ 컬러풀한 index.html 파일 생성 완료!")

if __name__ == "__main__":
    asyncio.run(create_colorful_widget())
