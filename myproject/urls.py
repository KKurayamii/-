"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from diabetes import views
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/login/', lambda request: redirect('login')),
    path('registration/login/', views.CustomLoginView.as_view(), name='login_r'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard_user', views.dashboard_user, name='dashboard'),
    path('dashboard/admin/dashboard_adminn/', views.dashboard_adminn, name='dashboard_adminn'),
    path('dashboard/doctor/home_dc/', views.dashboard_medical_staff, name='home_dc'),
    path('profile/', views.profile_view, name='profile'),
    path('articles/', views.articles_view, name='articles'),
    path('articles/list', views.articles_view, name='articles_list'),
    path('articles/add/', views.add_article, name='add_article'),
    path('articles/edit/<int:article_id>/', views.edit_article, name='edit_article'),
    path('articles/delete/<int:article_id>/', views.delete_article, name='delete_article'),
    path('articles/view/<int:article_id>/', views.view_article, name='view_article'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('view_all_users/', views.view_all_users, name='view_all_users'),
    path('upload_model/', views.upload_modelML, name='upload_model'),
    path('upload_model/upload_model/success_page/', views.success_page, name='success_page'),
    path('health-record1/', views.health_record_view1, name='health_record1'),
    path('success1/', views.success_page1, name='success1'),
    path('health_recordview', views.health_recordview, name='health_recordview'),
    path("historyview/", views.history_view1, name="history1"),
    path('diagnose_t/', views.diagnose_form, name='diagnose_t'),
    path('result_t/', views.diagnose_diabetes, name='result_t'),
    path('upload_file_test/', views.upload_file_test, name='upload11'),
    path('analysis/', views.analyze_data, name='analysis11'),
    path('health-records_admin/', views.health_record_list_admin, name='health_record_list_admin'),
    path('health-record_admin/<int:record_id>/', views.health_record_detail_admin, name='health_record_detail_admin'),
    path('health-record_admin/edit/<int:record_id>/', views.health_record_edit_admin, name='health_record_edit_admin'),
    path('health-record_admin/delete/<int:record_id>/', views.health_record_delete_admin, name='health_record_delete_admin'),
    path('doctor/health-records/', views.health_record_for_doctor, name='health_record_for_doctor'),
    path('doctor/health-record/<int:record_id>/', views.health_record_detail_for_doctor, name='health_record_detail_for_doctor'),
    path('diagnosis-report/', views.diagnosis_report_ad, name='diagnosis_report'),
    path('diagnosis-report_dc/', views.diagnosis_report_dc, name='diagnosis_report_dc'),
    path('map/', views.show_map, name='map_view'),
    path('map_admin/', views.show_map_admin, name='map_admin'),
    path('feature-importance/', views.feature_importance_view, name='feature_importance'),
    path('risk_info/', views.risk_info, name='risk_info'),
    path('no_risk_info/', views.no_risk_info, name='no_risk_info'),
    path('age-category/<str:age_category>-<str:risk_category>/', views.age_category_risk_info, name='age_category_risk_info'),
    path('diagnose_doctor/', views.diagnose_form_doctor, name='diagnose_doctor'),
    path('result_doctor/', views.diagnose_diabetes_doctor, name='result_doctor'),
    path('send-medication-email/', views.send_medication_email, name='send_medication_email'),
    path('medication-history/', views.medication_request_history, name='medication_request_history'),
    path('edit-medication-request/<int:request_id>/', views.edit_medication_request, name='edit_medication_request'),
    path('delete-medication-request/<int:request_id>/', views.delete_medication_request,name='delete_medication_request'),
    path('medication-request/list/', views.medication_request_list, name='medication_request_list'),
    path('medication-request/edit/<int:request_id>/', views.edit_medication_request_admin,name='edit_medication_request_admin'),
    path('medication-request/delete/<int:request_id>/', views.delete_medication_request_admin,name='delete_medication_request_admin'),
    path('success-email/', views.success_email_liat, name='success_email'),
    path('articles_user/', views.articlesuser_view, name='articles_user'),
    path('articles_user/list', views.articlesuser_view, name='articles_list'),
    path('articles_user/view/<int:article_id>/', views.viewuser_article, name='view_article_user'),
    path('admin_articles/', views.articlesadmin_view, name='articles_admin'),  # หน้ารายการบทความ
    path('admin_articles/add/', views.add_articleadmin, name='add_article'),  # หน้าสร้างบทความใหม่
    path('admin_articles/edit/<int:article_id>/', views.edit_articleadmin, name='edit_article_admin'),  # หน้าจัดการแก้ไขบทความ
    path('admin_articles/view/<int:article_id>/', views.viewuadmin_article, name='view_article_admin'),  # หน้ารายละเอียดบทความ
    path('admin_articles/delete/<int:article_id>/', views.delete_articleadmin, name='delete_article_admin'),
    path('upload_file_admin/', views.upload_file_test_admin, name='upload_admin'),
    path('analysis_admin/', views.analyze_data_admin, name='analysis_admin'),
    path('diagnose_admin/', views.diagnose_form_admin, name='diagnose_admin'),
    path('result_admin/', views.diagnose_diabetes_admin, name='result_admin'),

path('', views.CustomLoginView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

