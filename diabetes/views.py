from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm
from .models import DiagnosisHistory
from .forms import *
from .models import MLModel
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .models import HealthRecord1
from .forms import HealthRecord1Form
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Diagnosis_N
from django.db.models.functions import TruncMonth, TruncWeek
from django.db.models import Avg, Count
from geopy.exc import GeocoderTimedOut
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from .models import CustomUser, Articles, Diagnosis_N
import base64
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib import messages
import pickle

def is_admin_or_medical_staff(user):
    return user.is_staff or user.groups.filter(name='Medical Officer').exists()

# ฟังก์ชันสมัครสมาชิก
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():  # ตรวจสอบว่าฟอร์มถูกต้องหรือไม่
            user = form.save()  # บันทึกผู้ใช้
            login(request, user)  # ล็อกอินผู้ใช้ทันที
            return redirect('/login/')  # ไปที่หน้า dashboard
        else:
            print(form.errors)  # แสดงข้อผิดพลาดถ้าฟอร์มไม่ถูกต้อง
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

# ฟังก์ชันล็อกอิน (ใช้ LoginView ของ Django)
class CustomLoginView(LoginView):
    template_name = 'login.html'

def user_logout(request):
    logout(request)
    return redirect('login')
@login_required
def reset_password(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()  # บันทึกรหัสผ่านใหม่
            update_session_auth_hash(request, form.user)  # อัปเดต session เพื่อไม่ให้ล็อกอินออก
            messages.success(request, 'Your password has been successfully updated!')
            return redirect('login')  # หรือหน้าอื่นที่คุณต้องการให้ผู้ใช้ไปหลังจากรีเซ็ตรหัสผ่านเสร็จ
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResetPasswordForm(request.user)

    return render(request, 'reset_password.html', {'form': form})

# ฟังก์ชันแดชบอร์ด (ตรวจสอบสิทธิ์ผู้ใช้)
@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('admin/dashboard_adminn')
    elif request.user.role == 'medical_officer':
        return redirect('doctor/home_dc')
    return redirect('dashboard')


def feature_importance_view(request):
    model, uploaded_at = load_latest_model()

    if model is None:
        return render(request, 'feature_importance.html', {'error': 'No model found'})

    # ตรวจสอบว่าโมเดลมี feature_importances_ หรือไม่
    if not hasattr(model, "feature_importances_"):
        return render(request, 'feature_importance.html', {'error': 'Model does not support feature importance'})

    # โหลด Feature Importance
    importances = model.feature_importances_

    # ตัวอย่างชื่อฟีเจอร์ (ควรโหลดจากข้อมูลจริง)
    feature_names = ["Age", "Pregnancies", "Glucose", "BloodPressure", "Insulin", "BMI", "DiabetesPedigreeFunction", "SkinThickness"]

    # จับคู่ฟีเจอร์กับค่าความสำคัญ
    feature_importance = list(zip(feature_names, importances))
    feature_importance.sort(key=lambda x: x[1], reverse=True)

    # เลือก Top 5 Features
    top_features = feature_importance[:8]
    top_names, top_values = zip(*top_features)

    # สร้างกราฟ
    plt.figure(figsize=(10, 5))
    sns.barplot(x=top_values, y=top_names, palette='viridis')
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature Input Data")

    # แปลงเป็น base64 สำหรับแสดงใน HTML
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()

    return image_base64, uploaded_at

@login_required
def dashboard_adminn(request):
    # จำนวนสมาชิกทั้งหมด
    total_users = CustomUser.objects.count()

    # จำนวนบทความสุขภาพทั้งหมด
    total_articles = Articles.objects.count()

    # จำนวนการวินิจฉัยทั้งหมด
    total_diagnoses = Diagnosis_N.objects.count()

    # ดึงจำนวนสมาชิกที่สมัครใช้งานในแต่ละเดือน
    user_data = CustomUser.objects.extra(select={'month': "EXTRACT(MONTH FROM date_joined)"}).values('month').annotate(
        count=Count('id')).order_by('month')
    user_labels = [f'เดือน {item["month"]}' for item in user_data]
    user_counts = [item["count"] for item in user_data]

    # ดึงผลวินิจฉัยเพื่อแสดงเป็นกราฟโดนัท
    diagnosis_data = Diagnosis_N.objects.values('prediction').annotate(count=Count('id'))
    diagnosis_labels = [item['prediction'] for item in diagnosis_data]
    diagnosis_counts = [item['count'] for item in diagnosis_data]

    # ดึงสัดส่วนเพศของผู้ใช้
    gender_data = CustomUser.objects.values('sex').annotate(count=Count('id'))
    gender_labels = ['Male' if item['sex'] == 'M' else 'Female' for item in gender_data]
    gender_counts = [item['count'] for item in gender_data]

    age_mapping = {
        0: "children",
        1: "Adolescents",
        2: "Young Adult",
        3: "Middle-aged Adult",
        4: "Older Adult"
    }



    # ดึงข้อมูลผลวินิจฉัยแยกตามช่วงอายุ
    age_risk_data = Diagnosis_N.objects.values('age', 'prediction')
    age_risk_dict = {group: {"เสี่ยง": 0, "ไม่เสี่ยง": 0} for group in age_mapping.values()}

    for item in age_risk_data:
        age_code = item["age"]  # ได้ค่าตัวเลข เช่น 0, 1, 2
        prediction = item["prediction"]

        # แปลงค่าอายุจากตัวเลขเป็นช่วงอายุจริง
        age_group = age_mapping.get(age_code, "ไม่ระบุ")
        if age_group != "ไม่ระบุ":
            if prediction in ["เสี่ยง", "Risk"]:
                age_risk_dict[age_group]["เสี่ยง"] += 1
            else:
                age_risk_dict[age_group]["ไม่เสี่ยง"] += 1

    # เตรียมข้อมูลสำหรับกราฟ
    age_labels = list(age_risk_dict.keys())
    age_risk_counts = [age_risk_dict[group]["เสี่ยง"] for group in age_labels]
    age_no_risk_counts = [age_risk_dict[group]["ไม่เสี่ยง"] for group in age_labels]

    feature_image_base64, uploaded_at = feature_importance_view(request)

    context = {
        'total_users': total_users,
        'total_articles': total_articles,
        'total_diagnoses': total_diagnoses,
        'user_labels': user_labels,
        'user_counts': user_counts,
        'diagnosis_labels': diagnosis_labels,
        'diagnosis_counts': diagnosis_counts,
        'gender_labels': gender_labels,
        'gender_counts': gender_counts,
        'age_labels': age_labels,
        'age_risk_counts': age_risk_counts,
        'age_no_risk_counts': age_no_risk_counts,
        'feature_image_base64': feature_image_base64,
        'uploaded_at': uploaded_at,
    }

    return render(request, 'admin/dashboard_adminn.html', context)


from django.utils.dateparse import parse_datetime

from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_datetime
from django.contrib.auth.decorators import login_required
from .models import CustomUser, HealthRecord1, Diagnosis_N
from datetime import datetime
from django.db.models import Q
from datetime import timedelta
from django.utils.dateparse import parse_date


from datetime import datetime


@login_required
def dashboard_medical_staff(request):
    # จำนวนสมาชิกทั้งหมด
    total_users = CustomUser.objects.count()

    # จำนวนบทความสุขภาพทั้งหมด
    total_articles = Articles.objects.count()

    # จำนวนการวินิจฉัยทั้งหมด
    total_diagnoses = Diagnosis_N.objects.count()

    recent_diagnoses = Diagnosis_N.objects.all().order_by('-created_at')[:5]  # วินิจฉัยล่าสุด 5 รายการ
    recent_articles = Articles.objects.all().order_by('-created_at')[:5]  # บทความล่าสุด 5 รายการ

    # ดึงผลวินิจฉัยเพื่อแสดงเป็นกราฟโดนัท
    diagnosis_data = Diagnosis_N.objects.values('prediction').annotate(count=Count('id'))
    diagnosis_labels = [item['prediction'] for item in diagnosis_data]
    diagnosis_counts = [item['count'] for item in diagnosis_data]

    # แยกจำนวนเสี่ยง และไม่เสี่ยง
    risk_count_risk = 0
    risk_count_no_risk = 0

    for item in diagnosis_data:
        if item['prediction'] in ['Risk', 'เสี่ยง']:
            risk_count_risk += item['count']
        elif item['prediction'] in ['No Risk', 'ไม่เสี่ยง']:
            risk_count_no_risk += item['count']

    diagnoses = Diagnosis_N.objects.all().order_by('-created_at')

    categories = {
        "children": 0,
        "Adolescents": 1,
        "Young Adult": 2,
        "Middle-aged Adult": 3,
        "Older Adult": 4
    }

    def get_age_category(value):
        # ถ้าเป็น string เช่น "Children", "Adolescents" ให้แปลงเป็นหมายเลข
        if isinstance(value, str):
            return categories.get(value, 0)  # ถ้าไม่พบหมวดหมู่ ให้ค่าเริ่มต้นเป็น 0

        # ถ้าเป็นตัวเลข 0-4 (จัดกลุ่มไว้แล้ว) ให้คืนค่าเดิม
        if isinstance(value, int) and 0 <= value <= 4:
            return value

        # ถ้าเป็นตัวเลข (อายุจริง) ให้แปลงเป็นกลุ่ม
        try:
            v = int(value)
        except ValueError:  # ถ้าไม่สามารถแปลงเป็นตัวเลขได้ ให้คืนค่า 0
            return 0

        # กรองตามช่วงอายุ
        if v <= 12:
            return 0  # Children
        elif 13 <= v <= 19:
            return 1  # Adolescents
        elif 20 <= v <= 39:
            return 2  # Young Adult
        elif 40 <= v <= 59:
            return 3  # Middle-aged Adult
        else:
            return 4  # Older Adult

    # ดึงข้อมูลผลวินิจฉัยแยกตามช่วงอายุ
    age_risk_data = Diagnosis_N.objects.values('age', 'prediction')
    age_risk_dict = {group: {"เสี่ยง": 0, "ไม่เสี่ยง": 0} for group in categories.keys()}

    for item in age_risk_data:
        age = item["age"]  # ค่าของอายุจริงหรือกลุ่มที่จัดไว้
        prediction = item["prediction"]

        # แปลงอายุเป็นหมวดหมู่ (รองรับค่าที่เป็นตัวเลขกลุ่มแล้ว)
        age_category = get_age_category(age)

        # หาหมวดหมู่ที่ตรงกับค่า age_category
        category_label = list(categories.keys())[age_category]  # แปลงหมายเลขกลับเป็นชื่อหมวดหมู่

        if category_label:
            if prediction in ["เสี่ยง", "Risk"]:
                age_risk_dict[category_label]["เสี่ยง"] += 1
            else:
                age_risk_dict[category_label]["ไม่เสี่ยง"] += 1

    # เตรียมข้อมูลสำหรับกราฟ
    age_labels = list(age_risk_dict.keys())
    age_risk_counts = [age_risk_dict[group]["เสี่ยง"] for group in age_labels]
    age_no_risk_counts = [age_risk_dict[group]["ไม่เสี่ยง"] for group in age_labels]

    feature_image_base64, uploaded_at = feature_importance_view(request)

    return render(request, 'doctor/home_dc.html', {
        'total_users': total_users,
        'total_articles': total_articles,
        'total_diagnoses': total_diagnoses,
        'recent_diagnoses': recent_diagnoses,
        'recent_articles': recent_articles,
        'risk_count_risk': risk_count_risk,
        'risk_count_no_risk': risk_count_no_risk,
        'diagnosis_labels': diagnosis_labels,
        'diagnosis_counts': diagnosis_counts,
        'diagnoses': diagnoses,
        'age_labels': age_labels,
        'age_risk_counts': age_risk_counts,
        'age_no_risk_counts': age_no_risk_counts,
        'feature_image_base64': feature_image_base64,
        'uploaded_at': uploaded_at,
    })

@login_required
def dashboard_user(request):
    user = CustomUser.objects.get(username=request.user.username)
    health_record1 = HealthRecord1.objects.filter(user=request.user).order_by('-date_recorded').first()
    articles = Articles.objects.all().order_by('-created_at')[:6]

    # ✅ ดึงค่าประวัติ BMI ของผู้ใช้จาก Diagnosis_N (เรียงตามวันที่)
    bmi_records = HealthRecord1.objects.filter(user=request.user).order_by("-date_recorded").values_list("bmi", "date_recorded")

    # ✅ แปลงเป็น list สำหรับส่งไปยัง template
    bmi_values = [record[0] for record in bmi_records]  # ค่าของ BMI
    bmi_dates = [record[1].strftime("%Y-%m-%d") for record in bmi_records]  # วันที่ (แปลงเป็น string)

    # ดึงค่าความดันโลหิตทั้งหมด
    blood_pressure_records = HealthRecord1.objects.filter(user=request.user).order_by('date_recorded')

    # แปลงข้อมูลเป็น JSON สำหรับ JavaScript
    blood_pressure_values = [record.blood_pressure for record in blood_pressure_records]
    blood_pressure_dates = [record.date_recorded.strftime("%Y-%m-%d") for record in blood_pressure_records]

    # ดึงข้อมูลน้ำตาลก่อนอาหารและหลังอาหาร
    blood_sugar_records = HealthRecord1.objects.filter(user=request.user).order_by('date_recorded')

    fasting_blood_sugar_values = [record.fasting_blood_sugar for record in blood_sugar_records]
    postprandial_blood_sugar_values = [record.postprandial_blood_sugar for record in blood_sugar_records]
    record_dates = [record.date_recorded.strftime('%Y-%m-%d') for record in blood_sugar_records]

    blood_fats_records = HealthRecord1.objects.filter(user=request.user).order_by("-date_recorded")

    triglycerides_values = [record.triglycerides for record in blood_fats_records]
    cholesterol_values = [record.cholesterol for record in blood_fats_records]
    hdl_values = [record.hdl for record in blood_fats_records]
    ldl_values = [record.ldl for record in blood_fats_records]
    record_dates = [record.date_recorded.strftime('%Y-%m-%d') for record in blood_fats_records]


    # มาตรฐานที่แนะนำ (ค่าปกติ)
    recommended_values = {
        'cholesterol': 200,  # ค่ามาตรฐาน Cholesterol
        'triglycerides': 150,  # ค่ามาตรฐาน Triglycerides
        'hdl': 40,  # ค่ามาตรฐาน HDL
        'ldl': 100,  # ค่ามาตรฐาน LDL
    }

    return render(request, 'dashboard_user.html', {
        'health_record1': health_record1,
        'articles': articles,
        'bmi_values': bmi_values,
        'bmi_dates': bmi_dates,
        'blood_pressure_values': blood_pressure_values,
        'blood_pressure_dates': blood_pressure_dates,
        'fasting_blood_sugar_values': fasting_blood_sugar_values,
        'postprandial_blood_sugar_values': postprandial_blood_sugar_values,
        'record_dates': record_dates,
        'cholesterol_values': cholesterol_values,
        'triglycerides_values': triglycerides_values,
        'hdl_values': hdl_values,
        'ldl_values': ldl_values,
        'recommended_values': recommended_values,
    })



def risk_info(request):
    # ดึงข้อมูลการวินิจฉัยที่เป็น "เสี่ยง"
    risk_data = Diagnosis_N.objects.filter(prediction__in=["เสี่ยง", "Risk"])

    paginator = Paginator(risk_data, 5)  # Show 5 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'risk_info.html', {'data': page_obj})


def no_risk_info(request):
    # ดึงข้อมูลการวินิจฉัยที่เป็น "ไม่เสี่ยง"
    no_risk_data = Diagnosis_N.objects.filter(prediction__in=["ไม่เสี่ยง", "No Risk"])

    paginator = Paginator(no_risk_data, 5)  # Show 5 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'no_risk_info.html', {'data': page_obj})


def get_age_category(value):
    categories = {
        "Children": 0,
        "Adolescents": 1,
        "Young Adult": 2,
        "Middle-aged Adult": 3,
        "Older Adult": 4
    }

    # ถ้าเป็น string เช่น "Children", "Adolescents" ให้แปลงเป็นหมายเลข
    if isinstance(value, str):
        return categories.get(value, 0)  # ถ้าไม่พบหมวดหมู่ ให้ค่าเริ่มต้นเป็น 0

    # ถ้าเป็นตัวเลข 0-4 (จัดกลุ่มไว้แล้ว) ให้คืนค่าเดิม
    if isinstance(value, int) and 0 <= value <= 4:
        return value

    # ถ้าเป็นตัวเลข (อายุจริง) ให้แปลงเป็นกลุ่ม
    try:
        v = int(value)
    except ValueError:  # ถ้าไม่สามารถแปลงเป็นตัวเลขได้ ให้คืนค่า 0
        return 0

    # กรองตามช่วงอายุ
    if v <= 12:
        return 0  # Children
    elif 13 <= v <= 19:
        return 1  # Adolescents
    elif 20 <= v <= 39:
        return 2  # Young Adult
    elif 40 <= v <= 59:
        return 3  # Middle-aged Adult
    else:
        return 4  # Older Adult


def age_category_risk_info(request, age_category, risk_category):
    # กำหนดช่วงอายุ
    age_ranges = {
        "เด็ก (children) / 0-12 ปี": (0, 12),  # เด็ก
        "adolescents": (13, 19),  # วัยรุ่น
        "young_adults": (20, 39),  # วัยหนุ่มสาว
        "middle_aged_adults": (40, 59),  # วัยกลางคน
        "older_adults": (60, 100),  # วัยชรา
    }

    # กรองข้อมูลตามช่วงอายุ
    age_range = age_ranges.get(age_category, (0, 100))  # ค่าเริ่มต้นคือ 0-100 หากไม่พบช่วงอายุที่กำหนด

    # กรองข้อมูลตามประเภทเสี่ยงหรือไม่เสี่ยง
    prediction_filter = 'เสี่ยง' if risk_category == 'เสี่ยง' else 'ไม่เสี่ยง'

    # ดึงข้อมูลจากฐานข้อมูลที่กรองตามช่วงอายุและประเภทเสี่ยง
    data = Diagnosis_N.objects.filter(age__range=age_range, prediction=prediction_filter)

    paginator = Paginator(data, 5)  # Show 5 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'age_risk_info.html',
                  {'data': page_obj, 'age_category': age_category, 'risk_category': risk_category})


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')  # เปลี่ยนเส้นทางกลับมาที่หน้าโปรไฟล์
    else:
        form = ProfileUpdateForm(instance=user)

    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'profile.html', context)

@login_required
def articles_view(request):
    articles = Articles.objects.all()
    return render(request, 'articles.html', {
        'articles': articles,
        'is_admin': request.user.is_staff,
        'is_medical_staff': request.user.groups.filter(name='Medical Officer').exists()
    })

def view_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    return render(request, 'view_article.html', {'article': article })

def articles_list(request):
    articles = Articles.objects.all()
    return render(request, 'articles_list.html', {
        'articles': articles,
        'is_admin': request.user.is_staff,
        'medical_staff': request.user.groups.filter(name='Medical Officer').exists()
    })

@login_required
def add_article(request):
    if request.method == 'POST':
        form = ArticlesForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)  # สร้าง object แต่ยังไม่บันทึกในฐานข้อมูล
            article.author = request.user      # กำหนดผู้เขียนเป็นผู้ใช้ที่ล็อกอินอยู่
            article.save()                     # บันทึกบทความในฐานข้อมูล
            return redirect('articles')        # กลับไปยังหน้ารายการบทความ
    else:
        form = ArticlesForm()
    return render(request, 'add_article.html', {'form': form})

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)

    if request.method == 'POST':
        form = ArticlesForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            return redirect('articles_admin')
    else:
        form = ArticlesForm(instance=article)

    return render(request, 'edit_article.html', {'form': form, 'article': article})

# Delete an article (only admin or medical staff)
@login_required
@user_passes_test(is_admin_or_medical_staff)
def delete_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    if request.method == 'POST':
        article.delete()
        return redirect('articles_admin')
    return render(request, 'delete_article.html', {'article': article})


# ตรวจสอบว่าเป็นแอดมิน
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = CustomUser.objects.all()
    return render(request, 'manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = CustomUserForm(instance=user)
    return render(request, 'edit_user.html', {'form': form})

def is_admin_or_medical_staff1(user):
    return user.is_authenticated and (user.role == "admin" or user.role == "medical_staff")

@login_required
@user_passes_test(is_admin_or_medical_staff1)
def view_all_users(request):
    users = CustomUser.objects.all()  # ดึงสมาชิกทั้งหมด
    return render(request, 'view_all_users.html', {'users': users})


def load_model():
    with open('diabetes/diabetes/models/random_forest_model.pkl', 'rb') as file:
        model = pickle.load(file)
    return model

from django.utils import timezone

@login_required
def health_record_view1(request):
    # ดึงข้อมูลล่าสุดของผู้ใช้
    latest_record = HealthRecord1.objects.filter(user=request.user).order_by('-date_recorded').first()

    if request.method == "POST":
        form = HealthRecord1Form(request.POST)
        if form.is_valid():
            new_record = form.save(commit=False)
            new_record.user = request.user
            new_record.last_visit_date = timezone.now()

            # ตรวจสอบว่าเป็นการเพิ่มข้อมูลใหม่หรืออัปเดตข้อมูลเก่า
            # หากผู้ใช้กรอก 'last_visit_date' ให้ใช้ค่าจากฟอร์ม
            if 'last_visit_date' in form.cleaned_data:
                new_record.last_visit_date = form.cleaned_data['last_visit_date']

            # คำนวณ BMI ถ้าน้ำหนักและส่วนสูงมีค่า
            weight = new_record.weight
            height = new_record.height
            if weight and height:  # ตรวจสอบว่าน้ำหนักและส่วนสูงมีค่า
                new_record.bmi = weight / ((height / 100) ** 2)

            new_record.save()
            return redirect('success1')
    else:
        # ตรวจสอบและส่งค่า BMI ไปใน initial
        form = HealthRecord1Form(initial={
            'blood_pressure': latest_record.blood_pressure if latest_record else '',
            'weight': latest_record.weight if latest_record else '',
            'height': latest_record.height if latest_record else '',
            'bmi': latest_record.bmi if latest_record and latest_record.bmi is not None else '',  # กำหนดค่า BMI
            'insulin': latest_record.insulin if latest_record else '',
            'fasting_blood_sugar': latest_record.fasting_blood_sugar if latest_record else '',
            'postprandial_blood_sugar': latest_record.postprandial_blood_sugar if latest_record else '',
            'hba1c': latest_record.hba1c if latest_record else '',
            'bun': latest_record.bun if latest_record else '',
            'cr': latest_record.cr if latest_record else '',
            'egfr': latest_record.egfr if latest_record else '',
            'triglycerides': latest_record.triglycerides if latest_record else '',
            'cholesterol': latest_record.cholesterol if latest_record else '',
            'hdl': latest_record.hdl if latest_record else '',
            'ldl': latest_record.ldl if latest_record else '',
            'albumin_in_urine': latest_record.albumin_in_urine if latest_record else '',
            'ekg': latest_record.ekg if latest_record else '',
            'chest_x_ray': latest_record.chest_x_ray if latest_record else '',
            'diabetic_retinopathy_screening': latest_record.diabetic_retinopathy_screening if latest_record else '',
            'diabetic_foot_screening': latest_record.diabetic_foot_screening if latest_record else '',
            'last_visit_date': latest_record.last_visit_date if latest_record else None,  # ค่าล่าสุดจากฐานข้อมูล
        })

    records = HealthRecord1.objects.filter(user=request.user).order_by('-id')
    total_records = records.count()

    return render(request, 'health_records/form1h.html', {
        'form': form,
        'records': records,
        'total_records': total_records,
    })




def success_page1(request):
    return render(request, 'health_records/success1.html')


def history_view1(request):
    records = HealthRecord1.objects.filter(user=request.user).order_by("-date_recorded")
    return render(request, "health_records/history.html", {"records": records})

def health_recordview(request):
    record = HealthRecord1.objects.filter(user=request.user).order_by('-date_recorded').first()  # ดึงข้อมูลของผู้ใช้ปัจจุบัน
    return render(request, 'health_recordview.html', {'record': record})
def categorize_bmi_value(bmi):
    if bmi < 18.5:
        return 0  # น้ำหนักต่ำกว่าเกณฑ์
    elif 18.5 <= bmi < 25:
        return 1  # ปกติ
    elif 25 <= bmi < 30:
        return 2  # น้ำหนักเกิน
    elif 30 <= bmi < 35:
        return 3  # โรคอ้วนระดับ 1
    elif 35 <= bmi < 40:
        return 4  # โรคอ้วนระดับ 2
    else:
        return 5  # โรคอ้วนระดับ 3

def categorize_glucose_value(glucose):
    if glucose < 70:
        return 0  # น้ำตาลต่ำ
    elif 70 <= glucose < 100:
        return 1  # ปกติ
    elif 100 <= glucose < 125:
        return 2  # ระดับก่อนเบาหวาน
    else:
        return 3  # มีความเสี่ยงเบาหวาน

def categorize_blood_pressure_value(bp):
    if bp < 90:
        return 0  # ความดันต่ำ
    elif 90 <= bp < 120:
        return 1  # ปกติ
    elif 120 <= bp < 130:
        return 2  # มีความเสี่ยง
    elif 130 <= bp < 140:
        return 3  # ความดันโลหิตระดับที่ 1
    elif 140 <= bp < 180:
        return 4  # ความดันโลหิตระดับที่ 2
    else:
        return 5  # ค่าระดับวิกฤต

def categorize_skin_thickness_value(st):
    if st < 10:
        return 0  # ต่ำ
    elif 10 <= st < 20:
        return 1  # ปกติ
    elif 20 <= st < 30:
        return 2  # สะสมไขมันมาก
    else:
        return 3  # เสี่ยงต่อโรคอ้วน

def categorize_pregnancies_value(p):
    if p == 0:
        return 0  # ความเสี่ยงต่ำ
    elif 1 <= p <= 2:
        return 1  # ความเสี่ยงปานกลาง
    else:
        return 2  # ความเสี่ยงสูง

def categorize_age_value(age):
    if age < 18:
        return 0  # เด็ก
    elif 18 <= age < 30:
        return 1  # วัยรุ่น
    elif 30 <= age < 45:
        return 2  # วัยหนุ่มสาว
    elif 45 <= age < 60:
        return 3  # วัยกลางคน
    else:
        return 4  # วัยชรา

def categorize_insulin_value(insulin):
    if insulin < 5:
        return 0  # ไม่มีการผลิตอินซูลิน
    elif 5 <= insulin < 15:
        return 1  # ปกติ
    elif 15 <= insulin < 25:
        return 2  # สูง
    else:
        return 3  # สูงมาก

def categorize_dpf_value(dpf):
    if dpf < 0.3:
        return 0  # ความเสี่ยงต่ำ
    elif 0.3 <= dpf < 0.5:
        return 1  # ความเสี่ยงปานกลาง
    elif 0.5 <= dpf < 0.7:
        return 2  # ความเสี่ยงสูง
    else:
        return 3  # ความเสี่ยงสูงมาก


# โหลดโมเดล

with open('diabetes/diabetes/models/random_forest_model.pkl', 'rb') as file:
    rf_model = pickle.load(file)

with open('diabetes/diabetes/models/svm_model_m.pkl', 'rb') as file:
    svm_model = pickle.load(file)

with open('diabetes/diabetes/models/decision_tree_model.pkl', 'rb') as file:
    dt_model = pickle.load(file)

with open('diabetes/diabetes/models/logistic_regression_model.pkl', 'rb') as file:
    lr_model = pickle.load(file)

with open('diabetes/diabetes/models/scaler_m.pkl', 'rb') as file:
    scaler = pickle.load(file)

def upload_modelML(request):
    if request.method == 'POST':
        form = ModelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the new model with the current date and time
            form.save()
            return redirect('success_page')
    else:
        form = ModelUploadForm()
    return render(request, 'upload_model/upload_model.html', {'form': form})

def success_page(request):
    return render(request, 'upload_model/success_page.html')  # Success page after upload

# Function to load the latest model
def load_latest_model():
    try:
        # Get the most recent model from the database
        latest_model = MLModel.objects.latest('uploaded_at')  # Order by upload date
        model_file_path = latest_model.model_file.path  # Get the path to the uploaded model
        with open(model_file_path, 'rb') as model_file:
            model = pickle.load(model_file)  # Load the saved model with pickle
        return model, latest_model.uploaded_at
    except MLModel.DoesNotExist:
        return None, None

def diagnose_form(request):
    return render(request, 'diagnose_diabetes_t.html')


def diagnose_diabetes(request):
    if request.method == 'POST':
        try:
            pregnancies = int(request.POST.get('Pregnancies') or 0)
            glucose = int(request.POST.get('Glucose') or 0)
            blood_pressure = int(request.POST.get('BloodPressure') or 0)
            skin_thickness = int(request.POST.get('SkinThickness') or 0)
            insulin = int(request.POST.get('Insulin') or 0)
            bmi = float(request.POST.get('BMI') or 0)
            dpf = float(request.POST.get('DiabetesPedigreeFunction') or 0)
            age = int(request.POST.get('Age') or 0)

            # แปลงค่าที่กรอกมาเป็นหมวดหมู่ที่ 0, 1, 2, 3
            bmi_category = categorize_bmi_value(bmi)
            glucose_category = categorize_glucose_value(glucose)
            blood_pressure_category = categorize_blood_pressure_value(blood_pressure)
            skin_thickness_category = categorize_skin_thickness_value(skin_thickness)
            insulin_category = categorize_insulin_value(insulin)
            dpf_category = categorize_dpf_value(dpf)
            age_category = categorize_age_value(age)
            pregnancies_category = categorize_pregnancies_value(pregnancies)

            # เตรียมข้อมูล input สำหรับโมเดล
            input_data = [[pregnancies_category, glucose_category, blood_pressure_category,
                           skin_thickness_category, insulin_category, bmi_category,
                           dpf_category, age_category]]

            # โหลดโมเดลล่าสุด
            model, uploaded_at = load_latest_model()

            if not model:
                return render(request, 'diagnose_diabetes_t.html', {'error': "ยังไม่มีโมเดลที่อัปโหลด กรุณาอัปโหลดโมเดลก่อน."})

            # ทำนายผล
            rf_pred = model.predict(input_data)
            predictions = 'เสี่ยง' if rf_pred[0] == 1 else 'ไม่เสี่ยง'

            # สร้าง dictionary สำหรับแสดงค่าที่แปลงแล้ว
            categorized_data = {
                'Pregnancies': pregnancies_category,
                'Glucose': glucose_category,
                'Blood Pressure': blood_pressure_category,
                'Skin Thickness': skin_thickness_category,
                'Insulin': insulin_category,
                'BMI': bmi_category,
                'Diabetes Pedigree Function': dpf_category,
                'Age': age_category
            }

            # เพิ่มข้อมูลที่กรอกก่อนแปลง
            input_data_before_categorization = {
                'Pregnancies': pregnancies,
                'Glucose': glucose,
                'Blood Pressure': blood_pressure,
                'Skin Thickness': skin_thickness,
                'Insulin': insulin,
                'BMI': bmi,
                'Diabetes_Pedigree_Function': dpf,
                'Age': age
            }

            # Save the diagnosis result to the database
            diagnosis = Diagnosis_N(
                user=request.user,  # Save the user (if applicable)
                bmi=bmi,
                blood_pressure=blood_pressure,
                pregnancies=pregnancies,
                glucose=glucose,
                skin_thickness=skin_thickness,
                insulin=insulin,
                diabetes_pedigree_function=dpf,
                age=age,
                prediction=predictions
            )
            diagnosis.save()

            return render(request, 'result_t.html', {
                'results': predictions,
                'categorized_data': categorized_data,  # แสดงค่าที่แปลงแล้ว
                'input_data_before_categorization': input_data_before_categorization,  # แสดงค่าก่อนแปลง
                'uploaded_at': uploaded_at  # แสดงเวลาที่อัปโหลดโมเดล
            })

        except ValueError as e:
            return render(request, 'diagnose_diabetes_t.html', {'error': f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"})

    return render(request, 'diagnose_diabetes_t.html')

def diagnose_form_doctor(request):
    return render(request, 'diagnose_diabetes_doctor.html')


def diagnose_diabetes_doctor(request):
    if request.method == 'POST':
        try:
            pregnancies = int(request.POST.get('Pregnancies') or 0)
            glucose = int(request.POST.get('Glucose') or 0)
            blood_pressure = int(request.POST.get('BloodPressure') or 0)
            skin_thickness = int(request.POST.get('SkinThickness') or 0)
            insulin = int(request.POST.get('Insulin') or 0)
            bmi = float(request.POST.get('BMI') or 0)
            dpf = float(request.POST.get('DiabetesPedigreeFunction') or 0)
            age = int(request.POST.get('Age') or 0)

            # แปลงค่าที่กรอกมาเป็นหมวดหมู่ที่ 0, 1, 2, 3
            bmi_category = categorize_bmi_value(bmi)
            glucose_category = categorize_glucose_value(glucose)
            blood_pressure_category = categorize_blood_pressure_value(blood_pressure)
            skin_thickness_category = categorize_skin_thickness_value(skin_thickness)
            insulin_category = categorize_insulin_value(insulin)
            dpf_category = categorize_dpf_value(dpf)
            age_category = categorize_age_value(age)
            pregnancies_category = categorize_pregnancies_value(pregnancies)

            # เตรียมข้อมูล input สำหรับโมเดล
            input_data = [[pregnancies_category, glucose_category, blood_pressure_category,
                           skin_thickness_category, insulin_category, bmi_category,
                           dpf_category, age_category]]

            # โหลดโมเดลล่าสุด
            model, uploaded_at = load_latest_model()

            if not model:
                return render(request, 'diagnose_diabetes_doctor.html', {'error': "ยังไม่มีโมเดลที่อัปโหลด กรุณาอัปโหลดโมเดลก่อน."})

            # ทำนายผล
            rf_pred = model.predict(input_data)
            predictions = 'เสี่ยง' if rf_pred[0] == 1 else 'ไม่เสี่ยง'

            # สร้าง dictionary สำหรับแสดงค่าที่แปลงแล้ว
            categorized_data = {
                'Pregnancies': pregnancies_category,
                'Glucose': glucose_category,
                'Blood Pressure': blood_pressure_category,
                'Skin Thickness': skin_thickness_category,
                'Insulin': insulin_category,
                'BMI': bmi_category,
                'Diabetes Pedigree Function': dpf_category,
                'Age': age_category
            }

            # เพิ่มข้อมูลที่กรอกก่อนแปลง
            input_data_before_categorization = {
                'Pregnancies': pregnancies,
                'Glucose': glucose,
                'Blood Pressure': blood_pressure,
                'Skin Thickness': skin_thickness,
                'Insulin': insulin,
                'BMI': bmi,
                'Diabetes_Pedigree_Function': dpf,
                'Age': age
            }

            # Save the diagnosis result to the database
            diagnosis = Diagnosis_N(
                user=request.user,  # Save the user (if applicable)
                bmi=bmi,
                blood_pressure=blood_pressure,
                pregnancies=pregnancies,
                glucose=glucose,
                skin_thickness=skin_thickness,
                insulin=insulin,
                diabetes_pedigree_function=dpf,
                age=age,
                prediction=predictions
            )
            diagnosis.save()

            return render(request, 'result_doctor.html', {
                'results': predictions,
                'categorized_data': categorized_data,  # แสดงค่าที่แปลงแล้ว
                'input_data_before_categorization': input_data_before_categorization,  # แสดงค่าก่อนแปลง
                'uploaded_at': uploaded_at  # แสดงเวลาที่อัปโหลดโมเดล
            })

        except ValueError as e:
            return render(request, 'diagnose_diabetes_doctor.html', {'error': f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"})

    return render(request, 'diagnose_diabetes_doctor.html')


from django.core.paginator import Paginator
from django.shortcuts import render
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.core.files.storage import FileSystemStorage
import pickle
import numpy as np

# Categorization functions with suffix '1' and type conversion
def categorize_bmi1(value):
    categories = {
        "Underweight": 0,
        "Normal": 1,
        "Overweight": 2,
        "Obesity class 1": 3,
        "Obesity class 2": 4,
        "Obesity class 3": 5
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = float(value)
    except:
        return 0
    if v < 18.5: return 0
    elif 18.5 <= v <= 24.9: return 1
    elif 25.0 <= v <= 29.9: return 2
    elif 30.0 <= v <= 34.9: return 3
    elif 35.0 <= v <= 39.9: return 4
    else: return 5


def categorize_glucose1(value):
    categories = {
        "Hypoglycemia": 0,
        "Normal": 1,
        "Prediabetes": 2,
        "Diabetes": 3
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = float(value)
    except:
        return 0
    if v < 70: return 0
    elif 70 <= v <= 99: return 1
    elif 100 <= v <= 125: return 2
    else: return 3


def categorize_blood_pressure1(value):
    categories = {
        "Low": 0,
        "Normal": 1,
        "Elevated": 2,
        "Hypertension Stage 1": 3,
        "Hypertension Stage 2": 4,
        "Hypertensive Crisis": 5
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = float(value)
    except:
        return 0
    if v < 60: return 0
    elif 60 <= v <= 79: return 1
    elif 80 <= v <= 89: return 2
    elif 90 <= v <= 99: return 3
    elif 100 <= v <= 109: return 4
    else: return 5


def categorize_skin_thickness1(value):
    categories = {
        "Low": 0,
        "Normal": 1,
        "High Fat Accumulation": 2,
        "At Risk of Obesity": 3
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = float(value)
    except:
        return 0
    if v < 10: return 0
    elif 10 <= v <= 20: return 1
    elif 20 <= v <= 30: return 2
    else: return 3


def categorize_pregnancies1(value):
    categories = {
        "Low Risk": 0,
        "Moderate Risk": 1,
        "High Risk": 2
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = int(value)
    except:
        return 0
    if v <= 1: return 0
    elif 2 <= v <= 3: return 1
    else: return 2


def categorize_age1(value):
    categories = {
        "Children": 0,
        "Adolescents": 1,
        "Young Adult": 2,
        "Middle-aged Adult": 3,
        "Older Adult": 4
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = int(value)
    except:
        return 0
    if v <= 12: return 0
    elif 13 <= v <= 19: return 1
    elif 20 <= v <= 39: return 2
    elif 40 <= v <= 59: return 3
    else: return 4


def categorize_insulin1(value):
    categories = {
        "No Insulin Produced": 0,
        "Normal": 1,
        "Elevated": 2,
        "High": 3
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = float(value)
    except:
        return 0
    if v < 30: return 0
    elif 30 <= v <= 60: return 1
    elif 60 <= v <= 120: return 2
    else: return 3


def categorize_dpf1(value):
    categories = {
        "Low Risk": 0,
        "Moderate Risk": 1,
        "High Risk": 2,
        "Very High Risk": 3
    }
    if isinstance(value, str):
        return categories.get(value, 0)
    try:
        v = float(value)
    except:
        return 0
    if v < 0.2: return 0
    elif 0.2 <= v <= 0.5: return 1
    elif 0.5 <= v <= 1.0: return 2
    else: return 3


def preprocess_data1(df):
    df['BMI'] = df['BMI'].apply(categorize_bmi1)
    df['Glucose'] = df['Glucose'].apply(categorize_glucose1)
    df['BloodPressure'] = df['BloodPressure'].apply(categorize_blood_pressure1)
    df['SkinThickness'] = df['SkinThickness'].apply(categorize_skin_thickness1)
    df['Pregnancies'] = df['Pregnancies'].apply(categorize_pregnancies1)
    df['Age'] = df['Age'].apply(categorize_age1)
    df['Insulin'] = df['Insulin'].apply(categorize_insulin1)
    df['DiabetesPedigreeFunction'] = df['DiabetesPedigreeFunction'].apply(categorize_dpf1)

    return df


def load_data1(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        return None
    return df


def predict_risk1(df):
    # โหลดโมเดลล่าสุดจากฐานข้อมูล
    model, uploaded_at = load_latest_model()

    if model is None:
        return None  # ถ้าไม่มีโมเดล ให้คืนค่า None

    # ตรวจสอบว่า df มีเฉพาะฟีเจอร์ที่ต้องใช้
    required_features = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
                         'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

    if not all(feature in df.columns for feature in required_features):
        return None  # ถ้าข้อมูลไม่ครบ ก็คืนค่า None

    df = df[required_features]  # เลือกเฉพาะฟีเจอร์ที่ต้องการ

    # ทำการพยากรณ์
    df['Predicted_Outcome'] = model.predict(df)

    return df

def upload_file_test(request):
    if request.method == 'POST' and request.FILES.get('file'):
        # ลบข้อมูลใน session ก่อนการอัปโหลดใหม่
        if not request.user.is_authenticated:
            return redirect('/login/')

        # อัปโหลดไฟล์ใหม่
        file1 = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file1.name, file1)
        file_path = fs.path(filename)

        # โหลดข้อมูลจากไฟล์
        df = load_data1(file_path)
        if df is None:
            return render(request, 'upload11.html', {"error": "Invalid file format. Please upload CSV or XLSX."})

        # เก็บข้อมูลใน session
        request.session['file_path'] = file_path
        request.session['df'] = df.to_dict(orient='records')

        # คำนวณข้อมูลต่างๆ เช่น จำนวนผู้ป่วย
        total_count = len(df)

        # 🟢 แยกข้อมูลส่วนตัวออกจากฟีเจอร์ที่ใช้วินิจฉัย
        personal_info = df[['Name', 'Address', 'Phone', 'Gender']]
        diagnostic_features = df.drop(columns=['Name', 'Address', 'Phone', 'Gender'], errors='ignore')
        diagnostic_features = diagnostic_features.drop(columns=['Outcome'], errors='ignore')

        # 🟢 ค้นหาตามเพศและที่อยู่ (ถ้ามีการกรอก)
        gender_filter = request.GET.get('gender', '')
        address_filter = request.GET.get('address', '')

        # กรองข้อมูลตามเงื่อนไข
        if gender_filter:
            personal_info = personal_info[personal_info['Gender'].str.contains(gender_filter, case=False, na=False)]

        if address_filter:
            personal_info = personal_info[personal_info['Address'].str.contains(address_filter, case=False, na=False)]

        # 🟢 โหลดโมเดลล่าสุด
        model, model_date = load_latest_model()
        if model is None:
            return render(request, 'upload11.html', {"error": "No trained model available."})

        # 🟢 ประมวลผลฟีเจอร์
        diagnostic_features = preprocess_data1(diagnostic_features)

        # 🟢 ทำนายผล
        predictions = model.predict(diagnostic_features)
        diagnostic_features['Predicted_Outcome'] = predictions

        # 🟢 คำนวณจำนวนผู้ป่วยที่มีความเสี่ยงและไม่มีความเสี่ยง
        risk_count = (predictions == 1).sum()
        no_risk_count = (predictions == 0).sum()

        # แยกอายุของกลุ่มเสี่ยงและไม่เสี่ยง
        age_risk_counts = diagnostic_features[diagnostic_features['Predicted_Outcome'] == 1][
            'Age'].value_counts().sort_index()
        age_no_risk_counts = diagnostic_features[diagnostic_features['Predicted_Outcome'] == 0][
            'Age'].value_counts().sort_index()

        # สร้างกลุ่มอายุทั้งหมด (0-4) และเติมค่า 0 ถ้ากลุ่มไหนไม่มีข้อมูล
        all_age_groups = pd.Series(0, index=[0, 1, 2, 3, 4])
        age_risk_counts = all_age_groups.add(age_risk_counts, fill_value=0)
        age_no_risk_counts = all_age_groups.add(age_no_risk_counts, fill_value=0)

        # แปลงเป็น list สำหรับส่งไปยัง template
        age_risk_data = age_risk_counts.tolist()
        age_no_risk_data = age_no_risk_counts.tolist()

        bmi_data = diagnostic_features['BMI'].value_counts().sort_index().tolist()
        glucose_data = diagnostic_features['Glucose'].value_counts().sort_index().tolist()

        # 🟢 รวมข้อมูลส่วนบุคคล + ฟีเจอร์ + ผลลัพธ์กลับคืนมา
        df = pd.concat([personal_info, diagnostic_features], axis=1)

        # 🟢 แปลงเป็น List ของ Dictionary
        df_records = df.to_dict(orient='records')

        # เก็บข้อมูลใน session
        request.session['df_records'] = df_records
        request.session['total_count'] = total_count
        request.session['bmi_data'] = bmi_data
        request.session['glucose_data'] = glucose_data


        # 🟢 ตรวจสอบการเข้าสู่ระบบของผู้ใช้
        for index, row in df.iterrows():
            diagnosis = Diagnosis_N(
                user=request.user,  # Optionally save the user (if authenticated)
                bmi=row['BMI'],
                blood_pressure=row['BloodPressure'],
                pregnancies=row['Pregnancies'],
                glucose=row['Glucose'],
                skin_thickness=row['SkinThickness'],
                insulin=row['Insulin'],
                diabetes_pedigree_function=row['DiabetesPedigreeFunction'],
                age=row['Age'],
                prediction='เสี่ยง' if row['Predicted_Outcome'] == 1 else 'ไม่เสี่ยง',
                name=row['Name'],  # เก็บชื่อ
                address=row['Address'],  # เก็บที่อยู่
                phone=row['Phone'],  # เก็บเบอร์โทรศัพท์
                gender=row['Gender']  # เก็บเพศ
            )
            diagnosis.save()

        return redirect('analysis11')  # เปลี่ยนหน้าไปยังหน้าแสดงผลข้อมูล (analysis)

    return render(request, 'upload11.html')

def analyze_data(request):
    if request.GET.get('reset_filter') == '1':
        # ล้างค่าตัวกรองจาก session
        request.session.pop('gender_filter', None)
        request.session.pop('address_filter', None)
        return redirect('analysis11')  # โหลดข้อมูลใหม่ทั้งหมด
    # ดึงข้อมูลจาก session
    df_records = request.session.get('df_records', None)
    if not df_records:
        return redirect('upload11')  # ถ้าไม่มีข้อมูลให้กลับไปหน้าอัปโหลด

    # ค่าตัวกรองจาก GET (เก็บค่าตัวกรองเดิมไว้)
    gender_filter = request.GET.get('gender', '')
    address_filter = request.GET.get('address', '')

    # กรองข้อมูลตามเพศ
    if gender_filter:
        df_records = [record for record in df_records if record.get('Gender') == gender_filter]

    # กรองข้อมูลตามที่อยู่
    if address_filter:
        df_records = [record for record in df_records if address_filter.lower() in record.get('Address', '').lower()]

    # 🟢 เก็บค่าตัวกรองใน session เพื่อให้ยังคงอยู่ระหว่างเปลี่ยนหน้า
    request.session['gender_filter'] = gender_filter
    request.session['address_filter'] = address_filter

    df = pd.DataFrame(df_records)

    total_count = len(df)

    # 🟢 คำนวณจำนวนเสี่ยง/ไม่เสี่ยงใหม่ทุกครั้ง
    risk_count = df[df['Predicted_Outcome'] == 1].shape[0]
    no_risk_count = df[df['Predicted_Outcome'] == 0].shape[0]
    total_count = df.shape[0]

    # 🟢 คำนวณอายุของกลุ่มเสี่ยงและไม่เสี่ยง
    age_risk_counts = df[df['Predicted_Outcome'] == 1]['Age'].value_counts().sort_index()
    age_no_risk_counts = df[df['Predicted_Outcome'] == 0]['Age'].value_counts().sort_index()

    # 🟢 เติมค่า 0 ให้กับช่วงอายุที่ไม่มีข้อมูล
    all_age_groups = pd.Series(0, index=[0, 1, 2, 3, 4])  # แบ่งช่วงอายุเป็นกลุ่ม 0-4, 5-9, ...
    age_risk_counts = all_age_groups.add(age_risk_counts, fill_value=0).tolist()
    age_no_risk_counts = all_age_groups.add(age_no_risk_counts, fill_value=0).tolist()


    # ใช้ Paginator สำหรับแบ่งหน้า
    paginator = Paginator(df_records, 5)  # แสดง 5 รายการต่อหน้า
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # ดึงข้อมูลจาก session เพื่อให้แสดงผลกราฟได้

    model, model_date = load_latest_model()
    bmi_data = request.session.get('bmi_data', [])
    glucose_data = request.session.get('glucose_data', [])

    # ส่งค่าตัวกรองไปยัง template และใช้ urlencode เพื่อให้ค่าค้นหายังคงอยู่
    filter_params = f"gender={gender_filter}&address={address_filter}"

    return render(request, 'analysis11.html', {
        'df_records': df_records,
        'page_obj': page_obj,
        'gender_filter': gender_filter,
        'address_filter': address_filter,
        'risk_count': risk_count,
        'no_risk_count': no_risk_count,
        'total_count': total_count,
        'bmi_data': bmi_data,
        'glucose_data': glucose_data,
        'age_risk_data': age_risk_counts,
        'age_no_risk_data': age_no_risk_counts,
        'model_date': model_date,
        'filter_params': filter_params
    })

def health_record_list_admin(request):
    records = HealthRecord1.objects.all()
    return render(request, 'health_record_list_admin.html', {'records': records})


def health_record_detail_admin(request, record_id):
    record = get_object_or_404(HealthRecord1, id=record_id)
    return render(request, 'health_record_detail_admin.html', {'record': record})

def health_record_edit_admin(request, record_id):
    record = get_object_or_404(HealthRecord1, id=record_id)
    if request.method == 'POST':
        form = HealthRecord1Form(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('health_record_detail_admin', record_id=record.id)
    else:
        form = HealthRecord1Form(instance=record)
    return render(request, 'health_record_edit_admin.html', {'form': form, 'record': record})

def health_record_delete_admin(request, record_id):
    record = get_object_or_404(HealthRecord1, id=record_id)
    if request.method == 'POST':
        record.delete()
        return redirect('health_record_list_admin')
    return render(request, 'health_record_confirm_delete_admin.html', {'record': record})

#ดูข้อมูลสุขภาพของแพทย์
def health_record_for_doctor(request):
    records = HealthRecord1.objects.all()
    return render(request, 'health_record_for_doctor.html', {'records': records})

def health_record_detail_for_doctor(request, record_id):
    record = get_object_or_404(HealthRecord1, id=record_id)
    return render(request, 'health_record_detail_for_doctor.html', {'record': record})

#ดูผลการวินิจฉัย

def diagnosis_report_ad(request):
    diagnoses = Diagnosis_N.objects.all()

    paginator = Paginator(diagnoses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'diagnosis_report.html', {'page_obj': page_obj})

def diagnosis_report_dc(request):
    diagnoses = Diagnosis_N.objects.all()

    paginator = Paginator(diagnoses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'diagnosis_report_dc.html', {'page_obj': page_obj})

import requests
import logging


# ฟังก์ชันในการดึงพิกัดจากชื่ออำเภอ
def get_geocode(address):
    api_key = 'AIzaSyDszHFy6sy2klQOWoBm_sYC976sxsSb23w'  # ใส่ API key ของคุณที่นี่
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        'address': address,
        'key': api_key
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        # ดึงค่าพิกัดจากผลลัพธ์
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    return None, None


# ฟังก์ชันในการแสดงแผนที่
def show_map(request):
    # ดึงข้อมูลจากฐานข้อมูล
    diagnoses = Diagnosis_N.objects.all()
    marker_data = []

    for diagnosis in diagnoses:
        address = diagnosis.address  # ดึงชื่ออำเภอจากฐานข้อมูล
        lat, lng = get_geocode(address)  # ดึงพิกัดจากชื่ออำเภอ
        if lat and lng:
            # กำหนดสีของมาร์คเกอร์ตามค่าของ prediction
            marker_color = "red" if diagnosis.prediction == "เสี่ยง" else "green"

            # เพิ่มข้อมูลของบุคคลลงใน marker_data
            marker_data.append({
                'name': diagnosis.name,
                'phone': diagnosis.phone,
                'address': address,
                'lat': lat,
                'lng': lng,
                'risk': diagnosis.prediction,
                'marker_color': marker_color
            })

    return render(request, 'map.html', {'markers': marker_data})


def show_map_admin(request):
    # ดึงข้อมูลจากฐานข้อมูล
    diagnoses = Diagnosis_N.objects.all()
    marker_data = []

    for diagnosis in diagnoses:
        address = diagnosis.address  # ดึงชื่ออำเภอจากฐานข้อมูล
        lat, lng = get_geocode(address)  # ดึงพิกัดจากชื่ออำเภอ
        if lat and lng:
            # กำหนดสีของมาร์คเกอร์ตามค่าของ prediction
            marker_color = "red" if diagnosis.prediction == "เสี่ยง" else "green"

            # เพิ่มข้อมูลของบุคคลลงใน marker_data
            marker_data.append({
                'name': diagnosis.name,
                'phone': diagnosis.phone,
                'address': address,
                'lat': lat,
                'lng': lng,
                'risk': diagnosis.prediction,
                'marker_color': marker_color
            })

    return render(request, 'admin/map_admin.html', {'markers': marker_data})




def send_medication_email(request):
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            medication_request = form.save(commit=False)
            medication_request.user = request.user

            # ป้องกันไม่ให้กำหนดเวลาส่งอีเมลย้อนหลัง
            if medication_request.date_sent < now():
                return render(request, 'send_medication_email.html', {'form': form, 'error': 'ต้องเลือกเวลาที่มากกว่าปัจจุบัน'})

            medication_request.save()
            return redirect('success_email')

    else:
        form = MedicationForm()

    return render(request, 'send_medication_email.html', {'form': form})

# ฟังก์ชันแสดงประวัติคำขอ
def medication_request_history(request):
    medication_requests = MedicationRequest.objects.filter(user=request.user)
    return render(request, 'medication_request_history.html', {'medication_requests': medication_requests})

from django.shortcuts import render, redirect, get_object_or_404
from .forms import MedicationForm
from .models import MedicationRequest

# ฟังก์ชันแก้ไขคำขอ
def edit_medication_request(request, request_id):
    # ดึงข้อมูล MedicationRequest จากฐานข้อมูล
    medication_request = get_object_or_404(MedicationRequest, id=request_id, user=request.user)

    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication_request)
        if form.is_valid():
            form.save()  # บันทึกการเปลี่ยนแปลง
            return redirect('medication_request_history')  # กลับไปที่หน้าประวัติคำขอ
        else:
            # ถ้าฟอร์มไม่ถูกต้อง, แสดงข้อความข้อผิดพลาด
            return render(request, 'edit_medication_request.html', {'form': form, 'error': 'ข้อมูลไม่ถูกต้อง โปรดลองใหม่อีกครั้ง'})
    else:
        # ถ้าเป็น GET, แสดงฟอร์มพร้อมข้อมูลที่แก้ไข
        form = MedicationForm(instance=medication_request)

    return render(request, 'edit_medication_request.html', {'form': form})

# ฟังก์ชันลบคำขอ
def delete_medication_request(request, request_id):
    medication_request = get_object_or_404(MedicationRequest, id=request_id, user=request.user)
    medication_request.delete()  # ลบคำขอ
    return redirect('medication_request_history')  # กลับไปที่หน้าประวัติคำขอ

# ฟังก์ชันแสดงประวัติคำขอทั้งหมดสำหรับแอดมิน
def medication_request_list(request):
    # ตรวจสอบว่าเป็นแอดมิน
    if not request.user.is_staff:
        return redirect('home')  # ถ้าไม่ใช่แอดมินให้กลับไปหน้าหลัก

    # ดึงข้อมูลคำขอทั้งหมด
    medication_requests = MedicationRequest.objects.all()

    # ใช้ Paginator เพื่อแบ่งหน้า
    paginator = Paginator(medication_requests, 5)  # แสดง 5 รายการต่อหน้า
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'medication_request_list.html', {'page_obj': page_obj})

# ฟังก์ชันแก้ไขคำขอสำหรับแอดมิน
def edit_medication_request_admin(request, request_id):
    medication_request = get_object_or_404(MedicationRequest, id=request_id)

    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication_request)
        if form.is_valid():
            form.save()  # บันทึกการเปลี่ยนแปลง
            return redirect('medication_request_list')  # กลับไปที่หน้าประวัติคำขอทั้งหมด
    else:
        form = MedicationForm(instance=medication_request)

    return render(request, 'edit_medication_request_admin.html', {'form': form})

# ฟังก์ชันลบคำขอสำหรับแอดมิน
def delete_medication_request_admin(request, request_id):
    medication_request = get_object_or_404(MedicationRequest, id=request_id)
    medication_request.delete()  # ลบคำขอ
    return redirect('medication_request_list')  # กลับไปที่หน้าประวัติคำขอทั้งหมด

def success_email_liat(request):
    return render(request, 'success_emil.html')

@login_required
def articlesuser_view(request):
    articles = Articles.objects.all()
    return render(request, 'user_article/articles_user.html', {
        'articles': articles,
        'is_admin': request.user.is_staff,
        'is_medical_staff': request.user.groups.filter(name='Medical Officer').exists()
    })

def viewuser_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    return render(request, 'user_article/view_articleuser.html', {'article': article})





@login_required
def articlesadmin_view(request):
    articles = Articles.objects.all()
    return render(request, 'admin_/articles.html', {
        'articles': articles,
        'is_admin': request.user.is_staff,
        'is_medical_staff': request.user.groups.filter(name='Medical Officer').exists()
    })

def viewuadmin_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)

    return render(request, 'admin_/view_article.html', {'article': article})



@login_required
@user_passes_test(is_admin_or_medical_staff)
def add_articleadmin(request):
    if request.method == 'POST':
        form = ArticlesForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)  # สร้าง object แต่ยังไม่บันทึกในฐานข้อมูล
            article.author = request.user      # กำหนดผู้เขียนเป็นผู้ใช้ที่ล็อกอินอยู่
            article.save()                     # บันทึกบทความในฐานข้อมูล
            return redirect('articles')        # กลับไปยังหน้ารายการบทความ
    else:
        form = ArticlesForm()
    return render(request, 'admin_/add_article.html', {'form': form})

@login_required
@user_passes_test(is_admin_or_medical_staff)
def edit_articleadmin(request, article_id):
    article = get_object_or_404(Articles, id=article_id)

    if request.method == 'POST':
        form = ArticlesForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            return redirect('articles')
    else:
        form = ArticlesForm(instance=article)

    return render(request, 'admin_/edit_article.html', {'form': form, 'article': article})

# Delete an article (only admin or medical staff)
@login_required
@user_passes_test(is_admin_or_medical_staff)
def delete_articleadmin(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    if request.method == 'POST':
        article.delete()
        return redirect('articles_list')
    return render(request, 'admin_/delete_article.html', {'article': article})



def upload_file_test_admin(request):
    if request.method == 'POST' and request.FILES.get('file'):
        # ลบข้อมูลใน session ก่อนการอัปโหลดใหม่
        if not request.user.is_authenticated:
            return redirect('/login/')

        # อัปโหลดไฟล์ใหม่
        file1 = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file1.name, file1)
        file_path = fs.path(filename)

        # โหลดข้อมูลจากไฟล์
        df = load_data1(file_path)
        if df is None:
            return render(request, 'upload11.html', {"error": "Invalid file format. Please upload CSV or XLSX."})

        # เก็บข้อมูลใน session
        request.session['file_path'] = file_path
        request.session['df'] = df.to_dict(orient='records')

        # คำนวณข้อมูลต่างๆ เช่น จำนวนผู้ป่วย
        total_count = len(df)

        # 🟢 แยกข้อมูลส่วนตัวออกจากฟีเจอร์ที่ใช้วินิจฉัย
        personal_info = df[['Name', 'Address', 'Phone', 'Gender']]
        diagnostic_features = df.drop(columns=['Name', 'Address', 'Phone', 'Gender'], errors='ignore')
        diagnostic_features = diagnostic_features.drop(columns=['Outcome'], errors='ignore')

        # 🟢 ค้นหาตามเพศและที่อยู่ (ถ้ามีการกรอก)
        gender_filter = request.GET.get('gender', '')
        address_filter = request.GET.get('address', '')

        # กรองข้อมูลตามเงื่อนไข
        if gender_filter:
            personal_info = personal_info[personal_info['Gender'].str.contains(gender_filter, case=False, na=False)]

        if address_filter:
            personal_info = personal_info[personal_info['Address'].str.contains(address_filter, case=False, na=False)]

        # 🟢 โหลดโมเดลล่าสุด
        model, model_date = load_latest_model()
        if model is None:
            return render(request, 'upload11.html', {"error": "No trained model available."})

        # 🟢 ประมวลผลฟีเจอร์
        diagnostic_features = preprocess_data1(diagnostic_features)

        # 🟢 ทำนายผล
        predictions = model.predict(diagnostic_features)
        diagnostic_features['Predicted_Outcome'] = predictions

        # 🟢 คำนวณจำนวนผู้ป่วยที่มีความเสี่ยงและไม่มีความเสี่ยง
        risk_count = (predictions == 1).sum()
        no_risk_count = (predictions == 0).sum()

        # แยกอายุของกลุ่มเสี่ยงและไม่เสี่ยง
        age_risk_counts = diagnostic_features[diagnostic_features['Predicted_Outcome'] == 1][
            'Age'].value_counts().sort_index()
        age_no_risk_counts = diagnostic_features[diagnostic_features['Predicted_Outcome'] == 0][
            'Age'].value_counts().sort_index()

        # สร้างกลุ่มอายุทั้งหมด (0-4) และเติมค่า 0 ถ้ากลุ่มไหนไม่มีข้อมูล
        all_age_groups = pd.Series(0, index=[0, 1, 2, 3, 4])
        age_risk_counts = all_age_groups.add(age_risk_counts, fill_value=0)
        age_no_risk_counts = all_age_groups.add(age_no_risk_counts, fill_value=0)

        # แปลงเป็น list สำหรับส่งไปยัง template
        age_risk_data = age_risk_counts.tolist()
        age_no_risk_data = age_no_risk_counts.tolist()

        bmi_data = diagnostic_features['BMI'].value_counts().sort_index().tolist()
        glucose_data = diagnostic_features['Glucose'].value_counts().sort_index().tolist()

        # 🟢 รวมข้อมูลส่วนบุคคล + ฟีเจอร์ + ผลลัพธ์กลับคืนมา
        df = pd.concat([personal_info, diagnostic_features], axis=1)

        # 🟢 แปลงเป็น List ของ Dictionary
        df_records = df.to_dict(orient='records')

        # เก็บข้อมูลใน session
        request.session['df_records'] = df_records
        request.session['total_count'] = total_count
        request.session['bmi_data'] = bmi_data
        request.session['glucose_data'] = glucose_data


        # 🟢 ตรวจสอบการเข้าสู่ระบบของผู้ใช้
        for index, row in df.iterrows():
            diagnosis = Diagnosis_N(
                user=request.user,  # Optionally save the user (if authenticated)
                bmi=row['BMI'],
                blood_pressure=row['BloodPressure'],
                pregnancies=row['Pregnancies'],
                glucose=row['Glucose'],
                skin_thickness=row['SkinThickness'],
                insulin=row['Insulin'],
                diabetes_pedigree_function=row['DiabetesPedigreeFunction'],
                age=row['Age'],
                prediction='เสี่ยง' if row['Predicted_Outcome'] == 1 else 'ไม่เสี่ยง',
                name=row['Name'],  # เก็บชื่อ
                address=row['Address'],  # เก็บที่อยู่
                phone=row['Phone'],  # เก็บเบอร์โทรศัพท์
                gender=row['Gender']  # เก็บเพศ
            )
            diagnosis.save()

        return redirect('analysis_admin')  # เปลี่ยนหน้าไปยังหน้าแสดงผลข้อมูล (analysis)

    return render(request, 'admin/upload_admin.html')

def analyze_data_admin(request):
    if request.GET.get('reset_filter') == '1':
        # ล้างค่าตัวกรองจาก session
        request.session.pop('gender_filter', None)
        request.session.pop('address_filter', None)
        return redirect('analysis11')  # โหลดข้อมูลใหม่ทั้งหมด
    # ดึงข้อมูลจาก session
    df_records = request.session.get('df_records', None)
    if not df_records:
        return redirect('upload11')  # ถ้าไม่มีข้อมูลให้กลับไปหน้าอัปโหลด

    # ค่าตัวกรองจาก GET (เก็บค่าตัวกรองเดิมไว้)
    gender_filter = request.GET.get('gender', '')
    address_filter = request.GET.get('address', '')

    # กรองข้อมูลตามเพศ
    if gender_filter:
        df_records = [record for record in df_records if record.get('Gender') == gender_filter]

    # กรองข้อมูลตามที่อยู่
    if address_filter:
        df_records = [record for record in df_records if address_filter.lower() in record.get('Address', '').lower()]

    # 🟢 เก็บค่าตัวกรองใน session เพื่อให้ยังคงอยู่ระหว่างเปลี่ยนหน้า
    request.session['gender_filter'] = gender_filter
    request.session['address_filter'] = address_filter

    df = pd.DataFrame(df_records)

    total_count = len(df)

    # 🟢 คำนวณจำนวนเสี่ยง/ไม่เสี่ยงใหม่ทุกครั้ง
    risk_count = df[df['Predicted_Outcome'] == 1].shape[0]
    no_risk_count = df[df['Predicted_Outcome'] == 0].shape[0]
    total_count = df.shape[0]

    # 🟢 คำนวณอายุของกลุ่มเสี่ยงและไม่เสี่ยง
    age_risk_counts = df[df['Predicted_Outcome'] == 1]['Age'].value_counts().sort_index()
    age_no_risk_counts = df[df['Predicted_Outcome'] == 0]['Age'].value_counts().sort_index()

    # 🟢 เติมค่า 0 ให้กับช่วงอายุที่ไม่มีข้อมูล
    all_age_groups = pd.Series(0, index=[0, 1, 2, 3, 4])  # แบ่งช่วงอายุเป็นกลุ่ม 0-4, 5-9, ...
    age_risk_counts = all_age_groups.add(age_risk_counts, fill_value=0).tolist()
    age_no_risk_counts = all_age_groups.add(age_no_risk_counts, fill_value=0).tolist()


    # ใช้ Paginator สำหรับแบ่งหน้า
    paginator = Paginator(df_records, 5)  # แสดง 5 รายการต่อหน้า
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # ดึงข้อมูลจาก session เพื่อให้แสดงผลกราฟได้

    model, model_date = load_latest_model()
    bmi_data = request.session.get('bmi_data', [])
    glucose_data = request.session.get('glucose_data', [])

    # ส่งค่าตัวกรองไปยัง template และใช้ urlencode เพื่อให้ค่าค้นหายังคงอยู่
    filter_params = f"gender={gender_filter}&address={address_filter}"

    return render(request, 'admin/analysis_admin.html', {
        'df_records': df_records,
        'page_obj': page_obj,
        'gender_filter': gender_filter,
        'address_filter': address_filter,
        'risk_count': risk_count,
        'no_risk_count': no_risk_count,
        'total_count': total_count,
        'bmi_data': bmi_data,
        'glucose_data': glucose_data,
        'age_risk_data': age_risk_counts,
        'age_no_risk_data': age_no_risk_counts,
        'model_date': model_date,
        'filter_params': filter_params
    })


def diagnose_form_admin(request):
    return render(request, 'admin/diagnose_diabetes_admin.html')


def diagnose_diabetes_admin(request):
    if request.method == 'POST':
        try:
            pregnancies = int(request.POST.get('Pregnancies') or 0)
            glucose = int(request.POST.get('Glucose') or 0)
            blood_pressure = int(request.POST.get('BloodPressure') or 0)
            skin_thickness = int(request.POST.get('SkinThickness') or 0)
            insulin = int(request.POST.get('Insulin') or 0)
            bmi = float(request.POST.get('BMI') or 0)
            dpf = float(request.POST.get('DiabetesPedigreeFunction') or 0)
            age = int(request.POST.get('Age') or 0)

            # แปลงค่าที่กรอกมาเป็นหมวดหมู่ที่ 0, 1, 2, 3
            bmi_category = categorize_bmi_value(bmi)
            glucose_category = categorize_glucose_value(glucose)
            blood_pressure_category = categorize_blood_pressure_value(blood_pressure)
            skin_thickness_category = categorize_skin_thickness_value(skin_thickness)
            insulin_category = categorize_insulin_value(insulin)
            dpf_category = categorize_dpf_value(dpf)
            age_category = categorize_age_value(age)
            pregnancies_category = categorize_pregnancies_value(pregnancies)

            # เตรียมข้อมูล input สำหรับโมเดล
            input_data = [[pregnancies_category, glucose_category, blood_pressure_category,
                           skin_thickness_category, insulin_category, bmi_category,
                           dpf_category, age_category]]

            # โหลดโมเดลล่าสุด
            model, uploaded_at = load_latest_model()

            if not model:
                return render(request, 'admin/diagnose_diabetes_admin.html', {'error': "ยังไม่มีโมเดลที่อัปโหลด กรุณาอัปโหลดโมเดลก่อน."})

            # ทำนายผล
            rf_pred = model.predict(input_data)
            predictions = 'เสี่ยง' if rf_pred[0] == 1 else 'ไม่เสี่ยง'

            # สร้าง dictionary สำหรับแสดงค่าที่แปลงแล้ว
            categorized_data = {
                'Pregnancies': pregnancies_category,
                'Glucose': glucose_category,
                'Blood Pressure': blood_pressure_category,
                'Skin Thickness': skin_thickness_category,
                'Insulin': insulin_category,
                'BMI': bmi_category,
                'Diabetes Pedigree Function': dpf_category,
                'Age': age_category
            }

            # เพิ่มข้อมูลที่กรอกก่อนแปลง
            input_data_before_categorization = {
                'Pregnancies': pregnancies,
                'Glucose': glucose,
                'Blood Pressure': blood_pressure,
                'Skin Thickness': skin_thickness,
                'Insulin': insulin,
                'BMI': bmi,
                'Diabetes_Pedigree_Function': dpf,
                'Age': age
            }

            # Save the diagnosis result to the database
            diagnosis = Diagnosis_N(
                user=request.user,  # Save the user (if applicable)
                bmi=bmi,
                blood_pressure=blood_pressure,
                pregnancies=pregnancies,
                glucose=glucose,
                skin_thickness=skin_thickness,
                insulin=insulin,
                diabetes_pedigree_function=dpf,
                age=age,
                prediction=predictions
            )
            diagnosis.save()

            return render(request, 'admin/result_admin.html', {
                'results': predictions,
                'categorized_data': categorized_data,  # แสดงค่าที่แปลงแล้ว
                'input_data_before_categorization': input_data_before_categorization,  # แสดงค่าก่อนแปลง
                'uploaded_at': uploaded_at  # แสดงเวลาที่อัปโหลดโมเดล
            })

        except ValueError as e:
            return render(request, 'admin/diagnose_diabetes_admin.html', {'error': f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"})

    return render(request, 'admin/diagnose_diabetes_admin.html')
