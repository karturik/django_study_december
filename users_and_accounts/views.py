from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .forms import NewUserForm, UserEditForm, ProfileEditForm
from .models import Profile
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages


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