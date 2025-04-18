from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import (
    Profile, Hardware, HardwareImage, HardwareReview, Order,
    Solution, SolutionStep, SolutionImage, SolutionComment, SolutionRating,
    Message
)
from django.forms import inlineformset_factory, BaseInlineFormSet

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

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
        }

class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ['title', 'summary', 'content', 'category']
        # widgets = {
        #     'summary': forms.Textarea(attrs={'rows': 3}),
        #     'content': forms.Textarea(attrs={'rows': 10}),
        # }

# class SolutionStepForm(forms.ModelForm):
#     class Meta:
#         model = SolutionStep
#         fields = ['title', 'content', 'order']
        # widgets = {
        #     'content': forms.Textarea(attrs={'rows': 5}),
        # }

# SolutionStepFormSet = inlineformset_factory(
#     Solution, 
#     SolutionStep,
#     form=SolutionStepForm,
#     extra=1,
#     can_delete=True,
#     min_num=1,
#     validate_min=True
# )

class SolutionStepForm(forms.ModelForm):
    class Meta:
        model = SolutionStep
        fields = ['title', 'content', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class BaseSolutionStepFormSet(BaseInlineFormSet):
    def clean(self):
        """
        Custom clean method to ensure all forms are valid and properly processed
        """
        super().clean()
        
        # Check if any forms have been submitted
        if any(self.errors):
            return
            
        # Validate that we have at least one step
        if not any(form.cleaned_data and not form.cleaned_data.get('DELETE', False) 
                  for form in self.forms):
            raise forms.ValidationError('At least one step is required.')
            
        # Validate that all steps have unique order values
        orders = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                order = form.cleaned_data.get('order')
                if order in orders:
                    raise forms.ValidationError(f'Step {order} appears multiple times. Each step must have a unique order number.')
                orders.append(order)

# Create a formset with a high max_num to ensure many steps can be added
SolutionStepFormSet = inlineformset_factory(
    Solution, 
    SolutionStep,
    form=SolutionStepForm,
    formset=BaseSolutionStepFormSet,
    fields=('title', 'content', 'order'),
    extra=1,
    can_delete=True,
    max_num=50,  # Allow up to 50 steps
    validate_max=False,  # Don't validate max_num
)

class SolutionImageForm(forms.ModelForm):
    class Meta:
        model = SolutionImage
        fields = ['image', 'caption']

class SolutionCommentForm(forms.ModelForm):
    class Meta:
        model = SolutionComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }
        labels = {
            'content': '',
        }

class SolutionRatingForm(forms.ModelForm):
    class Meta:
        model = SolutionRating
        fields = ['rating']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-input'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2, 
                'placeholder': 'Type your message here...',
                'class': 'message-input',
            }),
        }
        labels = {
            'content': '',
        }