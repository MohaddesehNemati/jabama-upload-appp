
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

LOGO_PATH = "jabama_logo.png"
DATA_FILE = 'requests.csv'
UPLOAD_FOLDER = 'uploads'
EMAIL_RECEIVER = "mohaddeseh.nemati.aghdam@gmail.com"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=['host_code', 'name', 'place_name', 'doc_type', 'filename', 'timestamp']).to_csv(DATA_FILE, index=False)

col1, col2 = st.columns([4, 1])
with col2:
    st.image(LOGO_PATH, use_column_width=True)

st.title("فرم ارسال تعهدنامه میزبان‌ها")

with st.form("upload_form"):
    host_code = st.text_input("کد میزبانی")
    name = st.text_input("نام و نام خانوادگی")
    place_name = st.text_input("نام اقامتگاه")
    doc_type = st.selectbox("نوع تعهدنامه", ["تعهدنامه مالی", "تعهدنامه حقوقی", "تعهدنامه ویژه"])
    uploaded_file = st.file_uploader("آپلود تصویر تعهدنامه", type=["jpg", "jpeg", "png", "pdf"])
    submitted = st.form_submit_button("ارسال")

if submitted:
    if not (host_code and name and place_name and doc_type and uploaded_file):
        st.warning("لطفاً تمام فیلدها را کامل پر کنید.")
    else:
        df = pd.read_csv(DATA_FILE)
        now = datetime.now()
        three_days_ago = now - timedelta(days=3)

        recent = df[
            (df['host_code'] == host_code) &
            (df['doc_type'] == doc_type) &
            (pd.to_datetime(df['timestamp']) > three_days_ago)
        ]

        if not recent.empty:
            st.error("در ۳ روز اخیر، برای این نوع تعهدنامه ثبت انجام شده است.")
        else:
            filename = f"{host_code}_{doc_type}_{now.strftime('%Y%m%d%H%M%S')}.{uploaded_file.name.split('.')[-1]}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            new_entry = pd.DataFrame([{
                "host_code": host_code,
                "name": name,
                "place_name": place_name,
                "doc_type": doc_type,
                "filename": filename,
                "timestamp": now
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)

            try:
                msg = EmailMessage()
                msg["Subject"] = f"تعهدنامه جدید میزبان: {name}"
                msg["From"] = "youremail@gmail.com"
                msg["To"] = EMAIL_RECEIVER
                msg.set_content(f"میزبان {name} برای اقامتگاه {place_name} تعهدنامه ارسال کرده است.")

                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=filename)

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login("Mohaddeseh.nemati.aghdam@gmail.com", "yeza hhth ujxo kcos")
                    smtp.send_message(msg)

                st.success("فایل با موفقیت آپلود و ایمیل شد.")
            except Exception as e:
                st.warning("فایل ذخیره شد اما ایمیل ارسال نشد.")
                st.error(str(e))
