from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post
import requests
import re
from bs4 import BeautifulSoup

def home(request) -> HttpResponse:
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'blog/home.html', context)

def about(request) -> HttpResponse:
    return render(request, 'blog/about.html', {'title': 'About'})

class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5

class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')

class PostDetailView(DetailView):
    model = Post

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False
        # dobavit v otchet

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False
        # dobavit v otchet

@login_required
def parsemm(request):
    if request.user == User.objects.filter(username='roman').first():
        mmhaskell()
    else:
        messages.warning(request, "You do not have enough permission")
    return redirect('blog-home')

@login_required
def parsefpcomplete(request, pages):
    if request.user == User.objects.filter(username='roman').first():
        fpcomplete(pages)
    else:
        messages.warning(request, "You do not have enough permission")
    return redirect('blog-home')


def mmhaskell(request) -> [Post]:
    def find_title(string) -> str:
        titleSoup = BeautifulSoup(string, 'html.parser')
        links = titleSoup.find_all('a')
        titleLink = links[2]
        title = re.findall(re.compile(">(.*?)</a>"), str(titleLink))
        return title[0]

    def find_text_content(string, is_p) -> str:
        if is_p:
            return re.findall(re.compile('<p>(.*?)</p>'), string)[0]
        else:
            contentSoup = BeautifulSoup(string, 'html.parser')
            return str(contentSoup.find_all("div", class_="sqs-block-content")[1])

    def find_youtube_embed(string) -> str:
        video = re.findall(re.compile("youtube.com/(.*?)\\&"), string)
        if len(video) > 0:
            return ("www.youtube.com/" + re.findall(re.compile("youtube.com/(.*?)[?]"), string)[0])
        return None

    html = requests.get('https://mmhaskell.com/blog').text
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('article')
    posts = []
    mmhaskellAuthor = User.objects.filter(username='mmhaskell').first()
    for i in articles:
        article_video = find_youtube_embed(str(i))
        if article_video:
            article_content = find_text_content(str(i), True)
            post = Post(title=find_title(str(i)), content=article_content,
                        video=article_video, author=mmhaskellAuthor)
        else:
            article_content = find_text_content(str(i), False)
            post = Post(title=find_title(str(i)), content=article_content,
                        author=mmhaskellAuthor)
        try:
            post.save()
        except IntegrityError:
            pass
        posts.append(post)
    return posts

def fpcomplete(request, pages) -> [Post]:
    def parse_page(url) -> [str]:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        re_link = lambda x: re.findall(re.compile('href="(.*?)"'), str(x))[0]
        article_hrefs = soup.find_all('a', class_='text-decoration-none')
        article_urls_dup = list(map(re_link, article_hrefs))
        article_urls = []
        for i in enumerate(article_urls_dup):
            if i[0] % 2 == 0: article_urls.append(i[1])

        return article_urls

    def parse_article(author, url) -> Post:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        title = str(soup.find('h1', class_='text-uppercase').contents[0])
        content = str(soup.find('div', class_='container my-5 blog-body'))
        return Post(title=title, content=content, author=author)

    posts = []
    base = 'https://www.fpcomplete.com/blog/'
    fpCompAuthor = User.objects.filter(username='fpcomplete').first()
    for i in range(1, pages + 1):
        page_urls = parse_page(f'{base}/page/{i}')
        for x in page_urls:
            try:
                post = parse_article(fpCompAuthor, x)
                posts.append(post)
                post.save()
            except IntegrityError:
                pass

    return posts
