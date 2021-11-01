from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class PlannedLimit(EmbeddedDocument):
    date = StringField(required=True)
    limit = FloatField(required=True)


class MonthlyCost(EmbeddedDocument):
    date = StringField(required=True)
    usd_cost = FloatField(required=True)


class CostTypes(EmbeddedDocument):
    provider = ListField(StringField(), default=[])
    region_code = ListField(StringField(), default=[])
    account = ListField(StringField(), default=[])
    product = ListField(StringField(), default=[])

    def to_dict(self):
        return dict(self.to_mongo())


class Notification(EmbeddedDocument):
    threshold = FloatField(required=True)
    unit = StringField(max_length=20, choices=('PERCENT', 'ACTUAL_COST'))
    notification_type = StringField(max_length=20, choices=('CRITICAL', 'WARNING'))


class Budget(MongoModel):
    budget_id = StringField(max_length=40, generate_id='budget', unique=True)
    name = StringField(max_length=255, default='')
    limit = FloatField(required=True)
    planned_limits = ListField(EmbeddedDocumentField(PlannedLimit), default=[])
    total_usd_cost = FloatField(default=0)
    monthly_costs = ListField(EmbeddedDocumentField(MonthlyCost), default=[])
    cost_types = EmbeddedDocumentField(CostTypes, default=None, null=True)
    time_unit = StringField(max_length=20, choices=('TOTAL', 'MONTHLY', 'YEARLY'))
    start = DateField(required=True)
    end = DateField(required=True)
    notifications = ListField(EmbeddedDocumentField(Notification), default=[])
    tags = DictField(default={})
    project_id = StringField(max_length=40, default=None, null=True)
    project_group_id = StringField(max_length=40, default=None, null=True)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {
        'updatable_fields': [
            'name',
            'limit',
            'planned_limits',
            'total_usd_cost',
            'monthly_costs',
            'end',
            'notifications',
            'tags'
        ],
        'minimal_fields': [
            'budget_id',
            'name',
            'limit',
            'total_usd_cost',
            'project_id',
            'project_group_id'
        ],
        'change_query_keys': {
            'user_projects': 'project_id',
            'user_project_groups': 'project_group_id'
        },
        'ordering': ['name'],
        'indexes': [
            'budget_id',
            'name',
            'time_unit',
            'start',
            'end',
            'project_id',
            'project_group_id',
            'domain_id',
            'created_at'
        ]
    }