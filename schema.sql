-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL -- 'admin', 'teacher', 'student'
);

-- Subjects
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL
);

-- Faculties (teachers) ↔ subjects (many-to-many)
CREATE TABLE teacher_subject (
    teacher_id INTEGER,
    subject_id INTEGER,
    PRIMARY KEY (teacher_id, subject_id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- Classrooms
CREATE TABLE classrooms (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    capacity INTEGER NOT NULL
);

-- TimeSlots (e.g. Mon 10–11)
CREATE TABLE timeslots (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    day VARCHAR(50) NOT NULL,
    start_time VARCHAR(20) NOT NULL,
    end_time VARCHAR(20) NOT NULL
);

-- Classes scheduled (REQ3–7)
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    subject_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    classroom_id INTEGER NOT NULL,
    timeslot_id INTEGER NOT NULL,
    is_lab INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,      -- for edits tracking
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id),
    FOREIGN KEY (timeslot_id) REFERENCES timeslots(id)
);

-- Electives grouping (REQ11)
CREATE TABLE elective_groups (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE elective_membership (
    group_id INTEGER,
    schedule_id INTEGER,
    PRIMARY KEY (group_id, schedule_id),
    FOREIGN KEY (group_id) REFERENCES elective_groups(id),
    FOREIGN KEY (schedule_id) REFERENCES schedule(id)
);

-- Timetable edit requests (REQ8)
CREATE TABLE edit_requests (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    schedule_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    new_timeslot_id INTEGER,
    new_classroom_id INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    FOREIGN KEY (schedule_id) REFERENCES schedule(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);
