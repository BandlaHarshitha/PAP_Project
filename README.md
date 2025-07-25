# PAP_Project

This is a Timetable Generator application using Python

Functionalities: This application allows three types of users
	- Student
	- Teacher
	- Admin
The Admin can Add subjects/elective groups, Classrooms, map teachers to subjects and schedule classes
The teachers can make requests to make changes to the schedule
and all three users have an option to download the PDF

Bugs and other areas of improvement needed:

- Poor structuring of the code, can introduce modularity
- Opt for a more object Oriented implementation
- The time table must be displayed in a more structured format. Like using a grid like structure to display according to typical time table structure(days x time)
- Possible conflict during edit request functionality for teachers, if multiple users are accessing at once.
- Elective groups for multiple sections of a semester taught in one session should be managed
- There is no handling implemented for semester/academic year structures. Also multiple sections are not handled
- Notify users of changes in schedules
