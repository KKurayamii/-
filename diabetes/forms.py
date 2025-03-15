from django import forms
from django.contrib.auth.forms import UserCreationForm
#from flatpickr import DateTimePickerInput
from .models import *
from django.utils.timezone import now


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1','password2' ]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'sex', 'profile_picture']


class ArticlesForm(forms.ModelForm):
    class Meta:
        model = Articles
        fields = ['title', 'content', 'image', 'video_url']

class RatingForm(forms.Form):
    rating = forms.ChoiceField(
        choices=[(str(i), f"{i} ดาว") for i in range(1, 6)],
        widget=forms.RadioSelect
    )

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'sex', 'role']
        labels = {
            'username': 'ชื่อผู้ใช้งาน',
            'email': 'อีเมล',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'sex': 'เพศ',
            'role': 'บทบาท',
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # เอาข้อความผิดพลาดทั้งหมดออก
            for field in self.fields.values():
                field.error_messages = {
                    'required': '',
                    'max_length': '',
                    'invalid': '',
                }

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'permissions']

class UploadFileForm(forms.Form):
    file = forms.FileField()

class ModelUploadForm(forms.ModelForm):
    class Meta:
        model = MLModel
        fields = ['name', 'model_file']


class HealthRecord1Form(forms.ModelForm):
    class Meta:
        model = HealthRecord1
        exclude = ['user', 'bmi']
        fields = '__all__'
        widgets = {
            'last_visit_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class DiabetesDiagnosisForm11(forms.Form):
    pregnancies = forms.IntegerField(label='จำนวนการตั้งครรภ์', required=True)
    glucose = forms.IntegerField(label='ระดับน้ำตาลในเลือด', required=True)
    blood_pressure = forms.IntegerField(label='ความดันโลหิต', required=True)
    skin_thickness = forms.IntegerField(label='ความหนาของผิวหนัง', required=True)
    insulin = forms.IntegerField(label='ระดับอินซูลิน', required=True)
    bmi = forms.FloatField(label='ดัชนีมวลกาย (BMI)', required=True)
    diabetes_pedigree_function = forms.FloatField(label='ฟังก์ชันพงศ์พันธุ์เบาหวาน', required=True)
    age = forms.IntegerField(label='อายุ', required=True)

class HealthRecordForm2(forms.ModelForm):
    class Meta:
        model = HealthRecord1
        fields = '__all__'

