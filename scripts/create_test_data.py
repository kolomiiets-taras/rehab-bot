import asyncio
from datetime import datetime, timedelta, date, time

from faker import Faker
from passlib.handlers.bcrypt import bcrypt

from app.db.database import async_session
from app.models.user import User, UserCourse, DailySession
from app.models.course import Course, CourseItem
from app.models.complex import Complex, ComplexExercise
from app.models.exercise import Exercise
from app.models.employee import Employee, Role

faker = Faker("uk_UA")


async def populate_test_data():
    async with async_session() as session:
        # 1. Exercises
        exercises = [
            Exercise(title=faker.word(), text=faker.sentence())
            for i in range(1, 21)
        ]
        session.add_all(exercises)
        await session.flush()

        # 2. Complexes with Exercises
        complexes = []
        for i in range(10):
            complex_obj = Complex(name=f"Комплекс {i+1}")
            session.add(complex_obj)
            await session.flush()

            selected_exercises = faker.random_elements(elements=exercises, length=3, unique=True)
            for pos, ex in enumerate(selected_exercises):
                session.add(ComplexExercise(complex_id=complex_obj.id, exercise_id=ex.id, position=pos))
            complexes.append(complex_obj)

        # 3. Courses with Complexes
        courses = []
        for i in range(5):
            course = Course(name=faker.catch_phrase())
            session.add(course)
            await session.flush()

            selected_complexes = faker.random_elements(elements=complexes, length=3, unique=True)
            for pos, cx in enumerate(selected_complexes):
                session.add(CourseItem(course_id=course.id, complex_id=cx.id, position=pos))
            courses.append(course)

        # 4. Users with UserCourse & DailySession
        users = []
        for i in range(10):
            user = User(
                telegram_id=1000000 + i,
                phone=faker.phone_number(),
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                birthday=faker.date_of_birth(minimum_age=18, maximum_age=50),
                created_at=datetime.now()
            )
            session.add(user)
            await session.flush()

            course = faker.random_element(elements=courses)
            progress = ''.join(faker.random_choices(elements=["0", "1"], length=14))
            current_position = faker.random_int(min=0, max=len(progress)-1)
            user_course = UserCourse(
                user_id=user.id,
                course_id=course.id,
                created_at=datetime.now(),
                progress=progress,
                current_position=current_position,
                finished=(current_position == len(progress)-1),
                mailing_time=time(),
                mailing_days=",".join(str(d) for d in faker.random_elements(elements=range(1, 8), length=3, unique=True))
            )
            session.add(user_course)
            await session.flush()

            for j in range(5):
                session.add(DailySession(
                    user_course_id=user_course.id,
                    date=date.today() - timedelta(days=j),
                    pulse_before=faker.random_int(min=60, max=100),
                    pulse_after=faker.random_int(min=60, max=100),
                    wellbeing_before=faker.random_int(min=1, max=5),
                    wellbeing_after=faker.random_int(min=1, max=5),
                ))
            users.append(user)

        hashed_password = bcrypt.hash('1234')
        # 5. Admin Employee
        owner = Employee(
            email="owner@owner.com",
            password=hashed_password,
            role=Role.OWNER,
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            phone=faker.phone_number(),
            created_at=datetime.now()
        )
        admin = Employee(
            email="admin@admin.com",
            password=hashed_password,
            role=Role.ADMIN,
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            phone=faker.phone_number(),
            created_at=datetime.now()
        )
        doctor = Employee(
            email="doctor@doctor.com",
            password=hashed_password,
            role=Role.DOCTOR,
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            phone=faker.phone_number(),
            created_at=datetime.now()
        )
        session.add(owner)
        session.add(admin)
        session.add(doctor)

        await session.commit()
        print("✅ Тестові дані успішно додані.")

if __name__ == "__main__":
    asyncio.run(populate_test_data())
