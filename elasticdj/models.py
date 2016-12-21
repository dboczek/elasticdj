from django.db import models


class Log(models.Model):
    COMMANDS = (
        ("rebuild", "rebuild"),
        ("update", "update"),
    )
    command = models.CharField(max_length=7, choices=COMMANDS, editable=False)
    started_at = models.DateTimeField(auto_now_add=True, editable=False)
    finished_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        get_latest_by = 'started_at'
