# store/models.py
from django.db import models
from django.utils import timezone
import uuid
from cloudinary.models import CloudinaryField

def generate_order_reference():
    return f"BOOK-{uuid.uuid4().hex[:12].upper()}"

class Book(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    price_kobo = models.PositiveIntegerField(help_text="Price in kobo (NGN * 100)")
    cover = CloudinaryField("image", blank=True, null=True)
    link_url = models.URLField(max_length=1000, help_text="External URL to the book", blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def price_display(self):
        return self.price_kobo / 100


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    reference = models.CharField(max_length=64, unique=True, default=generate_order_reference)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount_kobo = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=10, default="NGN")
    paystack_ref = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.reference} — {self.email}"

    def total_amount_display(self):
        return self.total_amount_kobo / 100


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)
    unit_price_kobo = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Order item"
        verbose_name_plural = "Order items"

    def __str__(self):
        return f"{self.qty} x {self.book.title}"

    def line_total_kobo(self):
        return self.qty * self.unit_price_kobo

    def line_total_display(self):
        return self.line_total_kobo() / 100
