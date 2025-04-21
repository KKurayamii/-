
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.mail import send_mail
from django.utils.timezone import now
from .models import MedicationRequest
from django.conf import settings

def send_scheduled_medication_emails():
    """เช็คและส่งอีเมลเตือนยาที่ถึงเวลาส่ง"""
    pending_requests = MedicationRequest.objects.filter(date_sent__lte=now(), is_active=True)

    for request in pending_requests:
        send_mail(
            subject=f"Reminder: {request.medication_name}",
            message=request.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        request.is_active = False  # ป้องกันการส่งซ้ำ
        request.save()

def start_scheduler():
    """เริ่มตัวจัดการเวลาเมื่อ Django รัน"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_scheduled_medication_emails, 'interval', minutes=1)  # ตรวจสอบทุก 1 นาที
    scheduler.start()