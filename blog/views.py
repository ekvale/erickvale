from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Post, Category, Tag


def post_list(request):
    """Display list of published blog posts."""
    posts = Post.objects.filter(status='published')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    # Category filter
    category_slug = request.GET.get('category', '')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    # Tag filter
    tag_slug = request.GET.get('tag', '')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)
    
    # Pagination
    paginator = Paginator(posts, 6)  # 6 posts per page
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    categories = Category.objects.all()
    tags = Tag.objects.all()
    featured_posts = Post.objects.filter(status='published', featured=True)[:3]
    
    context = {
        'posts': posts,
        'categories': categories,
        'tags': tags,
        'featured_posts': featured_posts,
        'search_query': search_query,
        'category_slug': category_slug,
        'tag_slug': tag_slug,
    }
    
    return render(request, 'blog/post_list.html', context)


def post_detail(request, year, month, day, slug):
    """Display a single blog post."""
    post = get_object_or_404(
        Post,
        slug=slug,
        publish_date__year=year,
        publish_date__month=month,
        publish_date__day=day,
        status='published'
    )
    
    # Increment view count
    post.increment_views()
    
    # Get approved comments
    comments = post.comments.filter(approved=True)
    
    # Get related posts (same category)
    related_posts = Post.objects.filter(
        category=post.category,
        status='published'
    ).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'comments': comments,
        'related_posts': related_posts,
    }
    
    return render(request, 'blog/post_detail.html', context)


def category_list(request, slug):
    """Display posts by category."""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, status='published')
    
    paginator = Paginator(posts, 6)
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'category': category,
        'posts': posts,
        'categories': categories,
        'tags': tags,
    }
    
    return render(request, 'blog/category.html', context)


def tag_list(request, slug):
    """Display posts by tag."""
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(tags=tag, status='published')
    
    paginator = Paginator(posts, 6)
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    context = {
        'tag': tag,
        'posts': posts,
        'categories': categories,
        'tags': tags,
    }
    
    return render(request, 'blog/tag.html', context)
