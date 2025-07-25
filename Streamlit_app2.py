import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, time
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Subject, TeacherSubject, Classroom, TimeSlot, Schedule, EditRequest, ElectiveGroup, ElectiveMembership, db


# DB setup
engine = create_engine("mysql+mysqlconnector://root:Harshi0506*@localhost:3306/timetable_db")
Session = sessionmaker(bind=engine)
session = Session()

# -- Helpers --



def login(username, password):
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            st.session_state['user_id'] = user.id
            st.session_state['username'] = user.username
            st.session_state['role'] = user.role
            return True
    except SQLAlchemyError as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return False


def logout():
    for key in ['user_id', 'username', 'role']:
        if key in st.session_state:
            del st.session_state[key]

def get_current_user():
    if 'user_id' in st.session_state:
        return session.query(User).get(st.session_state['user_id'])
    return None

def generate_valid_timeslots():
    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("16:00", "%H:%M")
    slot_duration = timedelta(minutes=45)

    breaks = [
        (datetime.strptime("10:15", "%H:%M"), datetime.strptime("10:45", "%H:%M")),
        (datetime.strptime("13:00", "%H:%M"), datetime.strptime("13:45", "%H:%M")),
    ]

    valid_slots = []
    current = start
    while current + slot_duration <= end:
        slot_start = current
        slot_end = current + slot_duration
        if not any(b_start < slot_end and slot_start < b_end for b_start, b_end in breaks):
            valid_slots.append((slot_start.time(), slot_end.time()))
        current += slot_duration

    return valid_slots

# Helper to handle datetime.time vs string
def parse_time_if_needed(value):
    if isinstance(value, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        return None
    return value


def generate_schedule_pdf(schedules, filename="timetable.pdf"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    data = [["ID", "Teacher", "Subject", "Classroom", "Day", "Start Time", "End Time", "Lab?"]]

    for s in schedules:
        teacher = session.query(User).get(s.teacher_id)
        subject = session.query(Subject).get(s.subject_id)
        classroom = session.query(Classroom).get(s.classroom_id)
        timeslot = session.query(TimeSlot).get(s.timeslot_id)

        row = [
            str(s.id),
            teacher.username if teacher else "N/A",
            subject.name if subject else "N/A",
            classroom.name if classroom else "N/A",
            timeslot.day if timeslot else "N/A",
            parse_time_if_needed(timeslot.start_time).strftime("%H:%M") if timeslot else "N/A",
            parse_time_if_needed(timeslot.end_time).strftime("%H:%M") if timeslot else "N/A",
            "Yes" if s.is_lab else "No"
        ]
        data.append(row)

    table = Table(data, repeatRows=1, hAlign='LEFT')
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)

    elements = [table]
    doc.build(elements)
    buffer.seek(0)
    return buffer


# Initialize role if not set
if 'role' not in st.session_state:
    st.session_state['role'] = None

st.title("College Timetable App")

# No user logged in yet
if st.session_state['role'] is None:
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(username, password):
                st.success(f"Logged in as {st.session_state['username']}")
            else:
                st.error("Invalid username or password")

    elif choice == "Register":
        st.subheader("Create New Account")
        username = st.text_input("Username", key="reg_user")
        password = st.text_input("Password", type="password", key="reg_pass")
        role = st.selectbox("Role", ["admin", "teacher", "student"], key="register_role")
        if st.button("Register"):
            if session.query(User).filter_by(username=username).first():
                st.warning("Username already exists")
            elif not username or not password:
                st.warning("Please fill all fields")
            else:
                hashed = generate_password_hash(password)
                new_user = User(username=username, password_hash=hashed, role=role)
                try:
                    session.add(new_user)
                    session.commit()
                    st.success("User registered successfully. Please login.")
                except SQLAlchemyError as e:
                    session.rollback()
                    st.error(f"Database error during registration: {e}")

                

# User is logged in
else:
    user = get_current_user()
    st.sidebar.write(f"Logged in as: {user.username} ({user.role})")

    if st.sidebar.button("Logout"):
        logout()
        st.success("Logged out successfully")

    # --- Admin dashboard ---
    if user.role == "admin":
        st.header("Admin Dashboard")

        # --- Add core data entities ---

        st.subheader("Add Subject")
        new_subject = st.text_input("Subject Name", key="new_subject")
        if st.button("Add Subject"):
            if new_subject.strip() == "":
                st.warning("Subject name cannot be empty.")
            else:
                exists = session.query(Subject).filter_by(name=new_subject.strip()).first()
                if exists:
                    st.warning("Subject already exists.")
                else:
                    subject = Subject(name=new_subject.strip())
                    try:
                        session.add(subject)
                        session.commit()
                        st.success(f"Subject '{new_subject.strip()}' added.")
                    except SQLAlchemyError as e:
                        session.rollback()
                        st.error(f"Error adding subject: {e}")

                    

        st.subheader("Add Classroom")
        new_classroom = st.text_input("Classroom Name", key="new_classroom")
        classroom_capacity = st.number_input("Capacity", min_value=1, step=1, key="classroom_capacity")
        if st.button("Add Classroom"):
            if new_classroom.strip() == "":
                st.warning("Classroom name cannot be empty.")
            elif classroom_capacity <= 0:
                st.warning("Capacity must be greater than 0.")
            else:
                exists = session.query(Classroom).filter_by(name=new_classroom.strip()).first()
                if exists:
                    st.warning("Classroom already exists.")
                else:
                    classroom = Classroom(name=new_classroom.strip(), capacity=classroom_capacity)
                    try:
                        session.add(classroom)
                        session.commit()
                        st.success(f"Classroom '{new_classroom.strip()}' added with capacity {classroom_capacity}.")
                    except SQLAlchemyError as e:
                        session.rollback()
                        st.error(f"Error adding subject: {e}")
                    
        if st.button("Generate 45-minute Slots for Selected Day"):
            existing = session.query(TimeSlot).filter_by(day=selected_day).all()
            if existing:
                st.warning(f"Time slots for {selected_day} already exist. Skipping generation.")
            else:
                try:
                    for start_t, end_t in generate_valid_timeslots():
                        new_slot = TimeSlot(day=selected_day, start_time=start_t, end_time=end_t)
                        session.add(new_slot)
                    session.commit()
                    st.success(f"Time slots for {selected_day} generated successfully.")
                except SQLAlchemyError as e:
                    session.rollback()
                    st.error(f"Error generating time slots: {e}")




        # --- Query fresh data for dropdowns every rerun ---
        teachers = session.query(User).filter_by(role='teacher').all()
        subjects = session.query(Subject).all()
        classrooms = session.query(Classroom).all()
        timeslots = session.query(TimeSlot).all()

        # --- Assign Subjects to Teacher ---
        st.subheader("Assign Subjects to Teacher")
        if teachers and subjects:
            teacher_sel = st.selectbox("Select Teacher", [t.username for t in teachers], key="mapping_teacher")
            subject_sel = st.multiselect("Select Subjects", [s.name for s in subjects])
            if st.button("Add Mapping"):
                try:
                    selected_teacher = next((t for t in teachers if t.username == teacher_sel), None)
                    if selected_teacher:
                        for subj_name in subject_sel:
                            subj = next((s for s in subjects if s.name == subj_name), None)
                            if subj:
                                exists = session.query(TeacherSubject).filter_by(teacher_id=selected_teacher.id, subject_id=subj.id).first()
                                if not exists:
                                    session.add(TeacherSubject(teacher_id=selected_teacher.id, subject_id=subj.id))
                        session.commit()
                        st.success("Mappings updated")
                except SQLAlchemyError as e:
                    session.rollback()
                    st.error(f"Error assigning subjects: {e}")

        else:
            st.info("Add teachers and subjects first to assign mappings.")

        # --- Schedule a class ---
        st.subheader("Schedule a Class")

        # Expire session cache to ensure fresh data
        session.expire_all()

        # Fetch fresh data
        subjects = session.query(Subject).all()
        classrooms = session.query(Classroom).all()
        timeslots = session.query(TimeSlot).all()

        
        if subjects and classrooms and timeslots:
            subj_name = st.selectbox("Subject", [s.name for s in subjects])
            selected_subject = next(s for s in subjects if s.name == subj_name)

            # Fetch teachers assigned to this subject
            mapped_teachers = session.query(TeacherSubject).filter_by(subject_id=selected_subject.id).all()
            teacher_ids = [mt.teacher_id for mt in mapped_teachers]
            available_teachers = session.query(User).filter(User.id.in_(teacher_ids)).all()

            if not available_teachers:
                st.warning("No teachers mapped to this subject. Please assign first.")
            else:
                teacher_name = st.selectbox("Select Teacher", [t.username for t in available_teachers], key="schedule_teacher")
                selected_teacher = next(t for t in available_teachers if t.username == teacher_name)

                classroom_name = st.selectbox("Classroom", [c.name for c in classrooms], key="schedule_classroom")
                timeslot_desc = st.selectbox("Time Slot", [f"{t.day} {t.start_time}-{t.end_time}" for t in timeslots], key="schedule_timeslot")
                is_lab = st.checkbox("Is Lab?")
                if st.button("Schedule Class"):
                    classroom = next(c for c in classrooms if c.name == classroom_name)
                    timeslot = next(t for t in timeslots if f"{t.day} {t.start_time}-{t.end_time}" == timeslot_desc)

                    # Check for duplicate schedule
                    duplicate_schedule = session.query(Schedule).filter_by(
                        teacher_id=selected_teacher.id,
                        subject_id=selected_subject.id,
                        timeslot_id=timeslot.id
                    ).first()

                    if duplicate_schedule:
                        st.error("This teacher is already scheduled to teach this subject at the selected time.")
                    else:
                        # Proceed with conflict checking and scheduling
                        classroom_conflict = session.query(Schedule).filter_by(
                            classroom_id=classroom.id, timeslot_id=timeslot.id
                        ).first()
                        teacher_conflict = session.query(Schedule).filter_by(
                            teacher_id=selected_teacher.id, timeslot_id=timeslot.id
                        ).first()

                        next_timeslot = None
                        if is_lab:
                            day_slots = sorted(
                                [t for t in timeslots if t.day == timeslot.day],
                                key=lambda t: parse_time_if_needed(t.start_time)
                            )
                            for idx, t in enumerate(day_slots):
                                if t.id == timeslot.id and idx + 1 < len(day_slots):
                                    next_timeslot = day_slots[idx + 1]
                                    break

                        if is_lab and next_timeslot:
                            classroom_conflict2 = session.query(Schedule).filter_by(
                                classroom_id=classroom.id, timeslot_id=next_timeslot.id
                            ).first()
                            teacher_conflict2 = session.query(Schedule).filter_by(
                                teacher_id=selected_teacher.id, timeslot_id=next_timeslot.id
                            ).first()
                        else:
                            classroom_conflict2 = teacher_conflict2 = None

                        if classroom_conflict or teacher_conflict:
                            st.error("Classroom or teacher is already occupied at the selected time.")
                        elif is_lab and (not next_timeslot or classroom_conflict2 or teacher_conflict2):
                            st.error("Cannot schedule lab: consecutive slot unavailable for classroom or teacher.")
                        else:
                            try:
                                session.add(Schedule(
                                    subject_id=selected_subject.id,
                                    teacher_id=selected_teacher.id,
                                    classroom_id=classroom.id,
                                    timeslot_id=timeslot.id,
                                    is_lab=is_lab
                                ))

                                if is_lab and next_timeslot:
                                    session.add(Schedule(
                                        subject_id=selected_subject.id,
                                        teacher_id=selected_teacher.id,
                                        classroom_id=classroom.id,
                                        timeslot_id=next_timeslot.id,
                                        is_lab=is_lab
                                    ))

                                session.commit()
                                st.success("Class scheduled successfully.")
                            except Exception as e:
                                session.rollback()
                                st.error(f"Error scheduling class: {e}")



        else:
            st.info(" Add subjects, classrooms, and timeslots before scheduling classes.")
            st.write(" DEBUG - subjects:", subjects)
            st.write(" DEBUG - classrooms:", classrooms)
            st.write(" DEBUG - timeslots:", timeslots)


        # --- Process edit requests ---
        st.subheader("Edit Requests")
        requests = session.query(EditRequest).filter_by(status='pending').all()
        for req in requests:
            sched = session.query(Schedule).get(req.schedule_id)
            subj = session.query(Subject).get(sched.subject_id)
            teacher_req = session.query(User).get(req.teacher_id)
            timeslot_new = session.query(TimeSlot).get(req.new_timeslot_id) if req.new_timeslot_id else None
            classroom_new = session.query(Classroom).get(req.new_classroom_id) if req.new_classroom_id else None

            st.write(f"Request ID: {req.id}")
            st.write(f"Teacher: {teacher_req.username}")
            st.write(f"Class: {subj.name}")
            st.write(f"Requested timeslot: {timeslot_new.day if timeslot_new else 'No change'}")
            st.write(f"Requested classroom: {classroom_new.name if classroom_new else 'No change'}")

            action = st.selectbox(f"Action for request {req.id}", ['pending', 'approved', 'rejected'], key=f"action_{req.id}")
            if st.button(f"Submit decision for {req.id}"):
                try:
                    req.status = action
                    if action == 'approved':
                        sched.timeslot_id = req.new_timeslot_id or sched.timeslot_id
                        sched.classroom_id = req.new_classroom_id or sched.classroom_id
                        sched.version += 1
                    session.commit()
                    st.success(f"Request {req.id} updated")
                except SQLAlchemyError as e:
                    session.rollback()
                    st.error(f"Error processing request: {e}")


        # --- Setup elective groups ---
        st.subheader("Setup Elective Group")
        group_name = st.text_input("Elective Group Name")
        schedules = session.query(Schedule).all()
        schedule_options = [f"{s.id} - Subject {s.subject_id}" for s in schedules]
        selected_schedules = st.multiselect("Select Schedules", schedule_options)
        if st.button("Create Elective Group"):
            if group_name:
                try:
                    group = ElectiveGroup(name=group_name)
                    session.add(group)
                    session.commit()
                    for opt in selected_schedules:
                        sid = int(opt.split()[0])
                        session.add(ElectiveMembership(group_id=group.id, schedule_id=sid))
                    session.commit()
                    st.success("Elective group created")
                except SQLAlchemyError as e:
                    session.rollback()
                    st.error(f"Error creating elective group: {e}")
            else:
                st.warning("Please enter group name")


        # --- Download timetable PDF ---

        # When the user clicks Download PDF:
        if st.button("Download PDF"):
            try:
                schedules = session.query(Schedule).all()
                buffer = generate_schedule_pdf(schedules)
                st.download_button("Download Timetable PDF", data=buffer, file_name="timetable.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error generating PDF: {e}")

    # --- Teacher dashboard ---
    elif user.role == "teacher":
        st.header("Teacher Dashboard")

        try:
            schedules = session.query(Schedule).filter_by(teacher_id=user.id).all()
            st.subheader("Your Schedule")
            if schedules:
                for s in schedules:
                    try:
                        subject = session.query(Subject).get(s.subject_id)
                        classroom = session.query(Classroom).get(s.classroom_id)
                        timeslot = session.query(TimeSlot).get(s.timeslot_id)
                        st.write(f"{subject.name} in {classroom.name} on {timeslot.day} {timeslot.start_time}-{timeslot.end_time}")
                    except Exception as e:
                        st.error(f"Error fetching schedule details: {e}")
                try:
                    buffer = generate_schedule_pdf(schedules, filename="teacher_timetable.pdf")
                    st.download_button("Download PDF", data=buffer, file_name="teacher_timetable.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")    
            else:
                st.info("No schedules assigned yet.")
        except SQLAlchemyError as e:
            st.error(f"Error retrieving schedule: {e}")

        st.subheader("Request Class Edit")
        try:
            if schedules:
                class_display = {
                    f"{s.id} - {session.query(Subject).get(s.subject_id).name} on {session.query(TimeSlot).get(s.timeslot_id).day} {session.query(TimeSlot).get(s.timeslot_id).start_time}-{session.query(TimeSlot).get(s.timeslot_id).end_time}": s.id
                    for s in schedules
                }
                selected_class_display = st.selectbox("Select class to edit", list(class_display.keys()), key="teacher_edit_class")
                selected_id = class_display[selected_class_display]

                timeslots = session.query(TimeSlot).all()
                classrooms = session.query(Classroom).all()

                timeslot_display = {
                    f"{t.id} - {t.day} {t.start_time}-{t.end_time}": t.id for t in timeslots
                }
                classroom_display = {f"{c.name} (Capacity: {c.capacity})": c.id for c in classrooms}

                selected_timeslot_display = st.selectbox("New Timeslot", list(timeslot_display.keys()), key="teacher_edit_timeslot")

                selected_classroom_display = st.selectbox("New Classroom", list(classroom_display.keys()), key="teacher_edit_classroom")

                new_timeslot_id = timeslot_display[selected_timeslot_display]
                new_classroom_id = classroom_display[selected_classroom_display]

                if st.button("Submit Edit Request"):
                    try:
                        edit_req = EditRequest(
                            teacher_id=user.id,
                            schedule_id=selected_id,
                            new_timeslot_id=new_timeslot_id,
                            new_classroom_id=new_classroom_id,
                            status='pending'
                        )
                        session.add(edit_req)
                        session.commit()
                        st.success("Edit request submitted")
                    except SQLAlchemyError as e:
                        session.rollback()
                        st.error(f"Error submitting edit request: {e}")
            else:
                st.info("No schedules to edit.")
        except SQLAlchemyError as e:
            st.error(f"Error loading edit form data: {e}")


    # --- Student dashboard ---
    elif user.role == "student":
        st.header("Student Dashboard")
        st.subheader("View Elective Groups")

        try:
            groups = session.query(ElectiveGroup).all()
            student_schedules = []

            if groups:
                for group in groups:
                    st.write(f"Group: {group.name}")
                    memberships = session.query(ElectiveMembership).filter_by(group_id=group.id).all()
                    for mem in memberships:
                        try:
                            schedule = session.query(Schedule).get(mem.schedule_id)
                            subject = session.query(Subject).get(schedule.subject_id)
                            timeslot = session.query(TimeSlot).get(schedule.timeslot_id)
                            classroom = session.query(Classroom).get(schedule.classroom_id)

                            st.write(f"- {subject.name} in {classroom.name} on {timeslot.day} {timeslot.start_time}-{timeslot.end_time}")
                            student_schedules.append(schedule)
                        except Exception as e:
                            st.warning(f"Error processing a schedule: {e}")
            else:
                st.info("No elective groups available.")

            if student_schedules:
                try:
                    buffer = generate_schedule_pdf(student_schedules, filename="student_timetable.pdf")
                    st.download_button("Download PDF", data=buffer, file_name="student_timetable.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")
            else:
                st.info("No schedules available to download.")

        except SQLAlchemyError as e:
            st.error(f"Error fetching elective groups: {e}")
