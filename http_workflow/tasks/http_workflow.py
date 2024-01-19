import logging

from django.db import transaction
from django.db.models import Prefetch
from celery import chain, group, shared_task
import requests

from http_workflow.models import HTTPWorkflow, Step, HTTPRequest


logger = logging.getLogger(__name__)


@shared_task
def send_http_request(http_request_id: int):
    # Just to do a double check, in case the http_request has been already sent.
    # This occasion might happen if another celery task (def `send_http_request`) for the
    # same `http_request_id` has been executed (by mistake), between the time
    # that this celery task got enqueued and is about to be executed.
    queryset = HTTPRequest.objects.select_for_update().filter(id=http_request_id)

    with transaction.atomic():
        http_request = queryset.get()
        response = requests.request(
            http_request.method,
            http_request.url,
            json=http_request.body
        )

        http_request.status = response.status_code
        http_request.save(update_fields=('status',))


@shared_task
def generate_celery_workflow(http_workflow_id: int):
    """
    Generates celery workflow for the given `http_workflow_id`

    The generated workflow would be a chain which contain sub-chains for evey `Step`
    within the related `HTTPWorkflow` record. Every sub-chain, would contain a group
    of tasks, which contains one task per every `HTTPRequest` related to that step.
    """

    # TODO: implement a lock (using redis for example) to prevent executing a workflow twice at the same time
    # find the id of the previous chain_of_steps (if exists) and check celery results backend if it is still in progress

    http_workflow: HTTPWorkflow
    http_workflow = HTTPWorkflow.objects.filter(
        id=http_workflow_id
    ).prefetch_related(
        Prefetch(
            'step_set',
            Step.objects.prefetch_related('httprequest_set')
        )
    ).get()

    if http_workflow.succeeded:
        logger.info(f'{http_workflow.id=} already succeeded. Skipping.')
        return

    # Contains sub-chains, for every `Step` (which is not already succeeded)
    chain_of_steps = chain()

    step: Step
    for step in http_workflow.step_set.order_by('ordering'):
        if step.succeeded:
            logger.info(f'{step.id=} already succeeded. Skipping.')
            continue

        group_list = []
        http_request: HTTPRequest
        for http_request in step.httprequest_set.all():
            if http_request.succeeded:
                logger.info(f'{http_request.id=} already succeeded. Skipping.')
                continue

            group_list.append(send_http_request.si(http_request_id=http_request.id))

        if group_list:
            group_of_http_requests = group(group_list)
            chain_of_steps |= chain(group_of_http_requests)

    if chain_of_steps.tasks:
        chain_of_steps.apply_async()
