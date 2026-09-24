import streamlit as st
import sqlite3
from datetime import datetime, date
from zoneinfo import ZoneInfo
import base64
import time
import random

# ---------------------------------------------------------
# Page Setup & Modern Dark UI Design
# ---------------------------------------------------------
st.set_page_config(page_title="TRANSFORM GYM & CALISTHENICS PRO", page_icon="🏋️‍♂️", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: #0B0F19;
        color: #F3F4F6;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide sidebar completely */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    .app-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1E1B4B, #312E81);
        border-radius: 16px;
        border: 1px solid #4338CA;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    .profile-card {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 25px;
    }
    
    .quote-card {
        background: linear-gradient(135deg, #311B92, #1A237E);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #5C6BC0;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
    
    .profile-avatar {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #6366F1;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
        margin-bottom: 15px;
    }
    
    .badge {
        background: rgba(99, 102, 241, 0.2);
        color: #818CF8;
        padding: 8px 16px;
        border-radius: 20px;
        border: 1px solid rgba(129, 140, 248, 0.3);
        font-size: 0.95rem;
        font-weight: 600;
        display: inline-block;
        margin: 6px;
    }
    
    .checkin-hero-card {
        background: linear-gradient(135deg, #1E1B4B, #4338CA);
        padding: 35px;
        border-radius: 24px;
        text-align: center;
        border: 2px solid #6366F1;
        box-shadow: 0 15px 35px rgba(99, 102, 241, 0.3);
        margin: 30px 0;
    }

    .workout-card {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .stopwatch-display {
        font-size: 3.5rem;
        font-weight: 800;
        color: #818CF8;
        font-family: monospace;
        text-align: center;
        background: #111827;
        padding: 20px;
        border-radius: 20px;
        border: 2px solid #4338CA;
        margin: 20px 0;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #4F46E5, #6366F1) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(79, 70, 229, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Single Fixed Database Connection
# ---------------------------------------------------------
conn = sqlite3.connect("gym_app.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    dob TEXT,
    age INTEGER,
    city TEXT,
    country TEXT,
    gender TEXT,
    height_ft INTEGER,
    height_in INTEGER,
    level TEXT,
    profile_pic TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    checkin_date TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS custom_workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    day TEXT,
    exercise_name TEXT,
    sets INTEGER,
    reps INTEGER,
    equipment TEXT
)
""")
conn.commit()

# Session State Setup
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "sw_running" not in st.session_state:
    st.session_state.sw_running = False
if "sw_start_time" not in st.session_state:
    st.session_state.sw_start_time = 0
if "sw_elapsed" not in st.session_state:
    st.session_state.sw_elapsed = 0
if "sw_laps" not in st.session_state:
    st.session_state.sw_laps = []

def process_img(file):
    if file is not None:
        return base64.b64encode(file.read()).decode()
    return ""

TIMEZONE_MAP = {
    "Pakistan": "Asia/Karachi",
    "India": "Asia/Kolkata",
    "United Arab Emirates": "Asia/Dubai",
    "Saudi Arabia": "Asia/Riyadh",
    "United Kingdom": "Europe/London",
    "United States": "America/New_York",
    "Canada": "America/Toronto"
}

MOTIVATIONAL_QUOTES = [
    "🔥 'The body achieves what the mind believes.'",
    "💪 'No pain, no gain. Shut up and train!'",
    "⚡ 'Your body can stand almost anything. It's your mind that you have to convince.'",
    "🤸 'Mastering your body weight is the ultimate form of strength.'",
    "🏋️ 'Success starts with self-discipline.'",
    "🚀 'Don't count the days, make the days count.'",
    "💯 'Consistency is the difference between failure and success.'"
]

# ---------------------------------------------------------
# 1. LOGIN & ONBOARDING SYSTEM
# ---------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("""
    <div class="app-header">
        <h1 style="margin:0; font-size:2.2rem; color:#FFFFFF;">🏋️‍♂️ Gym & Calisthenics Pro Suite</h1>
        <p style="margin:5px 0 0 0; color:#A5B4FC;">Apna Account Login Ya Setup Karein</p>
    </div>
    """, unsafe_allow_html=True)
    
    uname_input = st.text_input("👤 Username Enter Karein:").strip().lower()
    
    if st.button("🔑 Login / Account Access", use_container_width=True):
        if uname_input:
            st.session_state.username = uname_input
            cursor.execute("SELECT * FROM users WHERE username = ?", (uname_input,))
            user_record = cursor.fetchone()
            
            if user_record:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.session_state.need_onboarding = True
        else:
            st.warning("Pehle koi Username enter karein!")

    if st.session_state.get("need_onboarding", False):
        st.divider()
        st.subheader(f"📝 Profile Details Add Karein: ({st.session_state.username})")
        
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            f_name = st.text_input("Full Name (Pura Naam):")
        with col_n2:
            u_email = st.text_input("📧 Gmail / Email Address (Optional):")
        
        col1, col2 = st.columns(2)
        with col1:
            u_dob = st.date_input("🎂 Date of Birth", min_value=date(1950, 1, 1), max_value=date.today(), value=date(2000, 1, 1))
            today = date.today()
            calc_age = today.year - u_dob.year - ((today.month, today.day) < (u_dob.month, u_dob.day))
            st.caption(f"Calculated Age: **{calc_age} Years**")
            
            u_city = st.text_input("🏙️ City Name:")
            u_country = st.selectbox("🌍 Country Select Karein:", list(TIMEZONE_MAP.keys()))
            u_gender = st.selectbox("👤 Gender", ["Male", "Female", "Other"])
            
        with col2:
            st.write("📏 **Height (Feet & Inches):**")
            h_col1, h_col2 = st.columns(2)
            with h_col1:
                u_height_ft = st.number_input("Feet (ft):", min_value=3, max_value=8, value=5)
            with h_col2:
                u_height_in = st.number_input("Inches (in):", min_value=0, max_value=11, value=7)
                
            u_level = st.selectbox("⚡ Fitness Level", ["Absolute Beginner", "Intermediate Level", "Advance Pro"])
            uploaded_file = st.file_uploader("🖼️ Profile Picture Upload Karein", type=["png", "jpg", "jpeg"])
            encoded_pic = process_img(uploaded_file)

        if st.button("💾 Save Profile & Continue", use_container_width=True):
            if f_name and u_city:
                today_str = str(date.today())
                cursor.execute("""
                INSERT OR REPLACE INTO users 
                (username, name, email, dob, age, city, country, gender, height_ft, height_in, level, profile_pic, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (st.session_state.username, f_name, u_email, str(u_dob), calc_age, u_city, u_country, u_gender, u_height_ft, u_height_in, u_level, encoded_pic, today_str))
                conn.commit()
                st.session_state.authenticated = True
                st.session_state.need_onboarding = False
                st.rerun()
            else:
                st.error("Kripya Naam aur City Name laazmi fill karein!")

    st.stop()

# Fetch User Info
cursor.execute("SELECT name, email, dob, age, city, country, gender, height_ft, height_in, level, profile_pic, created_at FROM users WHERE username = ?", (st.session_state.username,))
user = cursor.fetchone()
name, email, dob, age, city, country, gender, height_ft, height_in, level, pic_data, created_at = user

# Calculate Checkin Details
today_date_str = str(date.today())
cursor.execute("SELECT checkin_date FROM checkins WHERE username = ? ORDER BY checkin_date ASC", (st.session_state.username,))
user_checkins = [r[0] for r in cursor.fetchall()]

total_days_completed = len(user_checkins)
is_checked_in_today = today_date_str in user_checkins

# ---------------------------------------------------------
# 2. MANDATORY CHECK-IN GATEWAY
# ---------------------------------------------------------
if not is_checked_in_today:
    st.markdown(f"""
    <div class="checkin-hero-card">
        <h1 style="color:#FFFFFF; font-size: 2.2rem; margin:0;">🔥 365-DAY CHALLENGE GATEWAY</h1>
        <p style="color:#C7D2FE; font-size:1.1rem; margin-top:8px;">Welcome, <b>{name}</b>! App access karne ke liye pehle aaj ka check-in complete karein.</p>
        <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:15px; margin:20px 0; display:inline-block;">
            <h3 style="margin:0; color:#818CF8;">Target Status: <span style="color:#FBBF24;">Day {total_days_completed + 1} / 365</span></h3>
            <p style="margin:5px 0 0 0; opacity:0.8; font-size:0.9rem;">Total Days Completed: <b>{total_days_completed} Days</b></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        if st.button(f"⚡ COMPLETE DAY {total_days_completed + 1} CHECK-IN NOW", use_container_width=True):
            cursor.execute("INSERT OR IGNORE INTO checkins (username, checkin_date) VALUES (?, ?)", (st.session_state.username, today_date_str))
            conn.commit()
            st.success(f"🎉 Great job {name}! Day {total_days_completed + 1} Check-In Complete!")
            time.sleep(1)
            st.rerun()

    st.warning("⚠️ Access Locked: Pehle check-in karein, iske baad poori app aur navigation features unlock honge.")
    
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    st.stop()

# ---------------------------------------------------------
# 3. TOP RIGHT NAVIGATION MENU & HEADER
# ---------------------------------------------------------
head_col1, head_col2 = st.columns([3, 2])

with head_col1:
    st.markdown(f"<h2 style='margin:0; color:#FFFFFF;'>🏋️‍♂️ TRANSFORM GYM PRO</h2>", unsafe_allow_html=True)

with head_col2:
    menu = st.selectbox(
        "⚙️ Navigation Menu:",
        [
            "🏠 Home Page (Profile & Progress)", 
            "📅 Daily Workouts (Gym & Calisthenics)", 
            "🛠️ Make Custom Routine", 
            "⏱️ Stopwatch & Rest Timer"
        ],
        label_visibility="visible"
    )

st.divider()

# ---------------------------------------------------------
# PAGE 1: HOME PAGE (PROFILE, MOTIVATIONAL QUOTES & EDIT)
# ---------------------------------------------------------
if menu == "🏠 Home Page (Profile & Progress)":
    c_top1, c_top2 = st.columns([4, 1])
    with c_top1:
        st.markdown(f"### 👋 Welcome, <span style='color:#818CF8;'>{name}</span>!", unsafe_allow_html=True)
    with c_top2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()

    # MOTIVATIONAL QUOTE CARD (NEW FEATURE)
    daily_quote = random.choice(MOTIVATIONAL_QUOTES)
    st.markdown(f"""
    <div class="quote-card">
        <h3 style="margin:0; color:#E0E7FF; font-style: italic;">{daily_quote}</h3>
    </div>
    """, unsafe_allow_html=True)

    if pic_data:
        img_src = f"data:image/png;base64,{pic_data}"
    else:
        img_src = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

    email_display = f" | 📧 {email}" if email else ""

    st.markdown(f"""
    <div class="profile-card">
        <img src="{img_src}" class="profile-avatar"><br>
        <h2 style="margin: 5px 0; font-size: 2rem; font-weight:700; color:#FFFFFF;">{name}</h2>
        <p style="margin:0; opacity: 0.8; font-size:1rem; color:#9CA3AF;">📍 {city}, {country}{email_display}</p>
        <div style="margin-top: 18px;">
            <span class="badge">🔥 Challenge Status: Day {total_days_completed} / 365</span>
            <span class="badge">🎂 DOB: {dob} ({age} yrs)</span>
            <span class="badge">📏 Height: {height_ft} ft {height_in} in</span>
            <span class="badge">👤 Gender: {gender}</span>
            <span class="badge">⚡ Fitness Level: {level}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 365-Day Consistency Tracker")
    progress_val = min(total_days_completed / 365.0, 1.0)
    st.progress(progress_val)
    st.info(f"🎉 Aap ne 365 mein se **{total_days_completed} Days** ka Challenge poora kar liya hai! ({int(progress_val*100)}% Completed)")

    st.divider()

    # EDIT PROFILE SECTION
    with st.expander("✏️ Edit Profile Details (Country, City, Height, Level, etc.)"):
        with st.form("edit_profile_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_name = st.text_input("Full Name:", value=name)
                edit_email = st.text_input("Email Address:", value=email if email else "")
                
                try:
                    curr_country_idx = list(TIMEZONE_MAP.keys()).index(country)
                except:
                    curr_country_idx = 0
                edit_country = st.selectbox("🌍 Select Country:", list(TIMEZONE_MAP.keys()), index=curr_country_idx)
                edit_city = st.text_input("🏙️ City Name:", value=city)

            with col_e2:
                h_col1, h_col2 = st.columns(2)
                with h_col1:
                    edit_h_ft = st.number_input("Height (Feet):", min_value=3, max_value=8, value=height_ft)
                with h_col2:
                    edit_h_in = st.number_input("Height (Inches):", min_value=0, max_value=11, value=height_in)
                    
                levels = ["Absolute Beginner", "Intermediate Level", "Advance Pro"]
                try:
                    curr_lvl_idx = levels.index(level)
                except:
                    curr_lvl_idx = 0
                edit_level = st.selectbox("⚡ Fitness Level:", levels, index=curr_lvl_idx)
                
                new_pic_file = st.file_uploader("🖼️ Change Profile Picture (Optional)", type=["png", "jpg", "jpeg"])

            save_btn = st.form_submit_button("💾 Save Profile Changes")
            if save_btn:
                updated_pic = pic_data
                if new_pic_file is not None:
                    updated_pic = process_img(new_pic_file)

                cursor.execute("""
                UPDATE users SET 
                    name = ?, email = ?, city = ?, country = ?, 
                    height_ft = ?, height_in = ?, level = ?, profile_pic = ?
                WHERE username = ?
                """, (edit_name, edit_email, edit_city, edit_country, edit_h_ft, edit_h_in, edit_level, updated_pic, st.session_state.username))
                conn.commit()
                st.success("🎉 Profile Details Successfully Updated!")
                time.sleep(1)
                st.rerun()

# ---------------------------------------------------------
# PAGE 2: DAILY WORKOUTS (CALISTHENICS & GYM EQUIPMENT)
# ---------------------------------------------------------
elif menu == "📅 Daily Workouts (Gym & Calisthenics)":
    st.title("📅 Daily Workouts")

    day_selected = st.selectbox("Select Workout Day:", [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ])

    equipment_schedules = {
        "Monday": [
            {"name": "Barbell Bench Press", "sets": "4 Sets", "reps": "8-12 Reps", "eq": "Barbell & Flat Bench"},
            {"name": "Incline Dumbbell Press", "sets": "3 Sets", "reps": "10-12 Reps", "eq": "Dumbbells & Incline Bench"},
            {"name": "Cable Chest Flyes", "sets": "3 Sets", "reps": "15 Reps", "eq": "Cable Machine"},
            {"name": "Tricep Cable Pushdowns", "sets": "4 Sets", "reps": "12-15 Reps", "eq": "Cable Pulley"}
        ],
        "Tuesday": [
            {"name": "Barbell Deadlifts", "sets": "4 Sets", "reps": "6-8 Reps", "eq": "Barbell & Plates"},
            {"name": "Lat Pulldown Machine", "sets": "3 Sets", "reps": "10-12 Reps", "eq": "Cable Pulldown Machine"},
            {"name": "Seated Cable Rows", "sets": "3 Sets", "reps": "12 Reps", "eq": "Seated Row Machine"},
            {"name": "EZ-Bar Bicep Curls", "sets": "4 Sets", "reps": "12 Reps", "eq": "EZ Bar"}
        ],
        "Wednesday": [
            {"name": "Barbell Back Squats", "sets": "4 Sets", "reps": "8-10 Reps", "eq": "Squat Rack & Barbell"},
            {"name": "Leg Press Machine", "sets": "3 Sets", "reps": "12 Reps", "eq": "Leg Press Machine"},
            {"name": "Leg Extension & Curls", "sets": "3 Sets", "reps": "15 Reps", "eq": "Leg Extension Machine"}
        ],
        "Thursday": [
            {"name": "Overhead Military Press", "sets": "4 Sets", "reps": "8-10 Reps", "eq": "Barbell"},
            {"name": "Dumbbell Lateral Raises", "sets": "4 Sets", "reps": "15 Reps", "eq": "Dumbbells"},
            {"name": "Cable Face Pulls", "sets": "3 Sets", "reps": "15 Reps", "eq": "Cable Rope"}
        ],
        "Friday": [
            {"name": "Dumbbell Thrusters", "sets": "4 Sets", "reps": "12 Reps", "eq": "Dumbbells"},
            {"name": "Kettlebell Swings", "sets": "4 Sets", "reps": "20 Reps", "eq": "Kettlebell"}
        ],
        "Saturday": [
            {"name": "Machine Chest Press", "sets": "3 Sets", "reps": "12 Reps", "eq": "Chest Press Machine"},
            {"name": "Hamstring Curls Machine", "sets": "3 Sets", "reps": "15 Reps", "eq": "Machine"}
        ],
        "Sunday": [
            {"name": "Light Stretch & Mobility", "sets": "1 Session", "reps": "15 Mins", "eq": "Light Dumbbells"}
        ]
    }

    calisthenics_schedules = {
        "Monday": [
            {"name": "Parallel Bar Dips", "sets": "4 Sets", "reps": "12-15 Reps", "eq": "Dip Bars / Bodyweight"},
            {"name": "Incline / Decline Push-ups", "sets": "3 Sets", "reps": "15 Reps", "eq": "Bodyweight"}
        ],
        "Tuesday": [
            {"name": "Wide Grip Pull-Ups", "sets": "4 Sets", "reps": "8-12 Reps", "eq": "Pull-Up Bar"},
            {"name": "Chin-Ups", "sets": "3 Sets", "reps": "10 Reps", "eq": "Pull-Up Bar"}
        ],
        "Wednesday": [
            {"name": "Hanging Leg Raises", "sets": "4 Sets", "reps": "15 Reps", "eq": "Pull-Up Bar"},
            {"name": "Plank Hold", "sets": "3 Sets", "reps": "60 Seconds", "eq": "Bodyweight"}
        ],
        "Thursday": [
            {"name": "Pike Push-ups (Shoulders)", "sets": "4 Sets", "reps": "12 Reps", "eq": "Bodyweight"},
            {"name": "Handstand Hold against Wall", "sets": "3 Sets", "reps": "30 Seconds", "eq": "Wall / Bodyweight"}
        ],
        "Friday": [
            {"name": "Standard & Diamond Push-ups", "sets": "4 Sets", "reps": "20 Reps", "eq": "Bodyweight"},
            {"name": "Bar Dips", "sets": "4 Sets", "reps": "15 Reps", "eq": "Parallel Bars"},
            {"name": "Pull-ups", "sets": "4 Sets", "reps": "10 Reps", "eq": "Pull-up Bar"},
            {"name": "L-Sit Hold", "sets": "4 Sets", "reps": "20 Seconds", "eq": "Parallel Bars / Floor"}
        ],
        "Saturday": [
            {"name": "Muscle-Up Practice / Assisted Pull-ups", "sets": "4 Sets", "reps": "5 Reps", "eq": "Pull-Up Bar"},
            {"name": "Bodyweight Jump Squats", "sets": "4 Sets", "reps": "20 Reps", "eq": "Bodyweight"}
        ],
        "Sunday": [
            {"name": "Full Body Mobility & Calisthenics Active Recovery", "sets": "1 Session", "reps": "20 Mins", "eq": "Bodyweight Mat"}
        ]
    }

    tab_cal, tab_eq = st.tabs(["🤸 Calisthenics Workouts", "🏋️ Gym Equipment Workouts"])

    with tab_cal:
        st.subheader(f"🤸 Calisthenics & Bodyweight Routines ({day_selected})")
        items = calisthenics_schedules.get(day_selected, [])
        for item in items:
            st.markdown(f"""
            <div class="workout-card">
                <h3 style="margin:0; color:#34D399;">{item['name']}</h3>
                <p style="margin:5px 0;"><b>Sets:</b> {item['sets']} | <b>Reps:</b> {item['reps']}</p>
                <span class="badge" style="background:rgba(52,211,153,0.2); color:#34D399; border-color:rgba(52,211,153,0.3);">🤸 Style: {item['eq']}</span>
            </div>
            """, unsafe_allow_html=True)

    with tab_eq:
        st.subheader(f"🏋️ Gym Equipment Routines ({day_selected})")
        items = equipment_schedules.get(day_selected, [])
        for item in items:
            st.markdown(f"""
            <div class="workout-card">
                <h3 style="margin:0; color:#818CF8;">{item['name']}</h3>
                <p style="margin:5px 0;"><b>Sets:</b> {item['sets']} | <b>Reps:</b> {item['reps']}</p>
                <span class="badge">⚙️ Equipment: {item['eq']}</span>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE 3: MAKE CUSTOM ROUTINE
# ---------------------------------------------------------
elif menu == "🛠️ Make Custom Routine":
    st.title("🛠️ Make Your Own Custom Routine")
    st.write("Apni pasand ki equipment ya calisthenics exercises add karein!")
    
    with st.form("custom_ex_form"):
        col1, col2 = st.columns(2)
        with col1:
            c_day = st.selectbox("Select Day:", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            ex_name = st.text_input("Exercise Name (e.g., Incline Press / Muscle Up):")
        with col2:
            eq_name = st.selectbox("Category / Equipment:", ["Bodyweight / Calisthenics", "Barbell", "Dumbbell", "Cable Machine", "Kettlebell", "Machine"])
            c_sets = st.number_input("Sets:", min_value=1, max_value=10, value=3)
            c_reps = st.number_input("Reps:", min_value=1, max_value=100, value=12)
            
        submit_custom = st.form_submit_button("➕ Add Exercise")
        
    if submit_custom:
        if ex_name:
            cursor.execute("""
            INSERT INTO custom_workouts (username, day, exercise_name, sets, reps, equipment)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (st.session_state.username, c_day, ex_name, c_sets, c_reps, eq_name))
            conn.commit()
            st.success(f"Added {ex_name} to {c_day} Schedule!")
            st.rerun()
        else:
            st.error("Kripya Exercise ka naam enter karein!")

    st.divider()
    st.subheader("📋 Your Saved Custom Exercises")
    
    cursor.execute("SELECT id, day, exercise_name, sets, reps, equipment FROM custom_workouts WHERE username = ?", (st.session_state.username,))
    custom_records = cursor.fetchall()
    
    if custom_records:
        for ex_id, ex_day, ex_n, ex_s, ex_r, ex_eq in custom_records:
            c_col1, c_col2 = st.columns([5, 1])
            with c_col1:
                st.write(f"📌 **[{ex_day}] {ex_n}** — {ex_s} Sets x {ex_r} Reps ({ex_eq})")
            with c_col2:
                if st.button("🗑️ Delete", key=f"del_{ex_id}"):
                    cursor.execute("DELETE FROM custom_workouts WHERE id = ?", (ex_id,))
                    conn.commit()
                    st.rerun()
    else:
        st.info("Abhi tak koi custom exercise save nahi ki gayi.")

# ---------------------------------------------------------
# PAGE 4: STOPWATCH & REST TIMER
# ---------------------------------------------------------
elif menu == "⏱️ Stopwatch & Rest Timer":
    st.title("⏱️ Stopwatch & Rest Timer Tool")
    
    tab_sw, tab_rt = st.tabs(["⏱️ Live Stopwatch", "⏳ Rest Timer"])
    
    with tab_sw:
        st.subheader("⏱️ Live Stopwatch")
        
        current_elapsed = st.session_state.sw_elapsed
        if st.session_state.sw_running:
            current_elapsed += time.time() - st.session_state.sw_start_time
            
        mins, secs = divmod(int(current_elapsed), 60)
        millis = int((current_elapsed - int(current_elapsed)) * 100)
        
        st.markdown(f'<div class="stopwatch-display">{mins:02d}:{secs:02d}:{millis:02d}</div>', unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        
        with btn_col1:
            if not st.session_state.sw_running:
                if st.button("▶️ Start", use_container_width=True):
                    st.session_state.sw_running = True
                    st.session_state.sw_start_time = time.time()
                    st.rerun()
            else:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.sw_running = False
                    st.session_state.sw_elapsed += time.time() - st.session_state.sw_start_time
                    st.rerun()

        with btn_col2:
            if st.button("🚩 Record Lap", use_container_width=True):
                if current_elapsed > 0:
                    st.session_state.sw_laps.append(f"{mins:02d}:{secs:02d}:{millis:02d}")
                    st.rerun()

        with btn_col3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.sw_running = False
                st.session_state.sw_start_time = 0
                st.session_state.sw_elapsed = 0
                st.session_state.sw_laps = []
                st.rerun()

        if st.session_state.sw_running:
            time.sleep(0.1)
            st.rerun()
            
        if st.session_state.sw_laps:
            st.write("---")
            st.subheader("📋 Lap Times Recorded:")
            for idx, lap in enumerate(reversed(st.session_state.sw_laps), 1):
                st.write(f"**Lap {len(st.session_state.sw_laps) - idx + 1}:** `{lap}`")

    with tab_rt:
        st.subheader("⏳ Rest Timer")
        rest_sec = st.number_input("Rest Duration (Seconds):", min_value=5, max_value=300, value=60)
        
        if st.button("▶️ Start Rest Countdown"):
            timer_holder = st.empty()
            for s in range(rest_sec, 0, -1):
                timer_holder.metric("Time Left", f"{s} Seconds")
                time.sleep(1)
            timer_holder.success("⏰ TIME IS UP! Start Your Next Set! 🔥")