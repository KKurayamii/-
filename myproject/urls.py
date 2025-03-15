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
    path('rate/<int:article_id>/', views.rate_article, name='rate_article'),
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
    path('map/', views.show_map, name='map_view'),
    path('feature-importance/', views.feature_importance_view, name='feature_importance'),
    path('risk_info/', views.risk_info, name='risk_info'),
    path('no_risk_info/', views.no_risk_info, name='no_risk_info'),
    path('diagnose_doctor/', views.diagnose_form_doctor, name='diagnose_doctor'),
    path('result_doctor/', views.diagnose_diabetes_doctor, name='result_doctor'),

path('', views.CustomLoginView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

