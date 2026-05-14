from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from .models import Comment, Notification, Task, TaskStatus


@receiver(pre_save, sender=Task)
def task_cache_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Task.objects.only('status').get(pk=instance.pk)
            instance._previous_status = old.status
        except Task.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(m2m_changed, sender=Task.assignees.through)
def notify_new_assignees(sender, instance, action, pk_set, **kwargs):
    if action != 'post_add' or not pk_set:
        return
    if not isinstance(instance, Task):
        return
    actor_id = getattr(instance, '_actor_id', None)
    User = get_user_model()
    for user_id in pk_set:
        if actor_id and user_id == actor_id:
            continue
        try:
            assignee = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            continue
        Notification.objects.create(
            recipient=assignee,
            verb='assigned you to a task',
            actor_id=actor_id,
            target_task=instance,
            target_project=instance.project,
        )


@receiver(post_save, sender=Comment)
def notify_comment_on_task(sender, instance, created, **kwargs):
    if not created:
        return
    task = instance.task
    assignee_ids = set(task.assignees.values_list('pk', flat=True))
    assignee_ids.discard(instance.author_id)
    for uid in assignee_ids:
        Notification.objects.create(
            recipient_id=uid,
            verb='commented on a task you are assigned to',
            actor=instance.author,
            target_task=task,
            target_project=task.project,
        )


@receiver(post_save, sender=Task)
def notify_task_marked_done(sender, instance, **kwargs):
    prev = getattr(instance, '_previous_status', None)
    if prev is None or prev == TaskStatus.DONE or instance.status != TaskStatus.DONE:
        return
    actor = getattr(instance, '_actor', None)
    created_by = instance.created_by
    if not created_by:
        return
    if actor is not None and actor.pk == created_by.pk:
        return
    Notification.objects.create(
        recipient=created_by,
        verb='marked a task complete',
        actor=actor,
        target_task=instance,
        target_project=instance.project,
    )
