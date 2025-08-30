# store/admin.py
from django.contrib import admin
from .models import Book, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("book", "qty", "unit_price_display", "line_total_display")
    fields = ("book", "qty", "unit_price_display", "line_total_display")

    def unit_price_display(self, obj):
        return f"₦{obj.unit_price_kobo / 100:,.2f}"
    unit_price_display.short_description = "Unit Price"

    def line_total_display(self, obj):
        return f"₦{obj.line_total_kobo() / 100:,.2f}"
    line_total_display.short_description = "Line Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "email", "name", "status", "total_amount_display", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "email", "name", "paystack_ref")
    readonly_fields = ("reference", "created_at", "paid_at", "total_amount_display")
    inlines = [OrderItemInline]

    def total_amount_display(self, obj):
        return f"₦{obj.total_amount_kobo / 100:,.2f}"
    total_amount_display.short_description = "Total Paid"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "price_display", "link_url", "created_at")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}

    def price_display(self, obj):
        return f"₦{obj.price_kobo / 100:,.2f}"
    price_display.short_description = "Price"
