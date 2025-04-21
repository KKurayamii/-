from django.contrib.auth.models import AbstractUser
from django.conf import settings
import os
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.utils import timezone
from geopy.geocoders import Nominatim
import markdown


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('medical_officer', 'Medical Officer'),
        ('admin','Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    SEX_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, default='other')

    def __str__(self):
        return self.username

class Role(models.Model):
    name = models.CharField(max_length=50)
    permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.name


class Articles(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='articles')
    image = models.ImageField(upload_to='article_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def formatted_content(self):
        return markdown.markdown(self.content)

class HealthRecord1(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    blood_pressure = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    bmi = models.FloatField(blank=True, null=True)
    insulin = models.FloatField(blank=True, null=True)
    fasting_blood_sugar = models.FloatField(blank=True, null=True)
    postprandial_blood_sugar = models.FloatField(blank=True, null=True)
    hba1c = models.FloatField(blank=True, null=True)
    bun = models.FloatField(blank=True, null=True)
    cr = models.FloatField(blank=True, null=True)
    egfr = models.FloatField(blank=True, null=True)
    triglycerides = models.FloatField(blank=True, null=True)
    cholesterol = models.FloatField(blank=True, null=True)
    hdl = models.FloatField(blank=True, null=True)
    ldl = models.FloatField(blank=True, null=True)
    albumin_in_urine = models.FloatField(blank=True, null=True)
    ekg = models.TextField(blank=True, null=True)
    chest_x_ray = models.TextField(blank=True, null=True)
    diabetic_retinopathy_screening = models.TextField(blank=True, null=True)
    diabetic_foot_screening = models.TextField(blank=True, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True)
    last_visit_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Record {self.id} - {self.last_visit_date}"

    def save(self, *args, **kwargs):
        if self.weight and self.height:
            self.bmi = self.weight / ((self.height / 100) ** 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.date_recorded}"


class Diagnosis_N(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    health_record1_id = models.ForeignKey(HealthRecord1, null=True, blank=True, on_delete=models.CASCADE)
    bmi = models.FloatField()
    blood_pressure = models.FloatField()
    pregnancies = models.IntegerField()
    glucose = models.FloatField()
    skin_thickness = models.FloatField()
    insulin = models.FloatField()
    diabetes_pedigree_function = models.FloatField()
    age = models.IntegerField()
    prediction = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # ข้อมูลส่วนตัว
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"Diagnosis_N for {self.user.username} - {self.prediction}"


class DiagnosisHistory(models.Model):
    diagnosis = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for Patient {self.patient_id}: {self.diagnosis}"

class MLModel(models.Model):
    name = models.CharField(max_length=255)
    model_file = models.FileField(upload_to="models/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Model uploaded at {self.uploaded_at}'

class MedicationRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ผู้ใช้ที่ส่งคำขอ
    medication_name = models.CharField(max_length=255)  # ชื่อยา
    message = models.TextField()  # ข้อความเตือน
    date_sent = models.DateTimeField()  # วันที่และเวลาที่ต้องการส่งอีเมล
    is_active = models.BooleanField(default=True)  # ใช้ตรวจสอบว่าคำขอนี้ยังต้องส่งอยู่หรือไม่
    daily_notification = models.BooleanField(default=False)  # แจ้งเตือนทุกวัน (เช็คเมื่ออยากให้แจ้งเตือนทุกวัน)

    def __str__(self):
        return f"Medication request for {self.medication_name} by {self.user.username}"