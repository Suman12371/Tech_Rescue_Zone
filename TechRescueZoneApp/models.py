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

