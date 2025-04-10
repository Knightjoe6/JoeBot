from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
import uuid
from datetime import datetime, timedelta
from pytz import utc
import os

class TaskScheduler:
    def __init__(self):        
        MYSQL_HOST = os.getenv('MYSQL_HOST')
        MYSQL_USER = os.getenv('MYSQL_USER')
        MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
        MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

        jobstores = {
            'default': SQLAlchemyJobStore(engine=create_engine(f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}')),
        }
        executors = {
            'default': AsyncIOExecutor(),
        }
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone=utc
        )
        self.scheduler.start()

    def parse_duration(self, duration):
        unit = duration[-1]
        amount = int(duration[:-1])
        if unit == 'm':
            return timedelta(minutes=amount)
        elif unit == 'h':
            return timedelta(hours=amount)
        elif unit == 'd':
            return timedelta(days=amount)
        elif unit == 'w':
            return timedelta(weeks=amount)
        else:
            raise ValueError("Invalid duration format")

    def schedule_task(self, func, args, duration):
        parsed_duration = self.parse_duration(duration)
        trigger_time = datetime.utcnow() + parsed_duration

        if trigger_time > datetime.utcnow() + timedelta(days=28):
            raise ValueError("Duration exceeds maximum limit of 28 days")

        job_id = str(uuid.uuid4())
        
        job = self.scheduler.add_job(func, 'date', run_date=trigger_time, args=args, id=job_id)
        return job
        # print(f"Scheduled task for {trigger_time}, current time is {datetime.utcnow()} with ID {job_id}")
        # return job_id