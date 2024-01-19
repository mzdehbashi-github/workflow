from django.db import models


class HTTPRequest(models.Model):
    """
    Represents an HTTP request.

    Every HTTP request, belongs to a `Step` record, and all
    HTTP requests within the same `Step` are going to be executed in parallel.
    """

    class MethodChoice(models.TextChoices):
        POST = 'post'

    method = models.CharField(max_length=10, choices=MethodChoice.choices)
    body = models.JSONField(null=True, blank=True)
    url = models.URLField()
    status = models.PositiveSmallIntegerField(
        null=True,
        help_text='Contains the response.status_code, if this record has benn executed at least once'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    step = models.ForeignKey(
        'http_workflow.Step',
        on_delete=models.CASCADE,
        help_text='''
        Belongs to this step, this record gets executed in parallel among other
        http request which belong to the same step
        '''
    )

    @property
    def succeeded(self) -> bool:
        # TODO: For better accuracy, when evaluating success of a http request
        #  Maybe add a new field to this model `expected_success_statuses` i.e. [200, 201, 301]
        return self.status in [200, 201, 204]
