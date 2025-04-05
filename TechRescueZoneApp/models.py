from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
    
class Profile(models.Model):
    STATUS_CHOICES = (
        ('export', 'Export'),
        ('user', 'User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    auth_token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='user')
    
    def __str__(self):
        return self.user.username
    
    def is_exporter(self):
        return hasattr(self, 'exporter_profile') and self.exporter_profile is not None
    
    
class Category(models.Model):
    """Hardware categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'


class Hardware(models.Model):
    """Hardware items that can be sold"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='hardware')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hardware_listings')
    stock = models.PositiveIntegerField(default=1)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('hardware_detail', args=[str(self.id)])
    
    def get_discount_percentage(self):
        if self.discount_price and self.price > 0:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    def get_final_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price
    
    class Meta:
        verbose_name_plural = 'Hardware'


class HardwareImage(models.Model):
    """Images for hardware items"""
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hardware_images/')
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.hardware.name}"
    class Meta:
        verbose_name_plural = "Hardware Images"


class HardwareReview(models.Model):
    """Reviews for hardware items"""
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.hardware.name}"
    
    class Meta:
        unique_together = ('hardware', 'user')


class Order(models.Model):
    """Orders for hardware items"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    
    def __str__(self):
        return f"{self.quantity} x {self.hardware.name} in Order {self.order.id}"
    
    def get_total_price(self):
        return self.price * self.quantity
    
    
class SolutionCategory(models.Model):
    """Categories for solutions"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Solution Categories'


class Solution(models.Model):
    """Tech solutions posted by users"""
    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solutions')
    category = models.ForeignKey(SolutionCategory, on_delete=models.CASCADE, related_name='solutions')
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(User, related_name='liked_solutions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('solution_detail', args=[str(self.id)])
    
    def get_like_count(self):
        return self.likes.count()
    
    def get_comment_count(self):
        return self.comments.count()
    
    def get_average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():  # Using exists() for efficiency
            return sum(rating.rating for rating in ratings) / ratings.count()
        return 0



class SolutionStep(models.Model):
    """Steps for a solution"""
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.solution.title} - Step {self.order}: {self.title}"
    
    class Meta:
        ordering = ['order']
        unique_together = ('solution', 'order')


class SolutionImage(models.Model):
    """Images for solution steps"""
    step = models.ForeignKey(SolutionStep, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='solution_images/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"Image for {self.step.solution.title} - Step {self.step.order}"


class SolutionComment(models.Model):
    """Comments on solutions"""
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.solution.title}"


class SolutionRating(models.Model):
    """Ratings for solutions"""
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rating by {self.user.username} for {self.solution.title}"
    
    class Meta:
        unique_together = ('solution', 'user')
        

class Conversation(models.Model):
    """Conversation between users"""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Conversation {self.id}"
    
    def get_other_participant(self, user):
        """Get the other participant in a two-person conversation"""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Message in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message from {self.sender.username} in Conversation {self.conversation.id}"
    
    class Meta:
        ordering = ['created_at']
        

class Notification(models.Model):
    """Notification model for user notifications"""
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('solution_comment', 'Solution Comment'),
        ('solution_like', 'Solution Like'),
        ('solution_rating', 'Solution Rating'),
        ('order_status', 'Order Status Update'),
        ('system', 'System Notification'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    content = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.get_notification_type_display()}"
    
    class Meta:
        ordering = ['-created_at']
        
        
class Payment(models.Model):
    """Payment model for tracking payments"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"


class PaymentMethod(models.Model):
    """Saved payment methods for users"""
    CARD_TYPE_CHOICES = (
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES)
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, blank=True, null=True)
    last_four = models.CharField(max_length=4, blank=True, null=True)  
    expiry_date = models.CharField(max_length=7, blank=True, null=True) 
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.method_type == 'credit_card':
            return f"{self.get_card_type_display()} ending in {self.last_four}"
        return self.get_method_type_display()
    
    
