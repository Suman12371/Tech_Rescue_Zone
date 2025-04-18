from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Avg, Q, Count, Max
from django.http import JsonResponse
import random
import uuid
import pusher
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Profile, Category, Hardware, HardwareImage, HardwareReview, Order, OrderItem,
    SolutionCategory, Solution, SolutionStep, SolutionComment, SolutionRating,
    Conversation, Message, Notification, Payment, PaymentMethod, SolutionImage
)
from .forms import (
    UserRegisterForm, EmailVerificationForm, ProfileForm, HardwareForm, HardwareImageFormSet,
    HardwareReviewForm, OrderForm, SolutionForm, SolutionStepFormSet, SolutionCommentForm,
    SolutionRatingForm, MessageForm
)

User = get_user_model()

# Initialize Pusher client
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)

def home_view(request):
    featured_hardware = Hardware.objects.filter(is_featured=True)

    for hardware in featured_hardware:
        hardware.primary_image = hardware.images.filter(is_primary=True).first() or hardware.images.first()

    context = {'featured_hardware': featured_hardware}
    return render(request, 'home.html', context)

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            status = request.POST.get('status')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username is taken.')
                return redirect('TechRescueZoneApp:register')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is taken.')
                return redirect('TechRescueZoneApp:register')
            
            verification_code = str(random.randint(100000, 999999))
            auth_token = str(uuid.uuid4())
            
            request.session['registration_data'] = {
                'username': username,
                'email': email,
                'password': password,
                'status': status,
                'verification_code': verification_code,
                'auth_token': auth_token,
            }
            
            send_verification_code(email, verification_code)
            return redirect('TechRescueZoneApp:verify_email')
    else:
        form = UserRegisterForm()    
    return render(request, 'registration/register.html', {'form': form})

def verify_email(request):
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data.get('verification_code')
            registration_data = request.session.get('registration_data')

            if not registration_data:
                messages.error(request, 'No registration data found. Please try again.')
                return redirect('TechRescueZoneApp:register')

            if verification_code != registration_data.get('verification_code'):
                messages.error(request, 'Invalid verification code.')
                return redirect('TechRescueZoneApp:verify_email')

            user = User.objects.create_user(
                username=registration_data['username'],
                email=registration_data['email'],
                password=registration_data['password'],
            )
            
            Profile.objects.create(
                user=user,
                is_verified=True,
                status=registration_data['status'].lower(),
                auth_token=registration_data['auth_token'],
            )

            del request.session['registration_data']
            
            send_success_email(registration_data['email'])
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('/login')
    else:
        form = EmailVerificationForm()
    return render(request, 'verify_email.html', {'form': form})


def send_verification_code(email, code):
    subject = 'Your verification code'
    message = f'Your verification code is {code}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)

def send_success_email(email):
    subject = 'Registration successful'
    message = 'Your registration was successful. Welcome!'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user_obj = User.objects.filter(username=username).first()
        if user_obj is None:
            messages.success(request, 'User not found.')
            return redirect('/login')
        
        profile_obj = Profile.objects.filter(user=user_obj).first()
        if not profile_obj.is_verified:
            messages.success(request, 'Profile is not verified. Check your email.')
            return redirect('/login')
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            messages.success(request, 'Wrong password.')
            return redirect('/login')
        
        login(request, user)
        return redirect('TechRescueZoneApp:home')

    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('/login/')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'forgot_password.html'
    success_url = reverse_lazy('TechRescueZoneApp:password_reset_done')
    email_template_name = 'password_reset_email.html'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('TechRescueZoneApp:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'


def user_profile(request):
    return render(request, 'profiles/user_profile.html')

def export_profile(request):
    return render(request, 'profiles/export_profile.html')


def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('TechRescueZoneApp:home')

    total_users = User.objects.count()
    total_solutions = Solution.objects.count()
    total_hardware = Hardware.objects.count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_solutions = Solution.objects.order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_solutions': total_solutions,
        'total_hardware': total_hardware,
        'recent_users': recent_users,
        'recent_solutions': recent_solutions,
    }
    return render(request, 'dashboard.html', context)

def hardware_list(request):
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort_by', 'name')

    hardware_items = Hardware.objects.all()

    if category_id:
        hardware_items = hardware_items.filter(category_id=category_id)

    if min_price:
        hardware_items = hardware_items.filter(price__gte=min_price)

    if max_price:
        hardware_items = hardware_items.filter(price__lte=max_price)

    if search_query:
        hardware_items = hardware_items.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    if sort_by == 'price_low':
        hardware_items = hardware_items.order_by('price')
    elif sort_by == 'price_high':
        hardware_items = hardware_items.order_by('-price')
    elif sort_by == 'newest':
        hardware_items = hardware_items.order_by('-created_at')
    else:
        hardware_items = hardware_items.order_by('name')

    categories = Category.objects.all()

    context = {
        'hardware_items': hardware_items,
        'categories': categories,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'hardware/hardware_list.html', context)

def hardware_detail(request, hardware_id):
    hardware = get_object_or_404(Hardware, id=hardware_id)
    reviews = hardware.reviews.all().order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    if request.method == 'POST' and request.user.is_authenticated:
        review_form = HardwareReviewForm(request.POST)
        if review_form.is_valid():
            existing_review = HardwareReview.objects.filter(hardware=hardware, user=request.user).first()
            if existing_review:
                existing_review.rating = review_form.cleaned_data['rating']
                existing_review.comment = review_form.cleaned_data['comment']
                existing_review.save()
                messages.success(request, 'Your review has been updated!')
            else:
                review = review_form.save(commit=False)
                review.hardware = hardware
                review.user = request.user
                review.save()
                messages.success(request, 'Your review has been submitted!')
            return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)
    else:
        review_form = HardwareReviewForm()

    related_hardware = Hardware.objects.filter(category=hardware.category).exclude(id=hardware.id)[:4]

    context = {
        'hardware': hardware,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_form': review_form,
        'related_hardware': related_hardware,
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY if hasattr(settings, 'KHALTI_PUBLIC_KEY') else 'test_public_key_12345abcde',
    }
    return render(request, 'hardware/hardware_detail.html', context)

@login_required
def add_to_cart(request, hardware_id):
    hardware = get_object_or_404(Hardware, id=hardware_id)
    quantity = int(request.POST.get('quantity', 1))

    if hardware.stock < quantity:
        messages.error(request, f'Sorry, only {hardware.stock} units available.')
        return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)

    if 'cart' not in request.session:
        request.session['cart'] = {}

    cart = request.session['cart']
    hardware_id_str = str(hardware_id)

    if hardware_id_str in cart:
        cart[hardware_id_str]['quantity'] += quantity
    else:
        cart[hardware_id_str] = {
            'quantity': quantity,
            'price': float(hardware.get_final_price()),
            'name': hardware.name,
        }

    request.session.modified = True
    messages.success(request, f'{hardware.name} added to your cart.')
    return redirect('TechRescueZoneApp:cart')

@login_required
def cart(request):
    cart_items = []
    total = 0

    if 'cart' in request.session:
        for hardware_id, item_data in request.session['cart'].items():
            hardware = get_object_or_404(Hardware, id=hardware_id)
            quantity = item_data['quantity']
            price = item_data['price']
            item_total = quantity * price
            
            cart_items.append({
                'hardware': hardware,
                'quantity': quantity,
                'price': price,
                'total': item_total,
            })
            
            total += item_total

    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'hardware/cart.html', context)

@login_required
def checkout(request):
    if 'cart' not in request.session or not request.session['cart']:
        messages.error(request, 'Your cart is empty.')
        return redirect('TechRescueZoneApp:cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            
            total = 0
            for hardware_id, item_data in request.session['cart'].items():
                quantity = item_data['quantity']
                price = item_data['price']
                total += quantity * price
            
            order.total_price = total
            order.save()
            
            for hardware_id, item_data in request.session['cart'].items():
                hardware = get_object_or_404(Hardware, id=hardware_id)
                quantity = item_data['quantity']
                price = item_data['price']
                
                OrderItem.objects.create(
                    order=order,
                    hardware=hardware,
                    quantity=quantity,
                    price=price,
                )
                
                hardware.stock -= quantity
                hardware.save()
            
            del request.session['cart']
            request.session.modified = True
            
            messages.success(request, 'Your order has been placed successfully!')
            return redirect('TechRescueZoneApp:payment_process', order_id=order.id)
    else:
        form = OrderForm()

    cart_items = []
    subtotal = 0

    for hardware_id, item_data in request.session['cart'].items():
        hardware = get_object_or_404(Hardware, id=hardware_id)
        quantity = item_data['quantity']
        price = item_data['price']
        item_total = quantity * price
        
        cart_items.append({
            'hardware': hardware,
            'quantity': quantity,
            'price': price,
            'total': item_total,
        })
        
        subtotal += item_total

    shipping = 10.00
    tax = subtotal * 0.08
    total = subtotal + shipping + tax

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'hardware/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
    }
    return render(request, 'hardware/order_confirmation.html', context)

@login_required
def update_cart_item(request, hardware_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if 'cart' in request.session:
            cart = request.session['cart']
            hardware_id_str = str(hardware_id)
            
            if hardware_id_str in cart:
                hardware = get_object_or_404(Hardware, id=hardware_id)
                
                if quantity > hardware.stock:
                    messages.error(request, f'Sorry, only {hardware.stock} units available.')
                    return redirect('TechRescueZoneApp:cart')
                
                if quantity <= 0:
                    del cart[hardware_id_str]
                else:
                    cart[hardware_id_str]['quantity'] = quantity
                
                request.session.modified = True
                messages.success(request, 'Cart updated successfully.')

    return redirect('TechRescueZoneApp:cart')

@login_required
def remove_from_cart(request, hardware_id):
    if request.method == 'POST':
        if 'cart' in request.session:
            cart = request.session['cart']
            hardware_id_str = str(hardware_id)
            
            if hardware_id_str in cart:
                hardware = get_object_or_404(Hardware, id=hardware_id)
                del cart[hardware_id_str]
                request.session.modified = True
                messages.success(request, f'{hardware.name} removed from your cart.')

    return redirect('TechRescueZoneApp:cart')

@login_required
def add_hardware(request):
    if request.method == 'POST':
        form = HardwareForm(request.POST)
        formset = HardwareImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            hardware = form.save(commit=False)
            hardware.seller = request.user
            hardware.save()
            
            instances = formset.save(commit=False)
            for instance in instances:
                instance.hardware = hardware
                instance.save()
            
            messages.success(request, 'Hardware item added successfully!')
            return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)
    else:
        form = HardwareForm()
        formset = HardwareImageFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'hardware/add_hardware.html', context)

@login_required
def edit_hardware(request, hardware_id):
    hardware = get_object_or_404(Hardware, id=hardware_id)

    if hardware.seller != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this hardware item.')
        return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)

    if request.method == 'POST':
        form = HardwareForm(request.POST, instance=hardware)
        formset = HardwareImageFormSet(request.POST, request.FILES, instance=hardware)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Hardware item updated successfully!')
            return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)
    else:
        form = HardwareForm(instance=hardware)
        formset = HardwareImageFormSet(instance=hardware)

    context = {
        'form': form,
        'formset': formset,
        'hardware': hardware,
    }
    return render(request, 'hardware/edit_hardware.html', context)

@login_required
def delete_hardware(request, hardware_id):
    hardware = get_object_or_404(Hardware, id=hardware_id)

    if hardware.seller != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this hardware item.')
        return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)

    if request.method == 'POST':
        hardware.delete()
        messages.success(request, 'Hardware item deleted successfully!')
        return redirect('TechRescueZoneApp:hardware_list')

    context = {
        'hardware': hardware,
    }
    return render(request, 'hardware/delete_hardware.html', context)

def solution_list(request):
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort_by', 'newest')

    solutions = Solution.objects.all()

    if category_id:
        solutions = solutions.filter(category_id=category_id)

    if search_query:
        solutions = solutions.filter(
            Q(title__icontains=search_query) | 
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    if sort_by == 'popular':
        solutions = solutions.annotate(like_count=Count('likes')).order_by('-like_count')
    elif sort_by == 'top_rated':
        solutions = solutions.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
    elif sort_by == 'most_viewed':
        solutions = solutions.order_by('-views')
    else:
        solutions = solutions.order_by('-created_at')

    categories = SolutionCategory.objects.all()

    context = {
        'solutions': solutions,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'software/solution_list.html', context)

def solution_detail(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)
    steps = solution.steps.all().order_by('order')
    comments = solution.comments.all().order_by('-created_at')

    solution.views += 1
    solution.save()

    if request.method == 'POST' and 'comment_submit' in request.POST and request.user.is_authenticated:
        comment_form = SolutionCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.solution = solution
            comment.user = request.user
            comment.save()
            
            Notification.objects.create(
                recipient=solution.author,
                sender=request.user,
                notification_type='solution_comment',
                content=f"{request.user.username} commented on your solution '{solution.title}'",
                link=f"/solutions/{solution.id}/"
            )
            
            messages.success(request, 'Your comment has been posted!')
            return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)
    else:
        comment_form = SolutionCommentForm()

    if request.method == 'POST' and 'rating_submit' in request.POST and request.user.is_authenticated:
        rating_form = SolutionRatingForm(request.POST)
        if rating_form.is_valid():
            existing_rating = SolutionRating.objects.filter(solution=solution, user=request.user).first()
            if existing_rating:
                existing_rating.rating = rating_form.cleaned_data['rating']
                existing_rating.save()
                messages.success(request, 'Your rating has been updated!')
            else:
                rating = rating_form.save(commit=False)
                rating.solution = solution
                rating.user = request.user
                rating.save()
                
                Notification.objects.create(
                    recipient=solution.author,
                    sender=request.user,
                    notification_type='solution_rating',
                    content=f"{request.user.username} rated your solution '{solution.title}' with {rating.rating} stars",
                    link=f"/solutions/{solution.id}/"
                )
                
                messages.success(request, 'Your rating has been submitted!')
            return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)
    else:
        if request.user.is_authenticated:
            existing_rating = SolutionRating.objects.filter(solution=solution, user=request.user).first()
            if existing_rating:
                rating_form = SolutionRatingForm(instance=existing_rating)
            else:
                rating_form = SolutionRatingForm()
        else:
            rating_form = SolutionRatingForm()

    user_liked = False
    if request.user.is_authenticated:
        user_liked = solution.likes.filter(id=request.user.id).exists()

    related_solutions = Solution.objects.filter(category=solution.category).exclude(id=solution.id)[:4]

    context = {
        'solution': solution,
        'steps': steps,
        'comments': comments,
        'comment_form': comment_form,
        'rating_form': rating_form,
        'user_liked': user_liked,
        'related_solutions': related_solutions,
    }
    return render(request, 'software/solution_detail.html', context)

@login_required
def create_solution(request):
    if request.method == 'POST':
        form = SolutionForm(request.POST)
        if form.is_valid():
            solution = form.save(commit=False)
            solution.author = request.user
            solution.save()
            
            return redirect('TechRescueZoneApp:add_solution_steps', solution_id=solution.id)
    else:
        form = SolutionForm()

    context = {
        'form': form,
    }
    return render(request, 'software/create_solution.html', context)

@login_required
def edit_solution(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)

    if solution.author != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this solution.')
        return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)

    if request.method == 'POST':
        form = SolutionForm(request.POST, instance=solution)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solution updated successfully!')
            return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)
    else:
        form = SolutionForm(instance=solution)

    context = {
        'form': form,
        'solution': solution,
    }
    return render(request, 'software/edit_solution.html', context)

@login_required
def add_solution_steps(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)

    if solution.author != request.user:
        messages.error(request, 'You do not have permission to edit this solution.')
        return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)

    if request.method == 'POST':
        # Debug information
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        print(f"TOTAL_FORMS: {request.POST.get('form-TOTAL_FORMS')}")
        print(f"INITIAL_FORMS: {request.POST.get('form-INITIAL_FORMS')}")
        
        # Create the formset with the POST data
        formset = SolutionStepFormSet(request.POST, request.FILES, instance=solution)
        
        if formset.is_valid():
            print("Formset is valid")
            # Save each form individually to ensure all are processed
            instances = []
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    print(f"Saving form with data: {form.cleaned_data}")
                    instance = form.save(commit=False)
                    instance.solution = solution
                    instance.save()
                    instances.append(instance)
            
            # Process images for each saved instance
            for i, instance in enumerate(instances):
                # Find all image files for this step
                for key in request.FILES.keys():
                    if key.startswith(f'step_image_{i}_'):
                        image_file = request.FILES[key]
                        # Extract image number from key (e.g., step_image_0_1 -> 1)
                        image_num = key.split('_')[-1]
                        caption_key = f'step_image_caption_{i}_{image_num}'
                        caption = request.POST.get(caption_key, '')
                        
                        # Create the image
                        SolutionImage.objects.create(
                            step=instance,
                            image=image_file,
                            caption=caption
                        )
            
            messages.success(request, f'Solution steps added successfully! {len(instances)} steps were saved.')
            return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)
        else:
            # Debug formset validation errors
            print("Formset validation errors:", formset.errors)
            print("Non-form errors:", formset.non_form_errors())
            for i, form in enumerate(formset.forms):
                if form.errors:
                    print(f"Form {i} errors:", form.errors)
            
            messages.error(request, 'There was an error saving your steps. Please check the form and try again.')
    else:
        # If there are no existing steps, create at least one empty form
        if solution.steps.count() == 0:
            formset = SolutionStepFormSet(instance=solution, initial=[{'order': 1}])
        else:
            formset = SolutionStepFormSet(instance=solution)

    context = {
        'solution': solution,
        'formset': formset,
    }
    return render(request, 'software/add_solution_steps.html', context)

@login_required
def edit_solution_steps(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)

    if solution.author != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this solution.')
        return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)

    if request.method == 'POST':
        formset = SolutionStepFormSet(request.POST, instance=solution)
        if formset.is_valid():
            steps = formset.save()
            
            # Process images for each step
            for i, step in enumerate(steps):
                # Check for images to delete
                for key in request.POST.keys():
                    if key.startswith('delete_image_'):
                        image_id = key.replace('delete_image_', '')
                        try:
                            image = SolutionImage.objects.get(id=image_id, step=step)
                            image.delete()
                        except SolutionImage.DoesNotExist:
                            pass
                
                # Find all image files for this step
                image_keys = [k for k in request.FILES.keys() if k.startswith(f'step_image_{i}_')]
                
                for key in image_keys:
                    image_file = request.FILES[key]
                    # Extract image number from key (e.g., step_image_0_1 -> 1)
                    image_num = key.split('_')[-1]
                    caption_key = f'step_image_caption_{i}_{image_num}'
                    caption = request.POST.get(caption_key, '')
                    
                    # Create the image
                    SolutionImage.objects.create(
                        step=step,
                        image=image_file,
                        caption=caption
                    )
            
            messages.success(request, 'Solution steps updated successfully!')
            return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)
    else:
        formset = SolutionStepFormSet(instance=solution)

    context = {
        'solution': solution,
        'formset': formset,
    }
    return render(request, 'software/edit_solution_steps.html', context)

@login_required
def delete_solution(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)

    if solution.author != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this solution.')
        return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)

    if request.method == 'POST':
        solution.delete()
        messages.success(request, 'Solution deleted successfully!')
        return redirect('TechRescueZoneApp:solution_list')

    context = {
        'solution': solution,
    }
    return render(request, 'software/delete_solution.html', context)

@login_required
def like_solution(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)

    if solution.likes.filter(id=request.user.id).exists():
        solution.likes.remove(request.user)
        liked = False
    else:
        solution.likes.add(request.user)
        liked = True
        
        if solution.author != request.user:
            Notification.objects.create(
                recipient=solution.author,
                sender=request.user,
                notification_type='solution_like',
                content=f"{request.user.username} liked your solution '{solution.title}'",
                link=f"/solutions/{solution.id}/"
            )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': solution.get_like_count(),
        })

    return redirect('TechRescueZoneApp:solution_detail', solution_id=solution.id)

@login_required
def chat_list(request):
    # Get all conversations where the current user is a participant
    conversations = Conversation.objects.filter(participants=request.user)

    conversations = conversations.annotate(
        latest_message_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    ).order_by('-latest_message_time')

    conversation_data = []
    for conversation in conversations:
        other_user = conversation.get_other_participant(request.user)
        latest_message = conversation.messages.order_by('-created_at').first()
        
        conversation_data.append({
            'id': conversation.id,
            'other_user': other_user,
            'latest_message': latest_message,
            'unread_count': conversation.unread_count,
        })

    context = {
        'conversations': conversation_data,
        'pusher_key': settings.PUSHER_KEY,
        'pusher_cluster': settings.PUSHER_CLUSTER,
    }
    return render(request, 'chat/chat_list.html', context)

@login_required
def chat_detail(request, conversation_id):
    # Get the conversation and check if the user is a participant
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if not conversation.participants.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('TechRescueZoneApp:chat_list')
    
    other_user = conversation.get_other_participant(request.user)
    
    # Mark unread messages as read
    unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user)
    unread_messages.update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            # Create notification
            Notification.objects.create(
                recipient=other_user,
                sender=request.user,
                notification_type='message',
                content=f"New message from {request.user.username}",
                link=f"/chat/{conversation.id}/"
            )
            
            # Trigger Pusher event for real-time messaging
            pusher_client.trigger(
                f'private-chat-{conversation.id}', 
                'new-message',
                {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender.id,
                    'sender_username': message.sender.username,
                    'sender_profile_picture': message.sender.profile.profile_picture.url if message.sender.profile.profile_picture else None,
                    'created_at': message.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'is_read': message.is_read
                }
            )
            
            # Also trigger an event to update the conversation list
            pusher_client.trigger(
                f'private-user-{other_user.id}',
                'new-message-notification',
                {
                    'conversation_id': conversation.id,
                    'sender_id': request.user.id,
                    'sender_username': request.user.username,
                    'sender_profile_picture': request.user.profile.profile_picture.url if request.user.profile.profile_picture else None,
                    'sender_status': request.user.profile.status,
                    'message_preview': message.content[:50] + ('...' if len(message.content) > 50 else ''),
                    'timestamp': message.created_at.strftime('%b %d, %Y, %I:%M %p')
                }
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender_id': message.sender.id,
                        'created_at': message.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    }
                })
            
            return redirect('TechRescueZoneApp:chat_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    messages_list = conversation.messages.all()
    
    # Get all conversations for the sidebar
    conversations = Conversation.objects.filter(participants=request.user)
    conversations = conversations.annotate(
        latest_message_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
        )
    ).order_by('-latest_message_time')
    
    conversation_data = []
    for conv in conversations:
        other_participant = conv.get_other_participant(request.user)
        latest_message = conv.messages.order_by('-created_at').first()
        
        conversation_data.append({
            'id': conv.id,
            'other_user': other_participant,
            'latest_message': latest_message,
            'unread_count': conv.unread_count,
        })
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages_list,  # Changed variable name to avoid conflict with messages framework
        'form': form,
        'conversations': conversation_data,
        'pusher_key': settings.PUSHER_KEY,
        'pusher_cluster': settings.PUSHER_CLUSTER,
    }
    return render(request, 'chat/chat_detail.html', context)

@login_required
def get_new_messages(request, conversation_id):
    # Get the conversation and check if the user is a participant
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    last_message_id = request.GET.get('last_message_id', 0)
    
    new_messages = conversation.messages.filter(id__gt=last_message_id)
    
    # Mark messages as read
    unread_messages = new_messages.filter(is_read=False).exclude(sender=request.user)
    if unread_messages.exists():
        unread_messages.update(is_read=True)
        
        # Notify the sender that their messages have been read
        for message in unread_messages:
            pusher_client.trigger(
                f'private-chat-{conversation.id}',
                'message-read',
                {
                    'message_id': message.id,
                    'reader_id': request.user.id
                }
            )
    
    message_data = []
    for message in new_messages:
        message_data.append({
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'created_at': message.created_at.strftime('%b %d, %Y, %I:%M %p'),
            'is_read': message.is_read
        })
    
    return JsonResponse({
        'messages': message_data,
    })

@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Don't allow starting a conversation with yourself
    if other_user.id == request.user.id:
        messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('TechRescueZoneApp:chat_list')

    # Check if a conversation already exists between these users
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    if existing_conversation:
        return redirect('TechRescueZoneApp:chat_detail', conversation_id=existing_conversation.id)

    # Create a new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, other_user)

    return redirect('TechRescueZoneApp:chat_detail', conversation_id=conversation.id)

@login_required
def pusher_auth(request):
    if request.method == 'POST':
        socket_id = request.POST.get('socket_id')
        channel_name = request.POST.get('channel_name')
        
        # Check if the user has access to this channel
        if channel_name.startswith('private-chat-'):
            conversation_id = channel_name.replace('private-chat-', '')
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                if conversation.participants.filter(id=request.user.id).exists():
                    auth = pusher_client.authenticate(
                        channel=channel_name,
                        socket_id=socket_id
                    )
                    return JsonResponse(auth)
            except Conversation.DoesNotExist:
                pass
            
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        elif channel_name.startswith('private-user-'):
            user_id = channel_name.replace('private-user-', '')
            if str(request.user.id) == user_id:
                auth = pusher_client.authenticate(
                    channel=channel_name,
                    socket_id=socket_id
                )
                return JsonResponse(auth)
        
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def search_users(request):
    query = request.GET.get('query', '')

    if len(query) < 2:
        return JsonResponse({'users': []})

    # Search for users by username, excluding the current user
    users = User.objects.filter(
        Q(username__icontains=query) | 
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]

    # Format the results
    user_data = []
    for user in users:
        profile_picture = user.profile.profile_picture.url if user.profile.profile_picture else None
        user_data.append({
            'id': user.id,
            'username': user.username,
            'profile_picture': profile_picture,
            'status': user.profile.status,
        })

    return JsonResponse({'users': user_data})

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()

    context = {
        'notifications': notifications,
    }
    return render(request, 'notification_list.html', context)

@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    if notification.link:
        return redirect(notification.link)
    return redirect('TechRescueZoneApp:notification_list')

@login_required
def mark_all_as_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('TechRescueZoneApp:notification_list')

def notification_count(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'notification_count': count}
    return {'notification_count': 0}

@login_required
def payment_process(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if Payment.objects.filter(order=order, status='completed').exists():
        messages.info(request, 'This order has already been paid for.')
        return redirect('TechRescueZoneApp:order_confirmation', order_id=order.id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            user=request.user,
            amount=order.total_price,
            payment_method=payment_method,
            status='pending',
        )
        
        if payment_method == 'khalti':
            # Process Khalti payment
            khalti_payload = request.POST.get('khalti_payload')
            if khalti_payload:
                # In a real application, you would verify the payment with Khalti API here
                # For sandbox/demo purposes, we'll just mark it as completed
                payment.status = 'completed'
                payment.transaction_id = f"KHALTI-{payment.id}"
                payment.save()
                
                order.status = 'processing'
                order.save()
                
                messages.success(request, 'Payment processed successfully via Khalti!')
            else:
                messages.error(request, 'Khalti payment failed. Please try again.')
                return redirect('TechRescueZoneApp:payment_process', order_id=order.id)
        else:
            # Cash on Delivery
            payment.status = 'pending'  # COD payments remain pending until delivery
            payment.transaction_id = f"COD-{payment.id}"
            payment.save()
            
            order.status = 'processing'
            order.save()
            
            messages.success(request, 'Your order has been placed successfully! You will pay on delivery.')
        
        # Create notification
        Notification.objects.create(
            recipient=request.user,
            notification_type='order_status',
            content=f'Your order #{order.id} has been confirmed and is being processed.',
            link=f'/order-confirmation/{order.id}/',
        )
        
        return redirect('TechRescueZoneApp:order_confirmation', order_id=order.id)

    # For GET request, show payment options
    context = {
        'order': order,
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY if hasattr(settings, 'KHALTI_PUBLIC_KEY') else 'test_public_key_12345abcde',
    }
    return render(request, 'hardware/payment_process.html', context)

@login_required
def payment_methods(request):
    # Since we're only using COD and Khalti, we don't need saved payment methods
    # Redirect to home or another appropriate page
    messages.info(request, 'Payment methods are selected during checkout.')
    return redirect('TechRescueZoneApp:home')

@login_required
def add_payment_method(request):
    # Since we're only using COD and Khalti, we don't need to add payment methods
    messages.info(request, 'Payment methods are selected during checkout.')
    return redirect('TechRescueZoneApp:home')

@login_required
def delete_payment_method(request, method_id):
    # Since we're only using COD and Khalti, we don't need to delete payment methods
    messages.info(request, 'Payment methods are selected during checkout.')
    return redirect('TechRescueZoneApp:home')

@login_required
def set_default_payment_method(request, method_id):
    # Since we're only using COD and Khalti, we don't need to set default payment methods
    messages.info(request, 'Payment methods are selected during checkout.')
    return redirect('TechRescueZoneApp:home')

@login_required
def direct_payment(request, hardware_id):
    if request.method == 'POST':
        hardware = get_object_or_404(Hardware, id=hardware_id)
        quantity = int(request.POST.get('quantity', 1))
        payment_method = request.POST.get('payment_method')
        
        if hardware.stock < quantity:
            messages.error(request, f'Sorry, only {hardware.stock} units available.')
            return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            shipping_address=request.user.profile.user.email,  # Temporary, will be updated in checkout
            total_price=hardware.get_final_price() * quantity,
            status='pending'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            hardware=hardware,
            quantity=quantity,
            price=hardware.get_final_price()
        )
        
        # Update stock
        hardware.stock -= quantity
        hardware.save()
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            user=request.user,
            amount=order.total_price,
            payment_method=payment_method,
            status='pending',
        )
        
        if payment_method == 'khalti':
            # Process Khalti payment
            khalti_payload = request.POST.get('khalti_payload')
            if khalti_payload:
                # In a real application, you would verify the payment with Khalti API here
                # For sandbox/demo purposes, we'll just mark it as completed
                payment.status = 'completed'
                payment.transaction_id = f"KHALTI-{payment.id}"
                payment.save()
                
                order.status = 'processing'
                order.save()
                
                messages.success(request, 'Payment processed successfully via Khalti!')
            else:
                messages.error(request, 'Khalti payment failed. Please try again.')
                return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware.id)
        else:
            # Cash on Delivery
            payment.status = 'pending'  # COD payments remain pending until delivery
            payment.transaction_id = f"COD-{payment.id}"
            payment.save()
            
            order.status = 'processing'
            order.save()
            
            messages.success(request, 'Your order has been placed successfully! You will pay on delivery.')
        
        # Create notification
        Notification.objects.create(
            recipient=request.user,
            notification_type='order_status',
            content=f'Your order #{order.id} has been confirmed and is being processed.',
            link=f'/order-confirmation/{order.id}/',
        )
        
        return redirect('TechRescueZoneApp:order_confirmation', order_id=order.id)
    
    return redirect('TechRescueZoneApp:hardware_detail', hardware_id=hardware_id)


@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Generate a unique purchase order ID
    purchase_order_id = f"ORDER-{order.id}-{uuid.uuid4().hex[:8]}"
    
    # Prepare the payload for Khalti
    payload = {
        "return_url": request.build_absolute_uri(reverse('TechRescueZoneApp:payment_verify')),
        "website_url": request.build_absolute_uri('/'),
        "amount": int(order.total_price * 100),  # Convert to paisa
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": f"Order #{order.id}",
        "customer_info": {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "phone": request.user.profile.phone if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone') else ""
        }
    }
    
    # Make request to Khalti
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            settings.KHALTI_INITIATE_URL,
            json=payload,
            headers=headers
        )
        
        response_data = response.json()
        
        if response.status_code == 200:
            # Update order with pidx
            order.pidx = response_data.get('pidx')
            order.save()
            
            # Redirect to Khalti payment page
            return redirect(response_data.get('payment_url'))
        else:
            # Handle error
            return render(request, 'hardware/payment_error.html', {
                'error': response_data.get('detail', 'Payment initiation failed'),
                'order': order
            })
            
    except Exception as e:
        return render(request, 'hardware/payment_error.html', {
            'error': str(e),
            'order': order
        })

@csrf_exempt
def payment_verify(request):
    # Get parameters from the callback
    pidx = request.GET.get('pidx')
    status = request.GET.get('status')
    transaction_id = request.GET.get('transaction_id')
    
    if not pidx:
        return render(request, 'hardware/payment_error.html', {
            'error': 'Invalid payment information'
        })
    
    # Find the order
    try:
        order = Order.objects.get(pidx=pidx)
    except Order.DoesNotExist:
        return render(request, 'hardware/payment_error.html', {
            'error': 'Order not found'
        })
    
    # Update order status based on callback
    if status == 'Completed':
        order.status = 'processing'  # or 'completed' based on your workflow
        order.transaction_id = transaction_id
        order.save()
        
        # Create or update payment record
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'user': order.user,
                'amount': order.total_price,
                'payment_method': 'khalti',
                'status': 'completed',
                'transaction_id': transaction_id
            }
        )
        
        if not created:
            payment.status = 'completed'
            payment.transaction_id = transaction_id
            payment.save()
        
        # Verify with lookup API
        return verify_payment(request, order)
    elif status == 'Pending':
        order.status = 'pending'
        order.save()
        return render(request, 'hardware/payment_pending.html', {'order': order})
    else:
        order.status = 'failed' if status == 'Failed' else 'canceled'
        order.save()
        return render(request, 'hardware/payment_failed.html', {'order': order, 'status': status})

def verify_payment(request, order):
    # Prepare lookup request
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "pidx": order.pidx
    }
    
    try:
        response = requests.post(
            settings.KHALTI_LOOKUP_URL,
            json=payload,
            headers=headers
        )
        
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status') == 'Completed':
            # Payment is verified
            order.status = 'processing'  # or 'completed' based on your workflow
            order.transaction_id = response_data.get('transaction_id')
            order.save()
            
            # Create notification
            Notification.objects.create(
                recipient=order.user,
                notification_type='order_status',
                content=f'Your payment for order #{order.id} has been confirmed.',
                link=f'/order-confirmation/{order.id}/',
            )
            
            return render(request, 'hardware/payment_success.html', {'order': order})
        else:
            # Payment verification failed
            order.status = 'failed'
            order.save()
            
            return render(request, 'hardware/payment_failed.html', {
                'order': order,
                'status': response_data.get('status', 'Failed')
            })
            
    except Exception as e:
        order.status = 'failed'
        order.save()
        
        return render(request, 'hardware/payment_error.html', {
            'error': str(e),
            'order': order
        })
