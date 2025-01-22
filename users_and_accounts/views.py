from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .forms import NewUserForm, UserEditForm, ProfileEditForm, ContactForm
from .models import Profile
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView



# class SignUpView(CreateView):
#     template_name = 'registration/register.html'
#     form_class = UserCreationForm
#     success_url = reverse_lazy('catalog_main_page')

#     def form_valid(self, form):
#         valid = super().form_valid(form)
#         login(self.request, self.object)
#         return valid

def validate_username(request):
    """Проверка доступности логина"""
    username = request.GET.get('username', None)
    response = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(response)

def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = Profile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Registration successful." )
            return redirect(reverse_lazy('catalog_main_page'))
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(request=request, template_name="registration/register.html", context={"register_form":form})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect(reverse_lazy('catalog_main_page'))
        else:
            return render(request,
                         'profile/profile_edit.html',
                         {'user_form': user_form,
                          'profile_form': profile_form})

    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        return render(request,
                        'profile/profile_edit.html',
                        {'user_form': user_form,
                        'profile_form': profile_form})

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def contact_form(request):
    form = ContactForm()
    if request.method == "POST" and is_ajax(request):
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            form.save()
            return JsonResponse({"name": name}, status=200)
        else:
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)

    return render(request, "contact.html", {"form": form})