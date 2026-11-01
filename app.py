import streamlit as st
import json
import re
from google import genai

# ตั้งค่าหน้าจอ Web UI
st.set_page_config(page_title="AI Consumer Review Assistant", page_icon="🛍️")
st.title("🛍️ AI สรุปรีวิวสินค้า & ตรวจจับรีวิวปลอม")
st.write("วางข้อความรีวิวสินค้าเพื่อใช้ AI วิเคราะห์ข้อดี ข้อเสีย และคะแนนความน่าเชื่อถือ")

# รับ Gemini API Key จากผู้ใช้ หรือจาก Secrets
api_key = st.sidebar.text_input("ใส่ Gemini API Key", type="password")

# ช่องรับข้อมูลข้อความรีวิวจากผู้ซื้อ
review_input = st.text_area("วางข้อความรีวิวสินค้าที่นี่ (วางรวมกันหลายๆ รีวิวได้):", height=200)

if st.button("🔍 วิเคราะห์รีวิว"):
    if not api_key:
        st.error("กรุณากรอก Gemini API Key ในแถบด้านข้างก่อนครับ")
    elif not review_input.strip():
        st.warning("กรุณาใส่ข้อความรีวิวก่อนกดวิเคราะห์")
    else:
        with st.spinner("AI กำลังวิเคราะห์และคำนวณ Trust Score..."):
            try:
                # เรียกใช้ Google GenAI SDK
                client = genai.Client(api_key=api_key)
                
                # ออกแบบ Prompt สั่ง AI
                prompt = f"""
                คุณคือผู้เชี่ยวชาญด้านการคุ้มครองผู้บริโภค จงวิเคราะห์ข้อความรีวิวสินค้าต่อไปนี้:
                <reviews>
                {review_input}
                </reviews>

                งานของคุณ:
                1. คำนวณ Trust Score (0-100%) โดยตรวจหาแนวโน้มรีวิวปลอม/รีวิวรับจ้าง (เช่น คำซ้ำๆ ชมแบบไม่มีเนื้อหา)
                2. สรุปข้อดี (Pros) 3 ข้อ และ ข้อเสีย (Cons) 3 ข้อ
                3. ให้คะแนนมิติต่างๆ 1-10 (คุณภาพ, ความคุ้มค่า, บริการ)

                ตอบกลับเป็นรูปแบบ JSON โครงสร้างนี้เท่านั้น:
                {{
                  "trust_score": 85,
                  "fake_warning": "เหตุผล/สัญญาณรีวิวปลอมที่พบ (ถ้าไม่มีให้ใส่ 'ไม่พบสัญญาณรีวิวปลอม')",
                  "pros": ["ข้อดี 1", "ข้อดี 2", "ข้อดี 3"],
                  "cons": ["ข้อเสีย 1", "ข้อเสีย 2", "ข้อเสีย 3"],
                  "aspects": {{"quality": 8, "value": 7, "service": 9}}
                }}
                """

                # ส่งคำสั่งไปประมวลผลที่โมเดล Gemini
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )

                # ดึงข้อมูล JSON ออกมาจากข้อความที่ AI ตอบกลับ
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))

                    # แสดงผลคะแนน Trust Score
                    score = data.get("trust_score", 0)
                    st.subheader("🛡️ คะแนนความน่าเชื่อถือ (Trust Score)")
                    if score >= 75:
                        st.success(f"ความน่าเชื่อถือสูง: {score}%")
                    elif score >= 50:
                        st.warning(f"ความน่าเชื่อถือปานกลาง: {score}%")
                    else:
                        st.error(f"ระวัง! ความน่าเชื่อถือต่ำ: {score}%")
                    
                    st.caption(f"📌 **ข้อสังเกต:** {data.get('fake_warning')}")
                    st.divider()

                    # แสดงข้อดี - ข้อเสีย
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### 🟢 ข้อดี (Pros)")
                        for pro in data.get("pros", []):
                            st.write(f"- {pro}")
                    with col2:
                        st.write("### 🔴 ข้อเสีย (Cons)")
                        for con in data.get("cons", []):
                            st.write(f"- {con}")

                    st.divider()
                    # แสดงคะแนนแยกตามมิติ
                    st.write("### 📊 คะแนนแยกตามมิติ")
                    aspects = data.get("aspects", {})
                    st.json(aspects)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")