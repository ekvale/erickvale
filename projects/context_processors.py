from .models import Notification


def notification_count(request):
    if not request.user.is_authenticated:
        return {'unread_notification_count': 0}
    n = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return {'unread_notification_count': n}
