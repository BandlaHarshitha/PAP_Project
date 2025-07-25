from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subject'
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), primary_key=True)

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

class TimeSlot(db.Model):
    __tablename__ = 'timeslots'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)

class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    timeslot_id = db.Column(db.Integer, db.ForeignKey('timeslots.id'), nullable=False)
    is_lab = db.Column(db.Boolean, default=False)
    version = db.Column(db.Integer, default=1)

class ElectiveGroup(db.Model):
    __tablename__ = 'elective_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class ElectiveMembership(db.Model):
    __tablename__ = 'elective_membership'
    group_id = db.Column(db.Integer, db.ForeignKey('elective_groups.id'), primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), primary_key=True)

class EditRequest(db.Model):
    __tablename__ = 'edit_requests'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    new_timeslot_id = db.Column(db.Integer, db.ForeignKey('timeslots.id'))
    new_classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'))
    status = db.Column(db.String(20), default='pending')

