
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, CartItem, WishlistItem, Order, OrderItem

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom', {'fields': ('name','role','isBlocked')}),
    )
    list_display = ('id','username','email','name','role','isBlocked','is_staff')
    search_fields = ('email','username','name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name','brand','price','category','active')

@admin.register(CartItem)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id','user','product','quantity')

@admin.register(WishlistItem)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id','user','product')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user','total','status','date')
    inlines = [OrderItemInline]
