from nlp4all import db, bcrypt
from nlp4all.models import User, Role, Organization, Project
db.create_all()
db.session.commit()

admin_role = Role(name='Admin')
db.session.add(admin_role)
student_role = Role(name='Student')
db.session.add(admin_role)
teacher_role = Role(name='Teacher')
db.session.add(admin_role)
db.session.commit()

hp = bcrypt.generate_password_hash("Hermes_2014")
user = User(username="arthurhjorth", email="arthur.hjorth@stx.oxon.org", password=hp)
user.roles = [admin_role,]
db.session.add(user)
user = User(username="arthurhjorth_teacher", email="arthur.hjorth@u.northwestern.edu", password=hp)
user.roles = [teacher_role,]
db.session.add(user)
user = User(username="arthurhjorth_student", email="hermeshjorth2011@u.northwestern.edu", password=hp)
user.roles = [student_role,]
db.session.add(user)
db.session.commit()
org = Organization(name="UBI/CCTD")
db.session.add(org)
db.session.commit()
project = Project(name="Test Project", organization=org.id)
db.session.add(project)
db.session.commit()

