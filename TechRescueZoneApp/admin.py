from django.contrib import admin
from .models import *

admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Hardware)
admin.site.register(HardwareImage)
admin.site.register(HardwareReview)
admin.site.register(SolutionCategory)
admin.site.register(Solution)
admin.site.register(SolutionStep)
admin.site.register(SolutionImage)

