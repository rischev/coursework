from django.shortcuts import render
from django.http import HttpResponse

posts = [
    {
        'author': 'CoreyMS',
        'title': 'Blog post 1',
        'content': 'Sirst post content',
        'date_posted': 'August 27, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog post 2',
        'content': 'Second post content',
        'date_posted': 'August 28, 2018'
    }
]

def home(request) -> HttpResponse:
    context = {
        'posts': posts
    }
    return render(request, 'blog/home.html', context)

def about(request) -> HttpResponse:
    return render(request, 'blog/about.html', {'title': 'About'})
