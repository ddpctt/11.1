from django.shortcuts import render, get_object_or_404
from .models import Category, Post
from django.db.models import Q, F
from django.core.paginator import Paginator


def index(request):
    # 首页
    post_list = Post.objects.all()   # 查询到所有的文章
    # 分页方法
    paginator = Paginator(post_list, 2)  # 第二个参数2代表每页显示几个
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'post_list': post_list, 'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def category_list(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # 获取当前分类下的所有文章
    posts = category.post_set.all()
    paginator = Paginator(posts, 2)  # 第二个参数2代表每页显示几个
    page_number = request.GET.get('page')   # http://assas.co/?page=1 (页码)
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj }
    return render(request, 'blog/list.html', context)


def post_detail(request, post_id):
    # 文章详情页
    post = get_object_or_404(Post, id=post_id)

    # 用文章ID实现的上下篇
    prev_post = Post.objects.filter(id__lt=post_id).last()  # 上一篇
    next_post = Post.objects.filter(id__gt=post_id).first()  # 下一篇

    context = {'post': post, 'prev_post': prev_post, 'next_post': next_post}

    return render(request, 'blog/detail.html', context)


def search(request):
    """ 搜索视图 """
    keyword = request.GET.get('keyword')
    # 没有搜索默认显示所有文章
    if not keyword:
        post_list = Post.objects.all()
    else:
        # 包含查询的方法，用Q对象来组合复杂查询，title__icontains 他两个之间用的是双下划线（__）链接
        post_list = Post.objects.filter(Q(title__icontains=keyword) | Q(desc__icontains=keyword) | 		Q(content__icontains=keyword))
    paginator = Paginator(post_list, 2)  # 第二个参数2代表每页显示几个
    page_number = request.GET.get('page')   # http://assas.co/?page=1 (页码)
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'blog/index.html', context )


def archives(request, year, month):
    # 文章归档列表页
    post_list = Post.objects.filter(add_date__year=year, add_date__month=month)
    context = {'post_list': post_list, 'year': year, 'month': month}
    return render(request, 'blog/archives_list.html', context)

