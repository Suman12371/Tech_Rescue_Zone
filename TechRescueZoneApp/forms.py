from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import (Profile, Hardware, HardwareImage, HardwareReview,Order,Solution, SolutionStep, SolutionImage,)

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    STATUS_CHOICES = (
        ('export', 'Export'),
        ('user', 'User'),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, initial='export')
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
class EmailVerificationForm(forms.Form):
    verification_code = forms.CharField(max_length=6, required=True)
    
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

class HardwareForm(forms.ModelForm):
    class Meta:
        model = Hardware
        fields = ['name', 'description', 'price', 'discount_price', 'category', 'stock', 'is_featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

HardwareImageFormSet = inlineformset_factory(
    Hardware, 
    HardwareImage,
    fields=('image', 'is_primary'),
    extra=3,
    can_delete=True
)

class HardwareReviewForm(forms.ModelForm):
    class Meta:
        model = HardwareReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ['title', 'summary', 'content', 'category']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }

class SolutionStepForm(forms.ModelForm):
    class Meta:
        model = SolutionStep
        fields = ['title', 'content', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

SolutionStepFormSet = inlineformset_factory(
    Solution, 
    SolutionStep,
    form=SolutionStepForm,
    extra=1,
    can_delete=True
)

class SolutionImageForm(forms.ModelForm):
    class Meta:
        model = SolutionImage
        fields = ['image', 'caption']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
        }
