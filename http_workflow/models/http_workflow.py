from django.db import models


class HTTPWorkflow(models.Model):
    """
    Represents a workflow.

    Contains collection of HTTP requests that should be sent in a specific way.
    Sequentially or in parallel or a combination of both.
    """
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    # TODO: add a new field `scheduled_at` to to be able to schedule execution time of an HTTP workflow

    @property
    def succeeded(self) -> bool:
        output = True
        for step in self.step_set.prefetch_related('httprequest_set').all():
            if not step.succeeded:
                output = False
                break
        return output
