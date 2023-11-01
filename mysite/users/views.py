from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import authenticate, login
from.forms import LoginForm, RegisterForm, ForgetPwdForm, ModifyPwdForm, UserForm, UserProfileForm
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.contrib.auth.models import User
from .models import EmailVerifyRecord, UserProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
from utils.email_send import send_register_email


class MyBackend(ModelBackend):
    '''邮箱登录注册'''
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):  # 加密明文密码
                return user
        except Exception as e:
            return None


def active_user(request, active_code):
    '''修改用户状态比对链接验证码'''
    all_records = EmailVerifyRecord.objects.filter(code=active_code)
    if all_records:
        for record in all_records:
            email = record.email
            user = User.objects.get(email=email)
            user.is_staff = True
            user.save()
    else:
        return HttpResponse('连接有误')
    return redirect('users:login')

def login_view(request):
    '''登录功能'''
    if request.method != 'POST':
        form = LoginForm()
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # 登陆成功后跳转到个人中心
                return redirect('users:user_profile')
            else:
                return HttpResponse('登陆失败')
    context = {'form': form}
    return render(request, 'users/login.html', context)


def register(request):
    '''注册视图'''
    if request.method != 'POST':
        form = RegisterForm()
    else:
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data.get('password'))
            new_user.username = form.cleaned_data.get('email')
            new_user.save()

            #发送邮件
            send_register_email(form.cleaned_data.get('email'), 'register')
            return HttpResponse('注册成功')
    context = {'form': form}
    return render(request, 'users/register.html', context)


def forget_pwd(request):
    '''找回密码'''
    if request.method == 'GET':
        form = ForgetPwdForm()
    elif request.method == 'POST':
        form = ForgetPwdForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            exists = User.objects.filter(email=email).exists()
            if exists:
                # 发送邮件
                send_register_email(email, 'forget')
                return HttpResponse('邮件已经发送请查收！')
            else:
                return HttpResponse('邮箱还未注册，请前往注册！')

    return render(request, 'users/forget_pwd.html', {'form': form})


def forget_pwd_url(request, active_code):
    if request.method != 'POST':
        form = ModifyPwdForm()
    else:
        form = ModifyPwdForm(request.POST)
        if form.is_valid():
            record = EmailVerifyRecord.objects.get(code=active_code)
            email = record.email
            user = User.objects.get(email = email)
            user.username = email
            user.password = make_password(form.cleaned_data.get('password'))
            user.save()
            return HttpResponse('修改成功')
        else:
            return HttpResponse('修改失败')

    return render(request, 'users/reset_pwd.html', {'form': form})


@login_required(login_url='users:login')   # 设置登录后才能访问，如果没有登陆，就跳转到登录界面
def user_profile(request):
    user = User.objects.get(username=request.user)
    return render(request, 'users/user_profile.html', {'user': user})


def logout_view(request):
	logout(request)
	return redirect('users:login')


@login_required(login_url='users:login')   # 登录之后允许访问
def editor_users(request):
    """ 编辑用户信息 """
    user = User.objects.get(id=request.user.id)
    if request.method == "POST":
        try:
            userprofile = user.userprofile
            form = UserForm(request.POST, instance=user)
            user_profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)  # 向表单填充默认数据
            if form.is_valid() and user_profile_form.is_valid():
                form.save()
                user_profile_form.save()
                return redirect('users:user_profile')
        except UserProfile.DoesNotExist:   # 这里发生错误说明userprofile无数据
            form = UserForm(request.POST, instance=user)       # 填充默认数据 当前用户
            user_profile_form = UserProfileForm(request.POST, request.FILES)  # 空表单，直接获取空表单的数据保存
            if form.is_valid() and user_profile_form.is_valid():
                form.save()
                # commit=False 先不保存，先把数据放在内存中，然后再重新给指定的字段赋值天剑进去，提交保存新的数据
                new_user_profile = user_profile_form.save(commit=False)
                new_user_profile.owner = request.user
                new_user_profile.save()

                return redirect('users:user_profile')
    else:
        try:
            userprofile = user.userprofile
            form = UserForm(instance=user)
            user_profile_form = UserProfileForm(instance=userprofile)
        except UserProfile.DoesNotExist:
            form = UserForm(instance=user)
            user_profile_form = UserProfileForm()  # 显示空表单
    return render(request, 'users/editor_users.html', locals())

