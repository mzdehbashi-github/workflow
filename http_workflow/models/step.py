from django.db import models


class Step(models.Model):
    """
    Represents a step in a workflow.

    Every Step belongs to an HTTP workflow and all steps within a
    http workflow gets executed sequentially in a specific order.
    """
    http_workflow = models.ForeignKey(
        'http_workflow.HTTPWorkflow',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=255,
        help_text='''
        Makes reading and addressing steps easier.
        Not possible to have multiple steps within a http workflow with the same name.
        '''
    )
    ordering = models.PositiveSmallIntegerField(
        help_text='''
        Steps in a http workflow, will get executed in an'
        ascending order according to the value of this field.
        Not possible to have multiple steps within a http workflow with the same ordering.
        '''
    )

    @property
    def succeeded(self) -> bool:
        output = True
        for http_request in self.httprequest_set.all():
            if not http_request.succeeded:
                output = False
                break
        return output

    class Meta:
        unique_together = [
            ['name', 'http_workflow'],
            ['ordering', 'http_workflow'],
        ]
