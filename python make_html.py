import asyncio
from pycomcigan import TimeTable
import datetime

# ==========================================
# HTML 템플릿 (심플 버전)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>내 시간표</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .container {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 800px; width: 100%; }}
        
        /* 제목 스타일 (심플하게) */
        h1 {{ text-align: center; color: #333; margin-bottom: 20px; font-size: 1.5rem; }}
        
        /* 탭 디자인 */
        .tabs {{ display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; }}
        .tab {{ 
            padding: 10px 30px; text-align: center; border-radius: 20px; 
            color: #555; font-weight: bold; background: #eee; cursor: pointer; 
            transition: 0.3s;
        }}
        .tab.active {{ background: #4a90e2; color: white; box-shadow: 0 4px 6px rgba(74, 144, 226, 0.3); }}
        
        .content {{ display: none; }}
        .content.active {{ display: block; animation: fadeIn 0.3s; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }}
        th, td {{ border: 1px solid #e1e4e8; padding: 12px 8px; text-align: center; font-size: 0.95rem; }}
        th {{ background-color: #4a90e2; color: white; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        
        .period {{ background-color: #edf2f7; font-weight: bold; color: #4a5568; width: 40px; }}
        .subject {{ font-weight: bold; display: block; color: #2d3748; }}
        .class-info {{ font-size: 0.8em; color: #718096; display: block; margin-top: 2px; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
    <script>
        function openTab(event, tabId) {{
            var i, contents, tabs;
            contents = document.getElementsByClassName("content");
            for (i = 0; i < contents.length; i++) {{ contents[i].classList.remove("active"); }}
            
            tabs = document.getElementsByClassName("tab");
            for (i = 0; i < tabs.length; i++) {{ tabs[i].classList.remove("active"); }}
            
            document.getElementById(tabId).classList.add("active");
            event.currentTarget.classList.add("active");
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>📅 시간표</h1>

        <div class="tabs">
            {tab_buttons}
        </div>

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
                    rows += f"<td><span class='subject'>{data['subject']}</span><span class='class-info'>{data['class']}</span></td>"
                else:
                    rows += "<td></td>"
            rows += "</tr>"
        return rows

    except Exception:
        return None

async def create_simple_html():
    school = "송양고등학교"
    teacher = "정찬" 
    
    print(f"🚀 '{school}' 데이터 수집 중...")

    tab_buttons_html = ""
    tab_contents_html = ""
    
    # 딱 이번주(0), 다음주(1) 두 개만 가져오도록 설정
    max_weeks = 2 
    
    for w in range(max_weeks):
        print(f"📡 {w}주차 데이터 요청 중...", end="\r")
        table_rows = await get_week_data(school, teacher, w)
        
        if table_rows is None:
            # 데이터가 없으면 '정보 없음' 표시
            table_rows = "<tr><td colspan='6' style='padding: 30px;'>휴일이거나 시간표 정보가 없습니다.</td></tr>"
            
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
    
    print("\n✅ 완료! 깔끔한 시간표가 생성되었습니다.")

if __name__ == "__main__":
    asyncio.run(create_simple_html())
