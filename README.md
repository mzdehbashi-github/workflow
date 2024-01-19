# Workflow

**Description:**
The Workflow Django project is designed to facilitate the creation and execution of workflows that involve sending HTTP requests. Workflows can be structured to dispatch related HTTP requests sequentially, in parallel, or a combination of both, offering flexibility in designing complex interactions with external services.

To execute workflows, two different methods have been implemented: Celery for asynchronous task execution and asyncio for handling concurrent operations.

## Models Relationship

For a comprehensive understanding of the project's data structure and relationships,<br>
please refer to the following image depicting the models' relationships:

![Models Relationship](http_workflow_models.png)


## Execution Visualization

To gain insights into how the HTTP workflow execution is visualized,<br>
refer to the diagram provided in the following image:

![Execution Visualization](http_workflow_execution_diagram.png)
