# store/views.py
import json
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from .models import Book, Order, OrderItem

# existing views (catalog, cart_page, checkout_page, create_order) remain unchanged...
def catalog(request):
    books = Book.objects.all()
    return render(request, 'store/catalog.html', {'books': books})

def cart_page(request):
    return render(request, 'store/cart.html')

def checkout_page(request):
    public_key = getattr(settings, "PAYSTACK_PUBLIC_KEY", "")
    return render(request, 'store/checkout.html', {'PAYSTACK_PUBLIC_KEY': public_key})

@require_POST
def create_order(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    items = data.get("items", [])

    if not name or not email:
        return JsonResponse({"error": "name and email are required"}, status=400)
    if not items or not isinstance(items, list):
        return JsonResponse({"error": "cart items required"}, status=400)

    total = 0
    validated_items = []
    for it in items:
        try:
            book_id = int(it.get("book_id"))
            qty = max(1, int(it.get("qty", 1)))
        except Exception:
            return JsonResponse({"error": "invalid item format"}, status=400)

        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return JsonResponse({"error": f"book id {book_id} not found"}, status=400)

        line_total = book.price_kobo * qty
        total += line_total
        validated_items.append((book, qty, book.price_kobo))

    order = Order.objects.create(
        name=name,
        email=email,
        phone=phone,
        total_amount_kobo=total,
    )

    for book, qty, unit_price in validated_items:
        OrderItem.objects.create(
            order=order,
            book=book,
            qty=qty,
            unit_price_kobo=unit_price
        )

    response = {
        "reference": order.reference,
        "email": order.email,
        "amount_kobo": order.total_amount_kobo,
        "paystack_public_key": getattr(settings, "PAYSTACK_PUBLIC_KEY", "")
    }
    return JsonResponse(response)

from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import requests

from .models import Order
# from .utils import send_order_links_email  # wherever you defined it


def verify_payment(request):
    """
    GET /api/payments/verify/?ref=<reference>
    Verifies Paystack transaction and fulfills order.
    Redirects to catalog with error messages if anything fails.
    """
    ref = request.GET.get("ref")
    if not ref:
        messages.error(request, "Payment reference is missing.")
        return redirect("catalog")

    secret = getattr(settings, "PAYSTACK_SECRET_KEY", "")
    if not secret:
        messages.error(request, "Payment gateway not configured. Contact support.")
        return redirect("catalog")

    # Call Paystack verify
    headers = {"Authorization": f"Bearer {secret}"}
    verify_url = f"https://api.paystack.co/transaction/verify/{ref}"
    try:
        r = requests.get(verify_url, headers=headers, timeout=15)
        resp = r.json()
    except Exception as e:
        messages.error(request, "Error contacting payment gateway. Please try again.")
        return redirect("catalog")

    # Paystack returns status:false for failures
    if not resp.get("status"):
        messages.error(request, "Payment verification failed. Please try again.")
        return redirect("catalog")

    data = resp.get("data", {})
    status = data.get("status")  # expected "success"
    gateway_ref = data.get("reference")

    # Find order by reference
    try:
        order = Order.objects.get(reference=gateway_ref)
    except Order.DoesNotExist:
        try:
            order = Order.objects.get(reference=ref)
        except Order.DoesNotExist:
            messages.error(request, "No matching order found. Please contact support.")
            return redirect("catalog")

    if status == "success":
        # Mark paid
        order.status = Order.STATUS_PAID
        order.paid_at = timezone.now()
        order.paystack_ref = gateway_ref
        order.save()

        # Send email with book links
        try:
            send_order_links_email(order)
        except Exception as e:
            # Don’t fail payment, just warn in logs
            print(f"⚠️ Email sending failed: {e}")

        # Return JSON for frontend (keeps your working success flow)
        return JsonResponse({"status": "success"})
    else:
        order.status = Order.STATUS_FAILED
        order.save()
        messages.error(request, "Payment was not successful. Please try again.")
        return redirect("catalog")


# helper to send email with book links
from django.core.mail import send_mail
from django.conf import settings

def send_order_links_email(order):
    """
    Compose and send an email to the buyer with the book link(s).
    """
    subject = f"Your purchase — Order {order.reference}"
    lines = [
        f"Hi {order.name},",
        "",
        "Thanks for your purchase. Below are the link(s) to the book(s) you bought:",
        ""
    ]
    for item in order.items.all():
        lines.append(f"- {item.book.title} : {item.book.link_url}")

    lines.append("")
    lines.append("If a link doesn't work, reply to this email and we'll assist.")
    body = "\n".join(lines)

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    send_mail(
        subject=subject,
        message=body,
        from_email=from_email,
        recipient_list=[order.email],
        fail_silently=False,
    )


# thank you page
def thank_you(request, reference):
    order = get_object_or_404(Order, reference=reference)
    return render(request, 'store/thank_you.html', {'order': order})
