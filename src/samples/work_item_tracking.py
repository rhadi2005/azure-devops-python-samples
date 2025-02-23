"""
WIT samples
"""
import datetime
import logging

from samples import resource
from utils import emit

from azure.devops.v5_1.work_item_tracking.models import Wiql

logger = logging.getLogger(__name__)


def print_work_item(work_item):

    assigned_to = work_item.fields.get("System.AssignedTo")
    assigned_to = assigned_to.get("displayName") if assigned_to != None else None

    emit(
        "{0} {1} {2} {3} {4}: {5}".format(
            work_item.fields["System.WorkItemType"],
            work_item.id,
            work_item.fields["System.IterationPath"],
            work_item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate"),
            assigned_to,
            work_item.fields["System.Title"],
        )
    )


@resource("work_items")
def get_work_items(context):
    wit_client = context.connection.clients.get_work_item_tracking_client()

    desired_ids = range(1, 201)
    work_items = wit_client.get_work_items(ids=desired_ids, error_policy="omit")

    for id_, work_item in zip(desired_ids, work_items):
        if work_item:
            print_work_item(work_item)
        else:
            emit("(work item {0} omitted by server)".format(id_))

    return work_items


@resource("work_items")
def get_work_items_as_of(context):
    wit_client = context.connection.clients.get_work_item_tracking_client()

    desired_ids = range(1, 201)
    as_of_date = datetime.datetime.now() + datetime.timedelta(days=-7)
    work_items = wit_client.get_work_items(
        ids=desired_ids, as_of=as_of_date, error_policy="omit"
    )

    for id_, work_item in zip(desired_ids, work_items):
        if work_item:
            print_work_item(work_item)
        else:
            emit("(work item {0} omitted by server)".format(id_))

    return work_items


@resource("wiql_query")
def wiql_query(context):
    wit_client = context.connection.clients.get_work_item_tracking_client()
    wiql = Wiql(
        query="""
        select [System.Id],
            [System.WorkItemType],
            [System.Title],
            [System.State],
            [System.AreaPath],
            [System.IterationPath],
            [System.Tags]
        from WorkItems
        where [System.WorkItemType] = 'Task'
        order by [System.ChangedDate] desc"""
    )
    # We limit number of results to 30 on purpose
    wiql_results = wit_client.query_by_wiql(wiql, top=100).work_items
    emit("Results: {0}".format(len(wiql_results)))
    if wiql_results:
        # WIQL query gives a WorkItemReference with ID only
        # => we get the corresponding WorkItem from id
        work_items = (
            wit_client.get_work_item(int(res.id)) for res in wiql_results
        )
        for work_item in work_items:
            print_work_item(work_item)
        return work_items
    else:
        return []
