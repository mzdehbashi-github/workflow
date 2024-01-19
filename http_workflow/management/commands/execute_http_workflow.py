import asyncio
import logging
from typing import Tuple, List

from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
import aiohttp

from http_workflow.models import HTTPRequest, HTTPWorkflow, Step


logger = logging.getLogger(__name__)


@sync_to_async
def step_succeeded(step):
    return step.succeeded


@sync_to_async
def get_workflow_steps(workflow):
    return list(workflow.step_set.all())


@sync_to_async
def get_step_http_requests(step: Step) -> List[HTTPRequest]:
    return step.httprequest_set.all()


@sync_to_async
def update_request_status(request: HTTPRequest, status: int) -> HTTPRequest:
    request.status = status
    request.save(update_fields=('status',))
    return request


async def execute_http_request(session, request: HTTPRequest) -> HTTPRequest:
    method = request.method
    url = request.url
    body = request.body

    async with session.request(method, url, json=body) as response:
        status = response.status

        # Update the status in the database
        updated_request = await update_request_status(request, status)
        return updated_request


async def execute_step(step: Step) -> bool:
    if await step_succeeded(step):
        logger.info(f'{step.id=} already succeeded. Skipping.')
        return True

    requests = await get_step_http_requests(step)

    async with aiohttp.ClientSession() as session:
        tasks = [
            execute_http_request(session, request)
            for request in requests
            if not request.succeeded
        ]

        result: Tuple[HTTPRequest] = await asyncio.gather(*tasks)

    # Check if all requests succeeded
    return all(http_request.succeeded for http_request in result)


async def execute_workflow(workflow) -> None:
    steps = await get_workflow_steps(workflow)

    for step in steps:
        success = await execute_step(step)

        # Handle step success or failure as needed
        if success:
            logger.info(f'{step.id=} succeeded.')
        else:
            logger.error(f'{step.id=} failed.')
            break  # Stop further execution if a step fails


class Command(BaseCommand):
    help = 'Executes the given `HTTPWorkFlow`'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("http_work_flow_id", type=int)

    def handle(self, *args, **options):
        http_workflow = HTTPWorkflow.objects.get(id=options['http_work_flow_id'])
        asyncio.run(execute_workflow(http_workflow))
