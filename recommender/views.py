from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import *
from .ml.loader import load_bundle, predict_one
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import timedelta
import json

def home(request):
    total_users = User.objects.filter(is_staff=False).count()
    total_predictions = Prediction.objects.count()
    return render(request,"home.html",locals())

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not name or not email or not phone or not password:
            messages.error(request, "Please fill all required fields.")
            return redirect("signup")

        if len(password) < 6:
            messages.error(request, "Password should be at least 6 characters.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        user.first_name = name
        user.save()

        UserProfile.objects.create(user=user, phone=phone)
        login(request, user)
        return redirect("predict")

    return render(request, "signup.html")


@login_required
def predict_view(request):
    bundle = load_bundle()
    feature_order = bundle["feature_cols"]
    result = None
    last_data = None

    if request.method == "POST":
        data = {c: float(request.POST.get(c)) for c in feature_order}
        label = predict_one(data)

        Prediction.objects.create(
            user=request.user,
            **data,
            Predicted_label=label
        )

        result = label
        last_data = data
        messages.success(request,f"Recommended Crop: {label}")

    return render(request,"predict.html", locals())


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid login credentials.")
            return redirect("login")

        login(request, user)
        messages.success(request, "Logged in successfully")
        return redirect("predict")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.success(request,"Logout successfully")
    return redirect("login")


@login_required
def user_history_view(request):
    predictions = Prediction.objects.filter(user=request.user)
    return render(request, "history.html", {"predictions": predictions})


@login_required
def profile_view(request):
    profile = UserProfile.objects.get(user=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")

        if name:
            parts = name.split(" ", 1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts) > 1 else ""

        profile.phone = phone
        request.user.save()
        profile.save()

        messages.success(request, "Profile updated.")

    full_name = request.user.get_full_name()
    return render(request, "profile.html", locals())


@login_required
def change_password_view(request):
    if request.method == "POST":
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")

        if not request.user.check_password(current):
            messages.error(request, "Current password is incorrect.")
            return redirect("change_password")

        if len(new) < 6:
            messages.error(request, "New password must be at least 6 characters.")
            return redirect("change_password")

        if new != confirm:
            messages.error(request, "New passwords do not match.")
            return redirect("change_password")

        request.user.set_password(new)
        request.user.save()
        messages.success(request, "Password changed successfully")
        return redirect("change_password")

    return render(request, "change_password.html")


def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid login credentials.")
            return redirect("admin_login")

        if not user.is_staff:
            messages.error(request, "You are not authorized for admin panel.")
            return redirect("admin_login")

        login(request, user)
        messages.success(request, "Logged in successfully")
        return redirect("admin_dashboard")

    return render(request, "admin_login.html")


def is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff, login_url='admin_login')
def admin_dashboard_view(request):
    total_users = User.objects.filter(is_staff=False).count()
    total_predictions = Prediction.objects.count()

    crop_qs = (
        Prediction.objects.values('Predicted_label')
        .annotate(c=Count('id'))
        .order_by('-c')[:10]
    )

    crop_labels = [i['Predicted_label'].title() for i in crop_qs]
    crop_counts = [i['c'] for i in crop_qs]

    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    day_labels = [d.strftime("%d %b") for d in days]
    day_counts = [Prediction.objects.filter(created_at__date=d).count() for d in days]

    context = {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "crop_labels_json": json.dumps(crop_labels),
        "crop_counts_json": json.dumps(crop_counts),
        "day_labels_json": json.dumps(day_labels),
        "day_counts_json": json.dumps(day_counts),
    }

    return render(request, "admin_dashboard.html", context)


@user_passes_test(is_staff, login_url='admin_login')
def admin_users_view(request):
    users = User.objects.filter(is_staff=False)
    return render(request, "admin_view_users.html", {"users": users})


@user_passes_test(is_staff, login_url='admin_login')
def admin_user_delete(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    messages.success(request, "User deleted")
    return redirect("admin_users_view")

@login_required
def user_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id, user=request.user)
    prediction.delete()
    messages.success(request, "Entry Removed from history.")
    return redirect("user_history")

@user_passes_test(is_staff, login_url='admin_login')
def admin_view_predictions(request):

    qs = Prediction.objects.select_related('user')

    crop = request.GET.get('crop')
    start = request.GET.get('start')
    end = request.GET.get('end')

    if crop:
        qs = qs.filter(Predicted_label__iexact=crop)

    d_start = parse_date(start) if start else None
    d_end = parse_date(end) if end else None

    if d_start:
        qs = qs.filter(created_at__date__gte=d_start)

    if d_end:
        qs = qs.filter(created_at__date__lte=d_end)

    crops = (
        Prediction.objects
        .order_by('Predicted_label')
        .values_list('Predicted_label', flat=True)
        .distinct()
    )

    context = {
        "qs": qs,
        "crops": crops,
        "current_crop": crop,
        "start": start,
        "end": end,
    }

    return render(request, "admin_view_predictions.html", context)


@user_passes_test(is_staff, login_url='admin_login')
def admin_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction,id=id)
    prediction.delete()
    messages.success(request, "Prediction deleted")
    return redirect("admin_view_predictions")

def admin_logout(request):
    logout(request)
    messages.success(request,"Logout successfully")
    return redirect("admin_login")