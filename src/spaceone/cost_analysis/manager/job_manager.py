import logging
from typing import List
from datetime import datetime, timedelta

from spaceone.core.error import *
from spaceone.core import queue, utils, config
from spaceone.core.manager import BaseManager
from spaceone.cost_analysis.model.job_model import Job

_LOGGER = logging.getLogger(__name__)


class JobManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_model: Job = self.locator.get_model('Job')
        self.job_timeout = config.get_global('JOB_TIMEOUT', 7200)

    def is_job_running(self, data_source_id, domain_id):
        job_vos: List[Job] = self.job_model.filter(data_source_id=data_source_id, domain_id=domain_id,
                                                   status='IN_PROGRESS')

        running_job_count = job_vos.count()

        for job_vo in job_vos:
            if datetime.utcnow() > (job_vo.created_at + timedelta(seconds=self.job_timeout)):
                self.change_timeout_status(job_vo)
                running_job_count -= 1

        if running_job_count > 0:
            return True
        else:
            return False

    def create_job(self, data_source_id, domain_id, total_tasks=None, last_changed_at=None):
        data = {
            'data_source_id': data_source_id,
            'domain_id': domain_id
        }

        if total_tasks:
            data.update({
                'total_tasks': total_tasks,
                'remained_tasks': total_tasks
            })

        if last_changed_at:
            data['last_changed_at'] = utils.iso8601_to_datetime(last_changed_at)

        _LOGGER.debug(f'[create_job] create job: {data}')

        return self.job_model.create(data)

    def update_job_by_vo(self, params, job_vo):
        return job_vo.update(params)

    def get_job(self, job_id, domain_id, only=None):
        return self.job_model.get(job_id=job_id, domain_id=domain_id, only=only)

    def filter_jobs(self, **conditions):
        return self.job_model.filter(**conditions)

    def list_jobs(self, query={}):
        return self.job_model.query(**query)

    def stat_jobs(self, query):
        return self.job_model.stat(**query)

    @staticmethod
    def decrease_remained_tasks(job_vo: Job):
        job_vo.decrement('remained_tasks', 1)

    @staticmethod
    def change_success_status(job_vo: Job):
        _LOGGER.error(f'[change_success_status] job success: {job_vo.job_id}')

        job_vo.update({
            'status': 'SUCCESS',
            'finished_at': datetime.utcnow()
        })

    @staticmethod
    def change_timeout_status(job_vo: Job):
        _LOGGER.error(f'[change_timeout_status] job timeout: {job_vo.job_id}')

        job_vo.update({
            'status': 'TIMEOUT',
            'finished_at': datetime.utcnow()
        })

    @staticmethod
    def change_error_status(job_vo: Job, e):
        if not isinstance(e, ERROR_BASE):
            e = ERROR_UNKNOWN(message=str(e))

        _LOGGER.error(f'[change_error_status] job error ({job_vo.job_id}): {e.message}', exc_info=True)

        job_vo.update({
            'status': 'ERROR',
            'error_code': e.error_code,
            'error_message': e.message,
            'finished_at': datetime.utcnow()
        })
